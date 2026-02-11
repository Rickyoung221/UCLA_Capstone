-- task.sql
CREATE TABLE IF NOT EXISTS my_task_table (
  id INT,
  name STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE;

LOAD DATA INPATH '/data/myfiles/name.csv' INTO TABLE my_task_table;

SELECT * FROM my_task_table;
