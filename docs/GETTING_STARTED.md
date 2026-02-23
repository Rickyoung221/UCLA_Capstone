# 如何启动

分两种：**只跑 Partitioning Advisor**（推荐先做），或 **启动完整 Docker 集群**（复现实验时用）。

---

## 方式一：只跑 Advisor（本地，无需 Docker）

在终端进入项目根目录，然后：

### 1. 确保有实验汇总表

```bash
cd /Users/rickyang/Documents/GitHub/UCLA_Capstone
python3 advisor/scripts/build_summary.py
```

会生成/更新 `advisor/experiment_summary.csv`（若已有数据会直接生成）。

### 2. 运行 Advisor

```bash
python3 advisor/advisor.py --data-size 50mb --query-type join
```

或简写：

```bash
python3 advisor/advisor.py -s 5mb -q aggregate -o runtime
```

**要求**：本机已安装 **Python 3**，无需其他依赖。

---

## 方式二：启动 Docker 集群（Hadoop + Hive + Spark）

用于在集群里跑任务、复现实验或收集新数据。

### 1. 构建镜像（首次或 Dockerfile 改过后）

```bash
cd /Users/rickyang/Documents/GitHub/UCLA_Capstone

docker build -t hadoop-hive-spark-base ./base
docker build -t hadoop-hive-spark-master ./master
docker build -t hadoop-hive-spark-worker ./worker
docker build -t hadoop-hive-spark-history ./history
```

### 2. 启动集群

```bash
docker-compose up
```

或后台运行：

```bash
docker-compose up -d
```

### 3. 进入 master 跑任务（可选）

```bash
docker exec -it <master容器名> bash
# 在容器内运行 5mb/、50mb/、500mb/ 下的脚本，或执行 partition、hive 任务等
```

**要求**：本机已安装 **Docker** 与 **Docker Compose**。

---

## 在 Docker Desktop 里运行（方式二的具体步骤）

1. **先启动 Docker Desktop**  
   打开 Docker Desktop 应用，等左下角或状态栏显示 Docker 已运行（绿色/Running）。

2. **（建议）调高资源**  
   集群有 5 个容器（metastore、master、worker1、worker2、history），建议在 Docker Desktop 里给足资源：  
   - **Settings → Resources**：Memory 至少 **4GB**（推荐 6–8GB），CPU 和 Disk 按默认或略增。  
   - 改完后点 **Apply & Restart**。

3. **用终端在项目目录执行命令**  
   - **macOS**：打开 Terminal 或 iTerm，执行 `cd` 到项目根目录。  
   - **Windows**：在 Docker Desktop 里点 **Terminal** 打开 PowerShell，或使用 WSL / CMD，同样 `cd` 到项目根目录（例如 `cd C:\Users\你的用户名\...\UCLA_Capstone`）。

4. **构建并启动（与方式二相同）**  
   ```bash
   cd /Users/rickyang/Documents/GitHub/UCLA_Capstone

   docker build -t hadoop-hive-spark-base ./base
   docker build -t hadoop-hive-spark-master ./master
   docker build -t hadoop-hive-spark-worker ./worker
   docker build -t hadoop-hive-spark-history ./history

   docker-compose up
   ```
   `docker-compose up` 会占用当前终端并打印日志；按 `Ctrl+C` 可停止。  
   若想后台运行：`docker-compose up -d`，在 Docker Desktop 的 **Containers** 里可看到所有容器。

5. **在 Docker Desktop 里查看**  
   - **Containers**：能看到 master、worker1、worker2、history、metastore 等。  
   - **Logs**：点某个容器可看日志。  
   - 本机浏览器可访问：NameNode http://localhost:9870、ResourceManager http://localhost:8088、Spark Master http://localhost:8080 等（见主 README）。

---

## 如何确认 Docker 集群是否启动成功

1. **Docker Desktop → Containers**  
   应看到约 **5 个运行中的容器**：`metastore`、`master`、`worker1`、`worker2`、`history`，状态为 running（绿色）。

2. **终端里看容器列表**  
   ```bash
   docker ps
   ```
   同样应列出上述 5 个容器，STATUS 为 `Up`。

3. **用浏览器打开管理页**  
   在浏览器访问以下地址，能打开页面即说明对应服务已起来：  
   - **Hadoop NameNode**：http://localhost:9870  
   - **YARN ResourceManager**：http://localhost:8088  
   - **Spark Master**：http://localhost:8080  

   若这些页面能正常打开，说明集群已成功启动。

---

## 集群启动后，下一步做什么？

按你的目标二选一（或先 A 再 B）：

### 路径 A：在集群里跑实验（复现/收集数据）

1. **进 master 容器**  
   ```bash
   docker exec -it ucla_capstone-master-1 bash
   ```
   （容器名可能带项目前缀，可用 `docker ps` 看 master 的 NAME。）

2. **把数据放进 HDFS**  
   在**本机**准备好 CSV（如 5mb/50mb/500mb 数据），用 `docker cp` 拷进容器，再在容器内执行：  
   ```bash
   hdfs dfs -mkdir -p /data
   hdfs dfs -put /path/in/container/5mb.csv /data/
   ```
   若有现成分区脚本，按 [README 的 Data partitioning in Hive](../README.md) 做。

3. **跑任务**  
   在 master 容器里运行 `5mb/`、`50mb/`、`500mb/` 下对应脚本（如 `python 5mb/hive-task1.py`、`python 5mb/no-hive-task1_4.py` 等），跑完所有组合。

4. **收集结果**  
   从 YARN (http://localhost:8088) 或 Spark History (http://localhost:18080) 记下各任务 runtime；用 `docker stats` 或 `stats_collection_tools` 里的脚本采集 CPU/内存，得到 `*_results.csv` 和 `*_stats/*.csv`。

5. **更新汇总表**  
   在本机项目根目录：  
   ```bash
   python3 advisor/scripts/build_summary.py
   ```

详细实验设计与命名规则见 [docs/EXPERIMENT_DESIGN.md](EXPERIMENT_DESIGN.md)。

### 路径 B：继续做 Capstone（不依赖集群在跑）

- **直接用现有数据跑 Advisor**（本机即可）：  
  ```bash
  python3 advisor/scripts/build_summary.py
  python3 advisor/advisor.py -s 50mb -q join
  ```
- **做 Week 3**：写评估脚本（推荐 vs 真实最优一致率）、做 1～2 张报告用图。  
- **做 Week 4**：写 `docs/ADVISOR_DESIGN.md`、更新 README、可选 ML 或“未来工作”。

当前实验数据已够 Advisor 使用，**不做新实验也可以先推进路径 B**。

---

## 快速自检（只跑 Advisor 时）

只跑 Advisor 时，若看到类似输出即表示启动成功：

```
Recommendation:
  strategy:        spark_repartition
  num_partitions:  4
  reason:         lowest runtime in 50mb join experiments
```

若报错 `FileNotFoundError: ... experiment_summary.csv`，先执行一次：

```bash
python3 advisor/scripts/build_summary.py
```

再重新运行 `advisor/advisor.py`。
