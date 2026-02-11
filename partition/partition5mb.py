import findspark
findspark.init('/opt/spark')

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, TimestampType, DoubleType

spark = SparkSession.builder \
    .appName("ExplicitSchemaCSV5MB") \
    .enableHiveSupport() \
    .getOrCreate()

# Define the explicit schema without store_and_fwd_flag and congestion_surcharge
schema = StructType([
    StructField("VendorID", IntegerType(), True),
    StructField("tpep_pickup_datetime", TimestampType(), True),
    StructField("tpep_dropoff_datetime", TimestampType(), True),
    StructField("passenger_count", IntegerType(), True),
    StructField("trip_distance", DoubleType(), True),
    StructField("RatecodeID", IntegerType(), True),
    StructField("PULocationID", IntegerType(), True),
    StructField("DOLocationID", IntegerType(), True),
    StructField("payment_type", IntegerType(), True),
    StructField("fare_amount", DoubleType(), True),
    StructField("extra", DoubleType(), True),
    StructField("mta_tax", DoubleType(), True),
    StructField("tip_amount", DoubleType(), True),
    StructField("tolls_amount", DoubleType(), True),
    StructField("improvement_surcharge", DoubleType(), True),
    StructField("total_amount", DoubleType(), True)
])

# Read the CSV file with header and the explicit schema
df = spark.read.option("header", "true") \
    .schema(schema) \
    .csv("hdfs://master:8020/data/5mb.csv")

# Optionally, print the schema to verify the data types
df.printSchema()

# Write the data partitioned by RatecodeID, VendorID, and payment_type into a Hive table
df.write.partitionBy("RatecodeID", "VendorID", "payment_type") \
    .option("path", "hdfs://master:8020/data/nyc_taxi_partitioned_csv_5mb") \
    .mode("overwrite") \
    .saveAsTable("taxi_data_partitioned_csv_5mb")
