SELECT 
  RatecodeID,
  VendorID,
  payment_type,
  COUNT(*) AS trip_count,
  AVG(fare_amount) AS avg_fare,
  SUM(total_amount) AS total_revenue
FROM taxi_data_partitioned_csv_5mb
GROUP BY RatecodeID, VendorID, payment_type;
