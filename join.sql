SELECT 
  a.VendorID,
  a.RatecodeID,
  a.payment_type,
  a.tpep_pickup_datetime AS pickup_time_a,
  b.tpep_pickup_datetime AS pickup_time_b,
  a.total_amount AS total_amount_a,
  b.total_amount AS total_amount_b
FROM taxi_data_partitioned_csv a
JOIN taxi_data_partitioned_csv b
  ON a.VendorID = b.VendorID
  AND a.RatecodeID = b.RatecodeID
  AND a.payment_type = b.payment_type
  AND a.tpep_pickup_datetime < b.tpep_pickup_datetime
  AND b.tpep_pickup_datetime BETWEEN a.tpep_pickup_datetime 
       AND a.tpep_pickup_datetime + INTERVAL '10' MINUTE;
