import findspark
findspark.init('/opt/spark')
from pyspark.sql import SparkSession

spark = SparkSession.builder \
        .appName("Test50MB_Aggregate") \
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
FROM taxi_data_partitioned_csv_50mb
GROUP BY RatecodeID, VendorID, payment_type;
"""

df_complex = spark.sql(complex_query)
total_rows = df_complex.count()
df_complex.show(5)

print("Success")
print("Total rows", total_rows)
spark.stop()
