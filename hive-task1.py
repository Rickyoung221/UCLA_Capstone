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
  RatecodeID,
  VendorID,
  payment_type,
  COUNT(*) AS trip_count,
  AVG(fare_amount) AS avg_fare,
  SUM(total_amount) AS total_revenue
FROM taxi_data_partitioned_csv_5mb
GROUP BY RatecodeID, VendorID, payment_type;
"""

df_complex = spark.sql(complex_query)
df_complex.show(5)

print("Success")
spark.stop()
