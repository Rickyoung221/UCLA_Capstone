set hive.execution.engine=spark;
CREATE EXTERNAL TABLE IF NOT EXISTS taxi_data_partitioned (
  lpep_pickup_datetime   TIMESTAMP,
  lpep_dropoff_datetime  TIMESTAMP,
  store_and_fwd_flag     STRING,
  PULocationID           INT,
  DOLocationID           INT,
  passenger_count        FLOAT,
  trip_distance          FLOAT,
  fare_amount            FLOAT,
  extra                  FLOAT,
  mta_tax                FLOAT,
  tip_amount             FLOAT,
  tolls_amount           FLOAT,
  ehail_fee              STRING,
  improvement_surcharge  FLOAT,
  total_amount           FLOAT,
  trip_type              INT,
  congestion_surcharge   FLOAT
)
PARTITIONED BY (
  RatecodeID  INT,
  VendorID    INT,
  payment_type INT
)
STORED AS PARQUET
LOCATION '/data/nyc_partition/';
