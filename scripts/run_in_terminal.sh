#!/usr/bin/env bash

DIR=$(dirname $0)
PROJECT_DIR="$(cd $DIR/..; pwd)"

export PYTHONPATH=$PROJECT_DIR
#cd $PROJECT_DIR
#
## python allrank/data/generate_dummy_data.py
#python allrank/main_yuchuan.py \
#       --config-file-name scripts/local_config.json \
#       --run-id test_run \
#       --job-dir task-data \
#       --output_dir results_mq2008_mse_ndcg5_Fold1

# Define the number of times to run the Python command
NUM_RUNS=1
results=()

# Loop through and execute the Python command multiple times
for i in $(seq 1 $NUM_RUNS)
do
    python allrank/main_yuchuan.py \
           --config-file-name scripts/local_config.json \
           --data_dir new_dataset/MQ2008/Fold$i \
           --use_transformer 0 \
           --run-id test_run \
           --job-dir task-data \
           --output_dir total_results/results_mq2008_mse_ndcg5_Fold$i
done

for i in $(seq 1 $NUM_RUNS)
do
#    result=$(python my_script.py arg1 arg2 $i)
    result=$(python allrank/test_yuchuan.py \
                    --config-file-name scripts/local_config.json \
                    --use_transformer 0 \
                    --data_dir new_dataset/MQ2008/Fold$i \
                    --output_dir total_results/results_mq2008_mse_ndcg5_Fold$i)
    results+=("$result")
done

# Print the array of result values
echo "Results: ${results[@]}"
