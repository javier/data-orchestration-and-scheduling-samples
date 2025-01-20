from dagster import op, graph, job, resource, Out, schedule, repository
import pendulum
import glob
import os
import shutil
import gzip
import boto3
import psycopg

# Define resources for PostgreSQL and S3
@resource(config_schema={"connection_string": str})
def postgres_resource(context):
    conn = psycopg.connect(context.resource_config["connection_string"])
    try:
        yield conn
    finally:
        conn.close()

@resource(config_schema={"aws_access_key_id": str, "aws_secret_access_key": str, "region_name": str})
def s3_resource(context):
    session = boto3.session.Session(
        aws_access_key_id=context.resource_config["aws_access_key_id"],
        aws_secret_access_key=context.resource_config["aws_secret_access_key"],
        region_name=context.resource_config["region_name"]
    )
    return session.client('s3')

@resource(config_schema={"database_root": str})
def questdb_database_root(context):
    return context.resource_config["database_root"]

# Define operations
@op(required_resource_keys={'postgres'}, out=Out(str))
def convert_to_parquet(context, execution_date: str):
    sql_query = f"ALTER TABLE ecommerce_stats CONVERT PARTITION TO PARQUET WHERE ts = '{execution_date}'"
    with context.resources.postgres.cursor() as cursor:
        cursor.execute(sql_query)
    context.log.info(f"Converted to parquet for date: {execution_date}")
    return execution_date

@op(required_resource_keys={'postgres'}, out=Out(str))
def detach_partition(context, execution_date: str):
    sql_query = f"ALTER TABLE ecommerce_stats DETACH PARTITION WHERE ts = '{execution_date}'"
    with context.resources.postgres.cursor() as cursor:
        cursor.execute(sql_query)
    context.log.info(f"Detached partition for date: {execution_date}")
    return execution_date

@op(required_resource_keys={'s3', 'questdb_database_root'}, out=Out(str))
def upload_files_to_s3(context, execution_date: str):
    root_directory = context.resources.questdb_database_root
    table_name = "ecommerce_stats"
    directory_pattern = f"{root_directory}/{table_name}~*/{execution_date}.detached/**"
    context.log.info(f"Looking for files matching pattern: {directory_pattern}")
    files = glob.glob(directory_pattern, recursive=True)
    if not files:
        context.log.warning(f"No files found for pattern: {directory_pattern}")
    else:
        context.log.info(f"Found {len(files)} files: {files}")
    for file_path in files:
        try:
            if os.path.isdir(file_path):
                context.log.info(f"Skipping directory: {file_path}")
                continue
            if file_path.endswith('.parquet'):
                context.log.info(f"Compressing file: {file_path}")
                compressed_file = file_path + '.gz'
                with open(file_path, 'rb') as f_in, gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                file_path = compressed_file
            filename = os.path.relpath(file_path, start=root_directory)
            s3_key = f"dagster-demo/{filename}"
            context.log.info(f"Uploading {file_path} to S3 bucket 'questdb-javier-demos' with key {s3_key}")
            context.resources.s3.upload_file(Bucket='questdb-javier-demos', Key=s3_key, Filename=file_path)
            context.log.info(f"Successfully uploaded {file_path} to S3.")
        except Exception as e:
            context.log.error(f"Failed to process file {file_path}: {e}")
            raise
    return execution_date

@op(required_resource_keys={'questdb_database_root'})
def delete_folder(context, execution_date: str):
    root_directory = context.resources.questdb_database_root
    table_name = "ecommerce_stats"
    folder_path_pattern = f"{root_directory}/{table_name}~*/{execution_date}.detached"
    folder_paths = glob.glob(folder_path_pattern)
    for folder_path in folder_paths:
        shutil.rmtree(folder_path)
    context.log.info(f"Deleted folder for date: {execution_date}")

@op(out=Out(str))
def get_execution_date():
    return pendulum.now('UTC').subtract(days=1).format('YYYY-MM-DD')

@graph
def questdb_partition_exporter():
    execution_date = get_execution_date()
    delete_folder(upload_files_to_s3(detach_partition(convert_to_parquet(execution_date))))

questdb_partition_exporter_job = questdb_partition_exporter.to_job(
    resource_defs={
        "postgres": postgres_resource,
        "s3": s3_resource,
        "questdb_database_root": questdb_database_root
    }
)

@schedule(
    cron_schedule="0 0 * * *",  # At midnight UTC
    job=questdb_partition_exporter_job,
    execution_timezone="UTC"
)
def daily_questdb_exporter_schedule(context):
    return {}

@repository
def questdb_repository():
    return [questdb_partition_exporter_job, daily_questdb_exporter_schedule]

