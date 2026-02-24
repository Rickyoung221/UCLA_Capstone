# Hadoop-Hive-Spark cluster on Docker

## Software

* [Hadoop 3.3.6](https://hadoop.apache.org/)

* [Hive 3.1.3](http://hive.apache.org/)

* [Spark 3.5.3](https://spark.apache.org/)

## Quick Start
First build the image for each container (must build `base` first; use `--no-cache` if you changed base or hit JAVA_HOME/arch issues):
```bash
docker build -t hadoop-hive-spark-base ./base
docker build -t hadoop-hive-spark-master ./master
docker build -t hadoop-hive-spark-worker ./worker
docker build -t hadoop-hive-spark-history ./history
```
To start the container:
```bash
docker compose up -d
```
(Or `docker-compose up` if you use the legacy compose.)
## Load data into HDFS
Start from the master container, and move the data to the master container by the ```docker cp``` command.

Here's an example of loading file into HDFS:
```
hdfs dfs -mkdir -p /data/myfiles
hdfs dfs -put name.csv /data/myfiles/
hdfs dfs -ls  /data/myfiles
```

## Data partitioning in Hive
Refer to the file [partition/partition5mb.py](partition/partition5mb.py)
Run the python file from the master container

## Execute query
##### Spark + Hive: 
Refer to the file [hive-task1.py](hive-task1.py)
##### Spark with different repartition
Refer to the file [no-hive-task1.py](no-hive-task1.py)

Run the python file from the master container

## Monitor CPU/RAM usage of containers
Use the file [monitor.ps1](monitor.ps1) outside of docker

## Capstone: Partitioning Advisor

This project implements a **lightweight, workload-aware Partitioning Advisor** on top of a Spark–Hive benchmark (Hive partition vs Spark repartition): given data size and query type, it recommends Hive partitioning or Spark repartition and partition count. Goals and scope: [docs/PROJECT_GOALS.md](docs/PROJECT_GOALS.md).

### How to use the Advisor

1. **Build the experiment summary** (once, or after updating data). From the project root:
   ```bash
   python3 advisor/scripts/build_summary.py
   ```
   Output: `advisor/experiment_summary.csv`.

2. **Get a recommendation**. From the project root, e.g.:
   ```bash
   python3 advisor/advisor.py --data-size 50mb --query-type join
   python3 advisor/advisor.py -s 500mb -q aggregate -v   # -v shows runtime/cpu/memory details
   ```
   - `--data-size` / `-s`: 5mb, 50mb, 500mb, 5gb  
   - `--query-type` / `-q`: aggregate, join, window  
   - `--objective` / `-o`: runtime (default), cpu, memory  

For more (Python API, evaluation script, runtime plot), see **[advisor/README.md](advisor/README.md)**.

### Documentation

- **Capstone report**: [docs/Capstone_Report.md](docs/Capstone_Report.md)
- Experiment design and summary schema: [docs/EXPERIMENT_DESIGN.md](docs/EXPERIMENT_DESIGN.md)
- Advisor design: [docs/ADVISOR_DESIGN.md](docs/ADVISOR_DESIGN.md)

## Access interfaces with the following URL

##### Hadoop

ResourceManager: http://localhost:8088

NameNode: http://localhost:9870

HistoryServer: http://localhost:19888

Datanode1: http://localhost:9864
Datanode2: http://localhost:9865

NodeManager1: http://localhost:8042
NodeManager2: http://localhost:8043

##### Spark
master: http://localhost:8080

worker1: http://localhost:8081
worker2: http://localhost:8082

history: http://localhost:18080

##### Hive
URI: jdbc:hive2://localhost:10000
