# Using Bash and Cron for Data Orchestration

## Overview
This folder contains a **lightweight** data pipeline implemented using **Bash and Cron**. The pipeline performs the following tasks:

1. **Export partitions older than 21 days** from QuestDB.
2. **Convert the partitions to Parquet format**.
3. **Upload the Parquet files to S3**.
4. **Delete the local partition folder after upload**.

This approach provides **a minimal way** to schedule ETL jobs without requiring a full-fledged orchestration tool like **Airflow** or **Dagster**. Please note this workflow does not provide
error control or backfilling, so it is not as robust as using a proper orchestrator.

---

## Prerequisites
To run this script, ensure that you have the following installed:

- **Linux or macOS** (or Windows WSL)
- **QuestDB** running locally (`http://localhost:9000`) (or change the script to point to your installation)
- **AWS CLI** configured (`aws configure`)
- **Cron (for scheduling)**

---

## Setup & Execution

### **1. Clone the Repository**

```bash
git clone https://github.com/questdb/data-orchestration-and-scheduling-samples.git
cd data-orchestration-and-scheduling-samples/bash
```

### **2. Update the Configuration**
Edit the script `drop_partitions_older_than_21_days.sh` to match your setup:

```bash
ROOT_DIRECTORY="/path/to/questdb/db"
TABLE_NAME="YOUR_TABLE"
S3_BUCKET="YOUR-BUCKET"
S3_KEY_PREFIX="questdb-archive/your-table"
```

### **3. Run the Script**

Manually execute the script:

```bash
bash drop_partitions_older_than_21_days.sh
```

If everything is configured correctly, this will:
- Convert and detach partitions older than 21 days in QuestDB.
- Compress the generated Parquet files.
- Upload them to S3.
- Delete the local partition folder.

---

## Automating with Cron
To schedule the script to run **daily at midnight**, add the following line to your crontab:

```bash
0 0 * * * /bin/bash /path/to/drop_partitions_older_than_21_days.sh >> /var/log/questdb_partition_cleanup.log 2>&1
```

To edit your crontab:

```bash
crontab -e
```

---

## QuestDB Integration

This script demonstrates how to integrate with **QuestDB**:

### **Connecting to QuestDB**
The script interacts with QuestDB via its HTTP REST API at `http://localhost:9000/exec`.

Example query execution:

```bash
curl -G "http://localhost:9000/exec" --data-urlencode "query=ALTER TABLE $TABLE_NAME CONVERT PARTITION TO PARQUET WHERE ts < '$OLDER_THAN_DATE'"
```

### **Accessing the Filesystem**
The script accesses QuestDB’s **local data directory** (`ROOT_DIRECTORY`) to **directly manipulate detached partition folders**.

Example directory search:

```bash
find "$ROOT_DIRECTORY" -type d -name "*.detached"
```

---

## Next Steps
- Enhance logging and error handling.
- Extend the script to perform additional data processing.
- Use a proper orchestrator like the Dagster and Airflow examples provided.



