import findspark
findspark.init('/opt/spark')
from pyspark.sql import SparkSession

spark = SparkSession.builder \
        .appName("Test5MB_Window") \
        .enableHiveSupport() \
        .getOrCreate()

# Run a more complex SQL query on the table
complex_query = """
SELECT 
  ratecodeid,
  vendorid,
  payment_type,
  tpep_pickup_datetime,
  fare_amount,
  ROW_NUMBER() OVER (
    PARTITION BY vendorid, ratecodeid, payment_type 
    ORDER BY tpep_pickup_datetime
  ) AS trip_rank,
  SUM(fare_amount) OVER (
    PARTITION BY vendorid, ratecodeid, payment_type 
    ORDER BY tpep_pickup_datetime 
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS running_total_fare
From taxi_data_partitioned_csv_5mb;
"""

df_complex = spark.sql(complex_query)
total_rows = df_complex.count()
df_complex.show(5)

print("Success")
print("Total rows", total_rows)
spark.stop()
