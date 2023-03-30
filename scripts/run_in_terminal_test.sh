#!/usr/bin/env bash

DIR=$(dirname $0)
PROJECT_DIR="$(cd $DIR/..; pwd)"

export PYTHONPATH=$PROJECT_DIR
#cd $PROJECT_DIR

python allrank/test_yuchuan.py \
        --config-file-name scripts/local_config.json \
        --data_dir data/MQ2008/Fold1 \
        --output_dir results_mq2008_mse_ndcg5_Fold1

