import findspark
findspark.init('/opt/spark')
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, TimestampType, DoubleType

spark = SparkSession.builder \
    .appName("Test50MB_Aggregate_32") \
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
    .csv("hdfs://master:8020/data/50mb.csv")

# Repartition the DataFrame to a fixed number of partitions (e.g., 10)
df = df.repartition(32)

# Create a temporary view to run SQL queries on the repartitioned data
df.createOrReplaceTempView("temp")

# Example SQL query to aggregate trip count, average fare, and total revenue by RatecodeID, VendorID, and payment_type
simple_query = """
SELECT 
  RatecodeID,
  VendorID,
  payment_type,
  COUNT(*) AS trip_count,
  AVG(fare_amount) AS avg_fare,
  SUM(total_amount) AS total_revenue
FROM temp
GROUP BY RatecodeID, VendorID, payment_type;

"""
df_complex = spark.sql(simple_query)
total_rows = df_complex.count()
df_complex.show(5)

print("Success")
print("Total rows", total_rows)
spark.stop()
