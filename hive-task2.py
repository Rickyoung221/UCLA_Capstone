import findspark
findspark.init('/opt/spark')
from pyspark.sql import SparkSession

spark = SparkSession.builder \
        .appName("Test5MBT1") \
        .enableHiveSupport() \
        .getOrCreate()

# Run a more complex SQL query on the table
complex_query = """
SELECT 
  a.VendorID,
  a.RatecodeID,
  a.payment_type,
  a.tpep_pickup_datetime AS pickup_time_a,
  b.tpep_pickup_datetime AS pickup_time_b,
  a.total_amount AS total_amount_a,
  b.total_amount AS total_amount_b
FROM taxi_data_partitioned_csv_5mb a
JOIN taxi_data_partitioned_csv_5mb b
  ON a.VendorID = b.VendorID
  AND a.RatecodeID = b.RatecodeID
  AND a.payment_type = b.payment_type
  AND a.tpep_pickup_datetime < b.tpep_pickup_datetime
  AND b.tpep_pickup_datetime BETWEEN a.tpep_pickup_datetime 
       AND a.tpep_pickup_datetime + INTERVAL '10' MINUTE;
"""

df_complex = spark.sql(complex_query)
df_complex.show(5)

print("Success")
spark.stop()
