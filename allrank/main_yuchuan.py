from urllib.parse import urlparse

import allrank.models.losses as losses
import numpy as np
import os
import torch
from allrank.config import Config
from allrank.data.dataset_loading import load_libsvm_dataset, create_data_loaders, load_libsvm_dataset_role
from allrank.models.model import make_model
from allrank.models.model_utils import get_torch_device, CustomDataParallel
from allrank.training.train_utils import fit
from allrank.utils.command_executor import execute_command
from allrank.utils.experiments import dump_experiment_result, assert_expected_metrics
from allrank.utils.file_utils import create_output_dirs, PathsContainer, copy_local_to_gs
from allrank.utils.ltr_logging import init_logger
from allrank.utils.python_utils import dummy_context_mgr
from argparse import ArgumentParser, Namespace
from attr import asdict
from functools import partial
from pprint import pformat
from torch import optim

from torch.utils.data import DataLoader
from allrank.training.train_utils import compute_metrics


def parse_args() -> Namespace:
    parser = ArgumentParser("allRank")
    parser.add_argument("--job-dir", help="Base output path for all experiments", required=True)
    parser.add_argument("--run-id", help="Name of this run to be recorded (must be unique within output dir)",
                        required=True)
    parser.add_argument("--config-file-name", required=True, type=str, help="Name of json file with config")
    # Added by Yuchuan on 21/03/2023.
    parser.add_argument("--use_transformer", required=True, type=str, help="Whether to use transformer in the model.")
    parser.add_argument("--data_dir", required=True, type=str, help="Data directory.")
    parser.add_argument("--output_dir", required=True, type=str, help="Output directory for the model.")


    return parser.parse_args()


def run():
    # reproducibility
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    torch.set_num_threads(1)
    np.random.seed(42)

    args = parse_args()
    paths = PathsContainer.from_args(args.job_dir, args.run_id, args.config_file_name)

    paths.output_dir = args.output_dir
    create_output_dirs(paths.output_dir)

    logger = init_logger(paths.output_dir)
    logger.info(f"created paths container {paths}")

    # read config
    config = Config.from_json(paths.config_path)
    logger.info("Config:\n {}".format(pformat(vars(config), width=1)))

    output_config_path = os.path.join(paths.output_dir, "used_config.json")
    execute_command("cp {} {}".format(paths.config_path, output_config_path))

    # train_ds, val_ds
    train_ds, val_ds = load_libsvm_dataset(
        # replace with the data path from args
        input_path=args.data_dir,
        slate_length=config.data.slate_length,
        validation_ds_role=config.data.validation_ds_role,
    )

    n_features = train_ds.shape[-1]
    assert n_features == val_ds.shape[-1], "Last dimensions of train_ds and val_ds do not match!"

    # train_dl, val_dl
    train_dl, val_dl = create_data_loaders(
        train_ds, val_ds, num_workers=config.data.num_workers, batch_size=config.data.batch_size)

    tmp = [(xb, yb, indices) for xb, yb, indices in train_dl]
    # xb: [64, 240, 46]
    # yb: [64, 240]
    # indices: [64, 240]
    # print('tmp: ', tmp[0][0].shape, tmp[0][1].shape, tmp[0][2].shape)

    # gpu support
    dev = get_torch_device()
    logger.info("Model training will execute on {}".format(dev.type))

    # instantiate model
    # print(args.use_transformer)
    if args.use_transformer == '1':
        print('-'*100)
        model = make_model(n_features=n_features, **asdict(config.model, recurse=False))
    else:
        model = make_model(config.model.fc_model, None, config.model.post_model, n_features)

    if torch.cuda.device_count() > 1:
        model = CustomDataParallel(model)
        logger.info("Model training will be distributed to {} GPUs.".format(torch.cuda.device_count()))
    model.to(dev)

    # load optimizer, loss and LR scheduler
    optimizer = getattr(optim, config.optimizer.name)(params=model.parameters(), **config.optimizer.args)
    loss_func = partial(getattr(losses, config.loss.name), **config.loss.args)
    if config.lr_scheduler.name:
        scheduler = getattr(optim.lr_scheduler, config.lr_scheduler.name)(optimizer, **config.lr_scheduler.args)
    else:
        scheduler = None

    with torch.autograd.detect_anomaly() if config.detect_anomaly else dummy_context_mgr():  # type: ignore
        # run training
        result = fit(
            model=model,
            loss_func=loss_func,
            optimizer=optimizer,
            scheduler=scheduler,
            train_dl=train_dl,
            valid_dl=val_dl,
            config=config,
            device=dev,
            output_dir=paths.output_dir,
            tensorboard_output_path=paths.tensorboard_output_path,
            **asdict(config.training)
        )

    dump_experiment_result(args, config, paths.output_dir, result)

    if urlparse(args.job_dir).scheme == "gs":
        copy_local_to_gs(paths.local_base_output_path, args.job_dir)


if __name__ == "__main__":
    run()
