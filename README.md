# Data Orchestration and Scheduling Samples

This repository contains examples of data orchestration and scheduling using different tools:
- **Airflow**
- **Dagster**
- **Bash and Cron**

Each folder contains an example implementation of a data pipeline designed to:
1. Export a partition from QuestDB.
2. Convert the partition to Parquet format.
3. Upload the Parquet file to S3.
4. Delete the local partition folder.

## Folder Structure

- **airflow**: Example implementation using Apache Airflow.
- **dagster**: Example implementation using Dagster.
- **bash_cron**: Example implementation using a simple Bash script and Cron.

## Getting Started

1. Navigate to the folder of your preferred tool.
2. Follow the specific instructions in its `README.md` file to set up and run the example.

### Goals

This repository aims to demonstrate:
- How to use modern orchestration tools for real-world ETL scenarios.
- Comparing flexibility and configuration between Airflow, Dagster, and a lightweight Bash + Cron approach.
- Helping you decide which orchestration tool is suitable for your workflows.

Feel free to explore, adapt, and contribute to these examples!
