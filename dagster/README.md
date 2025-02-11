# Using Dagster for Data Orchestration

## Overview

This folder contains a data pipeline implemented using [Dagster](https://dagster.io/). The pipeline performs the following tasks:

1. **Convert to Parquet a partition from QuestDB**: Use a SQL command to convert a specific partition to Parquet format.
2. **Detach the partition**: Prepare the partition for external handling by detaching it from QuestDB.
3. **Compress and upload files to S3**: Compress Parquet files and upload them to an S3 bucket.
4. **Clean up local files**: Delete the partition folder from the local filesystem.

The pipeline showcases how Dagster integrates with external tools like PostgreSQL-compatible databases (QuestDB), S3 for cloud storage, and local filesystem operations.

## Prerequisites

- Python 3.9 or later installed.
- Basic understanding of Dagster.
- AWS credentials with access to the desired S3 bucket.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/questdb/data-orchestration-and-scheduling-samples.git
   cd data-orchestration-and-scheduling-samples/dagster
   ```

2. **Install the dependencies:**
   ```bash
   pip install -e "[.dev]"
   ```

3. **Start the Dagster UI:**
   ```bash
   dagster dev
   ```

4. **Access the Dagster UI:**
   Open your browser and navigate to [http://localhost:3000](http://localhost:3000).

## Running the Pipeline

### Run the pipeline manually:

1. In the Dagster UI, select the `questdb_partition_exporter` job and click "Launchpad."
2. Edit the `resources` configuration in the Dagster UI or in the `dagster.yaml` file to provide values for:
   - `questdb_database_root`: This should point to the `/db` folder inside your QuestDB root directory.
   - `aws_access_key_id`
   - `aws_secret_access_key`
   - `region_name`
3. Click "Launch Run."

### Monitor the Pipeline:

- Use the Dagster UI to view task execution details and logs.
- Verify the S3 bucket for the uploaded files.

## Scheduling

The pipeline is pre-configured with a daily schedule that runs at midnight UTC. The schedule will be disabled on the Dagster UI, but if you navigate to the "Automation" tab, you can toggle it on. You can modify the schedule directly in the `assets.py` file:

```python
@schedule(
    cron_schedule="0 0 * * *",  # At midnight UTC
    job=questdb_partition_exporter_job,
    execution_timezone="UTC"
)
```

## QuestDB Integration

This pipeline demonstrates how to integrate with QuestDB:

### Connecting to QuestDB:

We use the `psycopg` PostgreSQL client to connect to QuestDB. The connection details (like the connection string) are provided in the `postgres_resource` resource configuration.

Example resource configuration:

```python
@resource(config_schema={"connection_string": str})
def postgres_resource(context):
    conn = psycopg.connect(context.resource_config["connection_string"])
    try:
        yield conn
    finally:
        conn.close()
```

### Sending SQL Queries:

SQL operations like converting partitions to Parquet and detaching them are executed via the `cursor.execute()` method.

Example query execution:

```python
sql_query = f"ALTER TABLE ecommerce_stats CONVERT PARTITION TO PARQUET WHERE ts = '{execution_date}'"
with context.resources.postgres.cursor() as cursor:
    cursor.execute(sql_query)
```

### Accessing the Filesystem:

The pipeline accesses QuestDB’s local data directory (specified as `questdb_database_root` in the config) to directly manipulate detached partition folders.

The filesystem is accessed using Python’s `os`, `glob`, and `shutil` libraries.

Example file search:

```python
directory_pattern = f"{questdb_database_root}/{table_name}~*/{execution_date}.detached/**"
files = glob.glob(directory_pattern, recursive=True)
```

## Next Steps

- Explore additional Dagster features like [assets](https://docs.dagster.io/concepts/assets) and [sensors](https://docs.dagster.io/concepts/sensors).
- Integrate additional data processing steps into the pipeline.

For more details, refer to the [Dagster documentation](https://docs.dagster.io/).
