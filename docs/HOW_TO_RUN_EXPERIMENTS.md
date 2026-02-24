# How to Run Experiments

Use this to run tasks in the Docker cluster, collect runtimes from YARN, and update results and the summary (e.g. to add 500mb Join 16/32).

---

## Prerequisites

- Docker and Docker Compose installed; cluster built and started (see [GETTING_STARTED.md](GETTING_STARTED.md)).
- Data on HDFS (e.g. `/data/500mb.csv`) and paths in scripts matching (e.g. `hdfs://master:8020/data/500mb.csv`).

---

## Step 1: Start the cluster

```bash
cd /path/to/UCLA_Capstone
docker-compose up -d
```

When all containers are running, open http://localhost:8088 (YARN) in a browser to confirm.

---

## Step 2: Copy scripts and data into the master container

(If the project is already mounted in the container, you can skip copying scripts; ensure data is on HDFS.)

```bash
# Find the master container name (often xxx-master-1)
docker ps

# Copy 500mb directory and dependencies (replace <container> with your container name)
docker cp 500mb <container>:/opt/
docker cp partition <container>:/opt/
```

If 500mb data is not on HDFS yet, copy the CSV into the container and put it on HDFS:

```bash
docker cp /path/to/500mb.csv <container>:/tmp/
docker exec -it <container> bash
# Inside the container:
hdfs dfs -mkdir -p /data
hdfs dfs -put /tmp/500mb.csv /data/
exit
```

---

## Step 3: Run tasks in the master container

Example: adding **500mb Join Spark-16 / Spark-32**:

```bash
docker exec -it <container> bash
cd /opt/500mb   # or wherever you copied

# Run 500mb Join 16 partitions (application name will be Test500MB_Join_16 or similar)
spark-submit --master yarn no-hive-task2_16.py

# Then 32 partitions
spark-submit --master yarn no-hive-task2_32.py

exit
```

While running, check http://localhost:8088 for the application list; note **Application ID** and **runtime (seconds)**.

---

## Step 4: Record runtime from YARN / Spark History

- **YARN**: http://localhost:8088 → open the finished application → use **Finished** time minus **Start** time as runtime (seconds), or use Duration from the Spark UI.
- **Spark History**: http://localhost:18080 → find the application (e.g. Test500MB_Join_16) → note duration (seconds).

Record the values, e.g.:
- Test500MB_Join_16 → **19.7** s  
- Test500MB_Join_32 → **19.9** s  

(Use your actual numbers if different.)

---

## Step 5: Update 500mb_results.csv

On your machine, open `stats_collection_tools/500mb_results.csv` and add two rows (same header; id can be a placeholder; name and runtime_seconds must be correct):

```csv
id,name,start_time,launch_time,finish_time,runtime_seconds
...,Test500MB_Join_16,,,.,<your_16_seconds>
...,Test500MB_Join_32,,,.,<your_32_seconds>
```

Save. (`build_summary.py` recognizes these names and will include them in the Join summary.)

---

## Step 6: Regenerate the summary and plot

From the project root on your machine:

```bash
python3 advisor/scripts/build_summary.py
python3 advisor/scripts/plot_runtime.py
```

Open `advisor/experiment_summary.csv` and `advisor/scripts/runtime_comparison.png`; you should see 500mb Join Spark-16 and Spark-32 in the data and figure.

---

## Other scales / query types

- **Script locations**: Under `5mb/`, `50mb/`, `500mb/` there are `hive-task1/2/3.py` (Hive) and `no-hive-task1/2/3_4|16|32.py` (Spark 4/16/32). task1=aggregate, task2=join, task3=window.
- **Application names**: If the name is `Test*MB_Join_*` (or equivalent), the summary script will treat it as join.
- **Results files**: Write to `stats_collection_tools/5mb_results.csv`, `50mb_results.csv`, `500mb_results.csv` in the same format as existing rows.

See [EXPERIMENT_DESIGN.md](EXPERIMENT_DESIGN.md) for reproduction and naming rules.
