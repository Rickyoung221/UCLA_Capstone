import findspark
findspark.init('/opt/spark')
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, TimestampType, DoubleType

spark = SparkSession.builder \
    .appName("TestWithoutHiveNYC1") \
    .config("spark.sql.catalogImplementation", "in-memory") \
    .getOrCreate()

# Define the explicit schema
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

# Read CSV files from HDFS using the explicit schema
df = spark.read.option("header", "true") \
    .schema(schema) \
    .csv("hdfs://master:8020/data/5mb.csv")

# Repartition the DataFrame to a fixed number of partitions (e.g., 10)
df = df.repartition(10)

# Create a temporary view to run SQL queries on the repartitioned data
df.createOrReplaceTempView("temp")

# Example SQL query to aggregate trip count, average fare, and total revenue by RatecodeID, VendorID, and payment_type
# Another example SQL query with window functions
simple_query = """
SELECT 
  a.VendorID,
  a.RatecodeID,
  a.payment_type,
  a.tpep_pickup_datetime AS pickup_time_a,
  b.tpep_pickup_datetime AS pickup_time_b,
  a.total_amount AS total_amount_a,
  b.total_amount AS total_amount_b
FROM temp a
JOIN temp b
  ON a.VendorID = b.VendorID
  AND a.RatecodeID = b.RatecodeID
  AND a.payment_type = b.payment_type
  AND a.tpep_pickup_datetime < b.tpep_pickup_datetime
  AND b.tpep_pickup_datetime BETWEEN a.tpep_pickup_datetime 
       AND a.tpep_pickup_datetime + INTERVAL '10' MINUTE;

"""
spark.sql(simple_query).show(20)

print("Success")
spark.stop()
