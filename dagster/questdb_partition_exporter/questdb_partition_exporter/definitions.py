from dagster import repository
from .assets import questdb_partition_exporter_job, daily_questdb_exporter_schedule

@repository
def questdb_repository():
    """
    A repository that contains the job and schedule for the QuestDB partition exporter.
    """
    return [questdb_partition_exporter_job, daily_questdb_exporter_schedule]



