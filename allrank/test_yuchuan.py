import os
import torch
import numpy as np
from allrank.config import Config
from allrank.data.dataset_loading import load_libsvm_dataset_role
from allrank.models.model import make_model
from allrank.models.model_utils import get_torch_device
from allrank.utils.command_executor import execute_command
from allrank.utils.file_utils import create_output_dirs, PathsContainer
from allrank.utils.ltr_logging import init_logger
from argparse import ArgumentParser, Namespace
from attr import asdict
from pprint import pformat

from torch.utils.data import DataLoader
from allrank.training.train_utils import compute_metrics

from pkg_resources import Requirement, resource_filename


def parse_args() -> Namespace:
    parser = ArgumentParser("allRank")
    parser.add_argument("--config-file-name", required=True, type=str, help="Name of json file with config")
    parser.add_argument("--use_transformer", required=True, type=str, help="Whether to use transformer in the model.")
    parser.add_argument("--data_dir", required=True, type=str, help="Data directory.")
    parser.add_argument("--output_dir", required=True, type=str, help="Output directory for the model.")

    return parser.parse_args()

def run():

    args = parse_args()
    config = Config.from_json(args.config_file_name)
    test_ds = load_libsvm_dataset_role(
        role="test",
        input_path=args.data_dir,
        slate_length=config.data.slate_length
    )

    n_features = test_ds.shape[-1]
    test_dl = DataLoader(test_ds, batch_size=config.data.batch_size, num_workers=config.data.num_workers, shuffle=False)

    # gpu support
    device = get_torch_device()
    # instantiate model
    if args.use_transformer == '1':
        model = make_model(n_features=n_features, **asdict(config.model, recurse=False))
    else:
        model = make_model(config.model.fc_model, None, config.model.post_model, n_features)
    model.to(device)
    state_dict = torch.load(os.path.join(args.output_dir, "model.pkl"))
    model.load_state_dict(state_dict)
    model.eval()
    test_metrics = compute_metrics(config.metrics, model, test_dl, device)
    print(test_metrics)

if __name__ == "__main__":
    run()
