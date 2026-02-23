# 如何跑实验（补 500mb Join 16/32 等）

用于在 Docker 集群里跑任务、从 YARN 收集 runtime、更新 results 和汇总表。

---

## 前提

- Docker、Docker Compose 已安装，集群已构建并启动（见 [GETTING_STARTED.md](GETTING_STARTED.md)）。
- HDFS 上已有对应数据（如 `/data/500mb.csv`），且路径与脚本中一致（如 `hdfs://master:8020/data/500mb.csv`）。

---

## 步骤一：启动集群

```bash
cd /Users/rickyang/Documents/GitHub/UCLA_Capstone
docker-compose up -d
```

等所有容器 Running 后，用浏览器打开 http://localhost:8088（YARN）确认正常。

---

## 步骤二：把脚本和数据拷进 master 容器

（若项目已通过 volume 挂载到容器内，可跳过拷贝脚本，只保证数据在 HDFS。）

```bash
# 查看 master 容器名（常见为 xxx-master-1）
docker ps

# 把 500mb 目录和依赖拷进容器（按你的容器名改）
docker cp 500mb <容器名>:/opt/
docker cp partition <容器名>:/opt/
# 若脚本里用 findspark，确保容器内已有；一般镜像里已带
```

若 HDFS 上还没有 500mb 数据，需要先把本机 500mb.csv 拷进容器并 put 到 HDFS：

```bash
docker cp /path/to/500mb.csv <容器名>:/tmp/
docker exec -it <容器名> bash
# 在容器内：
hdfs dfs -mkdir -p /data
hdfs dfs -put /tmp/500mb.csv /data/
exit
```

---

## 步骤三：在 master 容器里跑任务

以补 **500mb Join Spark-16 / Spark-32** 为例：

```bash
docker exec -it <容器名> bash
cd /opt/500mb   # 或你拷入的路径

# 跑 500mb Join 16 分区（应用名会显示为 Test500MB_ExternalJoin_16）
spark-submit --master yarn no-hive-task2_16.py

# 跑完后同样跑 32 分区
spark-submit --master yarn no-hive-task2_32.py

exit
```

跑的时候可在 http://localhost:8088 看应用列表，记下 **Application ID** 和 **运行时间（秒）**。

---

## 步骤四：从 YARN / Spark History 记下 runtime

- **YARN**：http://localhost:8088 → 点进刚跑完的 Application → 看 **Finished** 时间与 **Start** 时间，差即为 runtime（秒）；或看 Spark UI 里的 Duration。
- **Spark History**：http://localhost:18080 → 找到对应应用（如 Test500MB_ExternalJoin_16）→ 记下 duration（秒）。

把两个数记下来，例如：
- Test500MB_ExternalJoin_16 → **19.7** 秒  
- Test500MB_ExternalJoin_32 → **19.9** 秒  

（若你跑出来的数字不同，以实际为准。）

---

## 步骤五：更新 500mb_results.csv

在本机用编辑器打开 `stats_collection_tools/500mb_results.csv`，在表头一致的前提下新增两行（id 可写占位，name 和 runtime_seconds 必须正确）：

```csv
id,name,start_time,launch_time,finish_time,runtime_seconds
...,Test500MB_ExternalJoin_16,,,.,<你记下的16的秒数>
...,Test500MB_ExternalJoin_32,,,.,<你记下的32的秒数>
```

保存。  
（`build_summary.py` 已支持 **ExternalJoin** 名字，会当作 Join 汇总。）

---

## 步骤六：重新生成汇总表和图

在本机项目根目录：

```bash
python3 advisor/scripts/build_summary.py
python3 advisor/scripts/plot_runtime.py
```

再打开 `advisor/experiment_summary.csv` 和 `advisor/scripts/runtime_comparison.png`，应能看到 500mb Join 的 Spark-16、Spark-32 数据与图中两根柱子。

---

## 其他规模 / 查询类型

- **脚本位置**：`5mb/`、`50mb/`、`500mb/` 下分别有 `hive-task1/2/3.py`（Hive）和 `no-hive-task1/2/3_4|16|32.py`（Spark 4/16/32）。task1=aggregate，task2=join，task3=window。
- **应用名**：若为 `Test*MB_Join_*` 或 `Test*MB_ExternalJoin_*`，汇总脚本都会识别为 join。
- **results 文件**：对应写入 `stats_collection_tools/5mb_results.csv`、`50mb_results.csv`、`500mb_results.csv`，格式与现有行一致即可。

复现与命名规则详见 [EXPERIMENT_DESIGN.md](EXPERIMENT_DESIGN.md)。
