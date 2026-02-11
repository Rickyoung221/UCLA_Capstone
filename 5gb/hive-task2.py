import findspark
findspark.init('/opt/spark')
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, StringType

spark = SparkSession.builder \
    .appName("Test5GB_ExternalJoin") \
    .enableHiveSupport() \
    .getOrCreate()

# Define an explicit schema for the taxi zone lookup CSV
# Assume the CSV has columns: LocationID (int), Zone (string), Borough (string), service_zone (string)
zone_schema = StructType([
    StructField("LocationID", IntegerType(), True),
    StructField("Zone", StringType(), True),
    StructField("Borough", StringType(), True),
    StructField("service_zone", StringType(), True)
])

# Load the taxi zone lookup CSV from HDFS using the explicit schema
zone_lookup_df = spark.read.option("header", "true") \
    .schema(zone_schema) \
    .csv("hdfs://master:8020/data/taxi+_zone_lookup.csv")

# Register the DataFrames as temporary views for SQL querying
zone_lookup_df.createOrReplaceTempView("zone_lookup")

# Run a simple join query: join taxi data with zone lookup on PULocationID = LocationID
external_join_query = """
SELECT 
  t.VendorID,
  t.RatecodeID,
  t.payment_type,
  t.tpep_pickup_datetime,
  t.total_amount,
  z.Zone AS pickup_zone,
  z.Borough AS pickup_borough,
  z.service_zone
FROM taxi_data_partitioned_csv_5gb t
JOIN zone_lookup z
  ON t.PULocationID = z.LocationID
"""

df_join = spark.sql(external_join_query)
total_rows = df_join.count()
df_join.show(20)

print("Success")
print("Total rows", total_rows)
spark.stop()
