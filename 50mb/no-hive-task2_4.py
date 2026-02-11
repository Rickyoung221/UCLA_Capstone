import findspark
findspark.init('/opt/spark')
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, TimestampType, DoubleType, StringType

spark = SparkSession.builder \
    .appName("Test50MB_ExternalJoin_4") \
    .config("spark.sql.catalogImplementation", "in-memory") \
    .getOrCreate()

# Define the explicit schema for the taxi data CSV
taxi_schema = StructType([
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

# Read the taxi data CSV from HDFS using the explicit schema
df = spark.read.option("header", "true") \
    .schema(taxi_schema) \
    .csv("hdfs://master:8020/data/50mb.csv")

# Repartition the DataFrame (e.g., 4 partitions)
df = df.repartition(4)

# Create a temporary view for the taxi data
df.createOrReplaceTempView("temp")

# Define an explicit schema for the taxi zone lookup CSV.
# LocationID is an integer and the rest are strings (including the new service_zone column).
zone_schema = StructType([
    StructField("LocationID", IntegerType(), True),
    StructField("Zone", StringType(), True),
    StructField("Borough", StringType(), True),
    StructField("service_zone", StringType(), True)
])

# Read the taxi zone lookup CSV from HDFS using the explicit schema
zone_df = spark.read.option("header", "true") \
    .schema(zone_schema) \
    .csv("hdfs://master:8020/data/taxi+_zone_lookup.csv")

# Create a temporary view for the zone lookup data
zone_df.createOrReplaceTempView("zone_lookup")

# Run a simple join query: join taxi data with zone lookup on PULocationID = LocationID
join_query = """
SELECT 
  t.VendorID,
  t.RatecodeID,
  t.payment_type,
  t.tpep_pickup_datetime,
  t.total_amount,
  z.Zone AS pickup_zone,
  z.Borough AS pickup_borough,
  z.service_zone
FROM temp t
JOIN zone_lookup z
  ON t.PULocationID = z.LocationID
"""

df_join = spark.sql(join_query)
total_rows = df_join.count()
df_join.show(5)

print("Success")
print("Total rows", total_rows)
spark.stop()
