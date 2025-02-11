#!/bin/bash

# This script needs both curl and jq installed.
# It will go over all the tables with daily partitioning and will remove all partitions older than 21 days
# It uses jq to parse the JSON output from the REST API, extracting the "dataset" element and flatten all the rows.
# Then it reads line by line and calls the QuestDB API with each ALTER TABLE statement.


#!/bin/bash

# Configuration
ROOT_DIRECTORY="/root/.questdb/db"
TABLE_NAME="YOUR_TABLE_NAME"
S3_BUCKET="YOUR_BUCKET_NAME"
S3_KEY_PREFIX="questdb-archive/your-table"

# Determine OS type and compute the date 21 days ago
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS (BSD date)
    OLDER_THAN_DATE=$(date -v-21d '+%Y-%m-%d')
elif [[ "$(uname -s)" == "Linux" ]]; then
    # Linux (GNU date)
    OLDER_THAN_DATE=$(date -d '21 days ago' '+%Y-%m-%d')
else
    echo "Unsupported OS. Exiting."
    exit 1
fi

echo "Processing partitions older than: $OLDER_THAN_DATE"

# Convert and detach partitions older than 21 days in QuestDB
curl -G "http://localhost:9000/exec" --data-urlencode "query=ALTER TABLE $TABLE_NAME CONVERT PARTITION TO PARQUET WHERE ts < '$OLDER_THAN_DATE'"
curl -G "http://localhost:9000/exec" --data-urlencode "query=ALTER TABLE $TABLE_NAME DETACH PARTITION WHERE ts < '$OLDER_THAN_DATE'"

# Find and process detached partitions
find "$ROOT_DIRECTORY" -type d -name "*.detached" | while read detached_dir; do
    echo "Processing detached partition: $detached_dir"

    # Compress Parquet files
    find "$detached_dir" -type f -name "*.parquet" | while read parquet_file; do
        echo "Compressing $parquet_file"
        gzip "$parquet_file"
    done

    # Upload to S3
    echo "Uploading $detached_dir to s3://$S3_BUCKET/$S3_KEY_PREFIX/$(basename $detached_dir)/"
    aws s3 cp "$detached_dir" "s3://$S3_BUCKET/$S3_KEY_PREFIX/$(basename $detached_dir)/" --recursive

    # Remove local detached partition directory
    echo "Deleting local partition: $detached_dir"
    rm -rf "$detached_dir"
done

echo "Partition cleanup complete."
