#!/usr/bin/bash
# Fix JAVA_HOME on platforms where path differs (e.g. arm64 = java-8-openjdk-arm64)
if [ ! -d "$JAVA_HOME" ]; then
  export JAVA_HOME=$(ls -d /usr/lib/jvm/java-8-openjdk-* 2>/dev/null | head -1)
fi

echo "Starting Hadoop data node..."
hdfs --daemon start datanode

echo "Starting Hadoop node manager..."
yarn --daemon start nodemanager

echo "Starting Spark slave node..."
spark-class org.apache.spark.deploy.worker.Worker "spark://master:7077"