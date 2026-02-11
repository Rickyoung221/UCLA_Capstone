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