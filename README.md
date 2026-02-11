# Hadoop-Hive-Spark cluster on Docker

## Software

* [Hadoop 3.3.6](https://hadoop.apache.org/)

* [Hive 3.1.3](http://hive.apache.org/)

* [Spark 3.5.3](https://spark.apache.org/)

## Quick Start
First build the image for each container:
```
docker build -t hadoop-hive-spark-base ./base
docker build -t hadoop-hive-spark-master ./master
docker build -t hadoop-hive-spark-worker ./worker
docker build -t hadoop-hive-spark-history ./history
```
To start the container
```
docker-compose up
```
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

本项目延伸为 workload-aware 的 partitioning 建议器：根据数据规模与查询类型推荐 Hive 分区或 Spark repartition 及 partition 数。

- **生成实验汇总表**（供 Advisor 使用）：在项目根目录执行  
  `python3 advisor/scripts/build_summary.py`  
  输出为 `advisor/experiment_summary.csv`。
- 实验设计、汇总表含义与复现方法见 [docs/EXPERIMENT_DESIGN.md](docs/EXPERIMENT_DESIGN.md)。
- Advisor 目录说明见 [advisor/README.md](advisor/README.md)。

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
URI: jdbc:hive2://localhost:10000# UCLA_Capstone
# UCLA_Capstone
