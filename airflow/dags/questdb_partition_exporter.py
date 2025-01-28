import pendulum

from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python_operator import PythonOperator
import os
import glob
import shutil
import gzip

root_directory = f'/questdb_root/db'
table_name = "ecommerce_stats"

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': pendulum.datetime(2025, 1, 1, tz="UTC"),  # Set to a past date,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': None,
    'catchup' : False,

}

dag = DAG(
    'questdb_partition_exporter',
    default_args=default_args,
    description='Converts to parquet, detaches, uploads to S3, and removes QuestDB partition from yesterday',
    schedule_interval='@daily',  # This sets the DAG to run once a day at midnight
    catchup=False,
    tags= ['questdb']
)

# Task to convert partition to Parquet
convert_to_parquet = PostgresOperator(
    task_id='convert_to_parquet',
    postgres_conn_id='questdb',
    sql="""
    alter table ecommerce_stats convert partition to parquet where ts = '{{ (execution_date - macros.timedelta(days=1)) | ds }}'
    """,
    dag=dag,
)

# Task to detach the partition
detach_partition = PostgresOperator(
    task_id='detach_partition',
    postgres_conn_id='questdb',
    sql="ALTER TABLE ecommerce_stats DETACH PARTITION WHERE ts = '{{ (execution_date - macros.timedelta(days=1)) | ds }}' ",
    dag=dag,
)

def upload_files_to_s3(yesterday, **kwargs):
    s3_bucket = "questdb-javier-demos"
    s3_key_prefix = "airflow-demo"
    root_directory = '/questdb_root/db'
    table_name = "ecommerce_stats"

    hook = S3Hook(aws_conn_id="AWS-questdb")

    # Adjust the search pattern to consider all files but process only Parquet files for compression
    search_pattern = f"{root_directory}/{table_name}~*/{yesterday}.detached/**"
    files = glob.glob(search_pattern, recursive=True)

    for file in files:
        if os.path.isdir(file):
            continue

        # Check if the file is a Parquet file
        if file.endswith('.parquet'):
            compressed_file = f"{file}.gz"
            # Compress the Parquet file
            with open(file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            file_to_upload = compressed_file
        else:
            file_to_upload = file

        # Determine the new filename for S3, adjusting for whether it was compressed
        filename = os.path.relpath(file_to_upload, start=root_directory)
        s3_key = f"{s3_key_prefix}/{filename}"

        # Upload the file (compressed or not) to S3
        hook.load_file(filename=file_to_upload, bucket_name=s3_bucket, replace=True, key=s3_key)
        print(f"Uploading {filename} to {s3_bucket}/{s3_key}")


upload_to_s3 = PythonOperator(
    task_id='upload_to_s3',
    python_callable=upload_files_to_s3,
    op_kwargs={'yesterday': "{{ (execution_date - macros.timedelta(days=1)) | ds }}"},
    dag=dag,
)

def delete_folder(yesterday, **kwargs):
    folder_path_pattern = f"{root_directory}/{table_name}~*/{yesterday}.detached"

    folder_paths = glob.glob(folder_path_pattern)
    if not folder_paths:
        print(f"No directory found for pattern: {folder_path_pattern}")
        return

    for folder_path in folder_paths:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f"Folder {folder_path} has been deleted successfully.")
        else:
            print(f"Folder {folder_path} not found.")

delete_detached_partition = PythonOperator(
    task_id='delete_folder',
    python_callable=delete_folder,
    op_kwargs={'yesterday': "{{ (execution_date - macros.timedelta(days=1)) | ds }}"},
    dag=dag,
)


convert_to_parquet >> detach_partition >> upload_to_s3 >> delete_detached_partition
