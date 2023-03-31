#!/usr/bin/env bash

DIR=$(dirname $0)
PROJECT_DIR="$(cd $DIR/..; pwd)"

export PYTHONPATH=$PROJECT_DIR

NUM_RUNS=1
use_transformer=1

start=$(date +%s.%3N)
# Loop through and execute the Python command multiple times
for i in $(seq 1 $NUM_RUNS)
do
    python allrank/main_yuchuan.py \
           --config-file-name scripts/local_config.json \
           --data_dir new_dataset/MQ2008/Fold$i \
           --use_transformer $use_transformer \
           --run-id test_run \
           --job-dir task-data \
           --output_dir total_results/results_mq2008_mse_ndcg5_Fold$i
done

end=$(date +%s.%3N)
runtime=$(echo "$end - $start" | bc)
echo "Execution time: $runtime seconds."

results=($(for i in $(seq 1 $NUM_RUNS)
do
    python allrank/test_yuchuan.py \
                    --config-file-name scripts/local_config.json \
                    --use_transformer $use_transformer \
                    --data_dir new_dataset/MQ2008/Fold$i \
                    --output_dir total_results/results_mq2008_mse_ndcg5_Fold$i
done))

echo "Results: ${results[@]}"

#ndcg_5=$(echo "${results[@]}" | awk '{for(i=2;i<=NF;i+=6) sum+=$i} END{print sum/$NUM_RUNS}')

ndcg_5=$(echo "${results[@]}" | awk "{for(i=2;i<=NF;i+=10) sum+=\$i} END{print sum/$NUM_RUNS}")
ndcg_10=$(echo "${results[@]}" | awk "{for(i=4;i<=NF;i+=10) sum+=\$i} END{print sum/$NUM_RUNS}")
ndcg_20=$(echo "${results[@]}" | awk "{for(i=6;i<=NF;i+=10) sum+=\$i} END{print sum/$NUM_RUNS}")

mrr_5=$(echo "${results[@]}" | awk "{for(i=8;i<=NF;i+=10) sum+=\$i} END{print sum/$NUM_RUNS}")
mrr_10=$(echo "${results[@]}" | awk "{for(i=10;i<=NF;i+=10) sum+=\$i} END{print sum/$NUM_RUNS}")

# Print the array of result values
echo "ndcg_5: ${ndcg_5}"
echo "ndcg_10: ${ndcg_10}"
echo "ndcg_20: ${ndcg_20}"
echo "mrr_5: ${mrr_5}"
echo "mrr_10: ${mrr_10}"