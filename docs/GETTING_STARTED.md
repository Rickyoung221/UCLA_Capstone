# Getting Started

Two paths: **run only the Partitioning Advisor** (recommended first), or **start the full Docker cluster** (for reproducing experiments).

---

## Option 1: Run the Advisor only (local, no Docker)

From the project root in a terminal:

### 1. Ensure the experiment summary exists

```bash
cd /path/to/UCLA_Capstone
python3 advisor/scripts/build_summary.py
```

This creates or updates `advisor/experiment_summary.csv` (if data is present it will be generated).

### 2. Run the Advisor

```bash
python3 advisor/advisor.py --data-size 50mb --query-type join
```

Or with short options:

```bash
python3 advisor/advisor.py -s 5mb -q aggregate -o runtime
```

**Requirements**: Python 3 only; no other dependencies.

---

## Option 2: Start the Docker cluster (Hadoop + Hive + Spark)

Use this to run jobs in the cluster, reproduce experiments, or collect new data.

### 1. Build images (first time or after changing Dockerfiles)

```bash
cd /path/to/UCLA_Capstone

docker build -t hadoop-hive-spark-base ./base
docker build -t hadoop-hive-spark-master ./master
docker build -t hadoop-hive-spark-worker ./worker
docker build -t hadoop-hive-spark-history ./history
```

### 2. Start the cluster

```bash
docker-compose up
```

Or in the background:

```bash
docker-compose up -d
```

### 3. Run jobs from the master (optional)

```bash
docker exec -it <master-container-name> bash
# Inside the container: run scripts under 5mb/, 50mb/, 500mb/, or run partition/hive tasks
```

**Requirements**: Docker and Docker Compose installed.

---

## Running with Docker Desktop (Option 2 step-by-step)

1. **Start Docker Desktop**  
   Open Docker Desktop and wait until it shows as running (green/Running).

2. **Allocate enough resources**  
   The cluster runs 5 containers (metastore, master, worker1, worker2, history). In Docker Desktop:  
   - **Settings → Resources**: Memory at least **4GB** (6–8GB recommended); CPU and disk as default or slightly higher.  
   - Click **Apply & Restart**.

3. **Open a terminal in the project directory**  
   - **macOS**: Terminal or iTerm, `cd` to the project root.  
   - **Windows**: Use Docker Desktop’s **Terminal** (PowerShell) or WSL/CMD, and `cd` to the project root.

4. **Build and start (same as Option 2)**  
   ```bash
   cd /path/to/UCLA_Capstone

   docker build -t hadoop-hive-spark-base ./base
   docker build -t hadoop-hive-spark-master ./master
   docker build -t hadoop-hive-spark-worker ./worker
   docker build -t hadoop-hive-spark-history ./history

   docker-compose up
   ```
   `docker-compose up` keeps the terminal attached and shows logs; use `Ctrl+C` to stop.  
   For background: `docker-compose up -d`; containers appear under Docker Desktop **Containers**.

5. **In Docker Desktop**  
   - **Containers**: You should see master, worker1, worker2, history, metastore.  
   - **Logs**: Click a container to view logs.  
   - In a browser: NameNode http://localhost:9870, ResourceManager http://localhost:8088, Spark Master http://localhost:8080 (see main README).

---

## Checking that the Docker cluster is up

1. **Docker Desktop → Containers**  
   About **5 running containers**: `metastore`, `master`, `worker1`, `worker2`, `history` (status running/green).

2. **List containers in terminal**  
   ```bash
   docker ps
   ```
   Same 5 containers with STATUS `Up`.

3. **Open the web UIs**  
   If these load, the services are up:  
   - **Hadoop NameNode**: http://localhost:9870  
   - **YARN ResourceManager**: http://localhost:8088  
   - **Spark Master**: http://localhost:8080  

---

## After the cluster is up: what next?

Choose one path (or do A then B):

### Path A: Run experiments in the cluster (reproduce / collect data)

1. **Enter the master container**  
   ```bash
   docker exec -it <master-container-name> bash
   ```
   (Container name may include a project prefix; use `docker ps` to see the master NAME.)

2. **Put data in HDFS**  
   Prepare CSV (e.g. 5mb/50mb/500mb) on the host, copy into the container with `docker cp`, then inside the container:  
   ```bash
   hdfs dfs -mkdir -p /data
   hdfs dfs -put /path/in/container/5mb.csv /data/
   ```
   If you have partition scripts, follow the README’s “Data partitioning in Hive” section.

3. **Run tasks**  
   In the master container, run scripts under `5mb/`, `50mb/`, `500mb/` (e.g. `python 5mb/hive-task1.py`, `python 5mb/no-hive-task1_4.py`) for all combinations.

4. **Collect results**  
   Record runtimes from YARN (http://localhost:8088) or Spark History (http://localhost:18080); use `docker stats` or scripts in `stats_collection_tools` to collect CPU/memory and produce `*_results.csv` and `*_stats/*.csv`.

5. **Update the summary**  
   On the host, from the project root:  
   ```bash
   python3 advisor/scripts/build_summary.py
   ```

See [docs/EXPERIMENT_DESIGN.md](EXPERIMENT_DESIGN.md) for experiment design and naming.

### Path B: Use the Capstone Advisor (no need for the cluster to be running)

- **Run the Advisor with existing data** (on your machine):  
  ```bash
  python3 advisor/scripts/build_summary.py
  python3 advisor/advisor.py -s 50mb -q join
  ```
- **Evaluation**: Use the evaluation script (recommendation vs true best, agreement rate) and runtime plot for the report.

Current experiment data is sufficient for the Advisor; you can follow Path B without running new experiments.

---

## Quick check (Advisor only)

When running only the Advisor, success looks like:

```
Recommendation:
  strategy:        spark_repartition
  num_partitions:  4
  reason:          lowest runtime in 50mb join experiments
```

If you see `FileNotFoundError: ... experiment_summary.csv`, run once:

```bash
python3 advisor/scripts/build_summary.py
```

Then run `advisor/advisor.py` again.
