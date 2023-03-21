#!/usr/bin/env bash

DIR=$(dirname $0)
PROJECT_DIR="$(cd $DIR/..; pwd)"

export PYTHONPATH=$PROJECT_DIR
cd $PROJECT_DIR

python allrank/data/generate_dummy_data.py
python allrank/main.py \
       --config-file-name scripts/local_config.json \
       --run-id test_run \
       --job-dir task-data \
       --output_dir results
