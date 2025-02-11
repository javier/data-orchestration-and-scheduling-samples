# Using Apache Airflow for Data Orchestration

## Overview

This folder contains a data pipeline implemented using [Apache Airflow](https://airflow.apache.org/). The pipeline performs the following tasks:

1. Export a partition from QuestDB.
2. Convert the partition to Parquet format.
3. Upload the Parquet file to S3.
4. Delete the local partition folder.

## Prerequisites

- Python 3.9 or later installed.
- Docker installed.
- Basic understanding of Apache Airflow.
- AWS credentials with access to the desired S3 bucket.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/questdb/data-orchestration-and-scheduling-samples.git
   cd data-orchestration-and-scheduling-samples/airflow
   ```

2. **Install Docker Compose:**
   Ensure Docker Compose is installed by following the [official guide](https://docs.docker.com/compose/install/).

3. **Start the Airflow environment:**
   ```bash
   docker compose up
   ```

   This command starts the Airflow web server, scheduler, and necessary components using Docker Compose. The
   `docker-compose.yaml` file we are using is taken directly from the [Apache Airflow docs](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#fetching-docker-compose-yaml).

4. **Access the Airflow UI:**
   Open your browser and navigate to [http://localhost:8080](http://localhost:8080).

   - Default username: `airflow`
   - Default password: `airflow`

5. **DAG file:**
   The docker compose file will mount the local `./dags/` directory on the airflow container, so the sample script in
   this repository will be directly accesible to Airflow.

## Running the Pipeline

1. **Trigger the DAG manually:**
   - In the Airflow UI, navigate to the "DAGs" view.
   - Find the `questdb_partition_exporter` DAG.
   - Click the "Trigger DAG" button.

2. **Monitor the Pipeline:**
   - Use the Airflow UI to view task execution details and logs.
   - Verify the S3 bucket for the uploaded files.

## Scheduling

The pipeline is pre-configured to run daily at midnight UTC. This is controlled by the `schedule_interval` parameter in the DAG definition:

```python
schedule_interval='@daily'
```

You can modify the schedule to suit your needs. For example:

- Every hour: `schedule_interval='@hourly'`
- Specific time: `schedule_interval='0 12 * * *'` (runs daily at 12 PM UTC).

## QuestDB Integration

This pipeline demonstrates how to integrate with QuestDB:

### Connecting to QuestDB

Airflow uses the `PostgresOperator` to connect to QuestDB via its PostgreSQL interface. The connection details are
configured in the Airflow UI under **Admin > Connections**. Ensure the `postgres_conn_id` in the DAG matches the connection ID in the UI.

Example connection configuration:

- **Connection ID**: `questdb`
- **Host**: QuestDB server host
- **Port**: 8812
- **Schema**: database name (e.g., `qdb`)
- **Login**: username (e.g., `admin`)
- **Password**: password

### Executing SQL Queries

SQL operations such as converting partitions to Parquet and detaching them are performed using the `PostgresOperator`:

```python
convert_to_parquet = PostgresOperator(
    task_id='convert_to_parquet',
    postgres_conn_id='questdb',
    sql="""
    ALTER TABLE ecommerce_stats CONVERT PARTITION TO PARQUET WHERE ts = '{{ (execution_date - macros.timedelta(days=1)) | ds }}'
    """,
    dag=dag,
)
```

### Accessing the Filesystem

The pipeline accesses QuestDB’s local data directory to manipulate detached partition folders. Python’s `os`, `glob`, and `shutil` libraries are used for this purpose.

Example file search:

```python
root_directory = '/questdb_root/db'
directory_pattern = f"{root_directory}/ecommerce_stats~*/{{ yesterday }}.detached/**"
files = glob.glob(directory_pattern, recursive=True)
```

## Next Steps

- Experiment with additional Airflow operators such as [S3FileTransformOperator](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/operators/s3.html).
- Integrate additional data processing steps into the pipeline.

For more details, refer to the [Airflow documentation](https://airflow.apache.org/docs/apache-airflow/stable/index.html).

