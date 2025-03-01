SELECT
	*
FROM
	TAXI_ZONE;

SELECT
	*
FROM
	YELLOW_TAXI_TRIPS
LIMIT
	100;

--Joining the yellow taxi trips table with taxi zone table to identify and analyze pick up / drop off locations.
WITH
	YELLOW_TAXI_COMB AS (
		SELECT
			Y.*,
			PL."Borough" AS "PUBorough",
			PL."Zone" AS "PUZone",
			DL."Borough" AS "DOBorough",
			DL."Zone" AS "DOZone",
			PL."service_zone"
		FROM
			YELLOW_TAXI_TRIPS Y
			LEFT JOIN TAXI_ZONE PL ON Y."PULocationID" = PL."LocationID"
			LEFT JOIN TAXI_ZONE DL ON Y."DOLocationID" = DL."LocationID"
	);

SELECT
	*
FROM
	YELLOW_TAXI_COMB
LIMIT
	100;

-- Creating a View for joining the data of yellow taxi table and taxi zones table for analysis.
CREATE OR REPLACE VIEW YELLOW_TAXI_ZONE_VIEW AS (
	SELECT
		Y.*,
		PL."Borough" AS "PUBorough",
		PL."Zone" AS "PUZone",
		DL."Borough" AS "DOBorough",
		DL."Zone" AS "DOZone",
		PL."service_zone"
	FROM
		YELLOW_TAXI_TRIPS Y
		LEFT JOIN TAXI_ZONE PL ON Y."PULocationID" = PL."LocationID"
		LEFT JOIN TAXI_ZONE DL ON Y."DOLocationID" = DL."LocationID"
);

--Reviewing the records from newly created view above.
SELECT
	*
FROM
	YELLOW_TAXI_ZONE_VIEW
LIMIT
	100;

--Optimizing the query performance of the yellow_taxi_zone_view by applying various techniques (as it processes the join everytime the view is called)

CREATE INDEX idx_yellow_drop_dt ON yellow_taxi_trips ((tpep_dropoff_datetime::date));
CREATE INDEX yellow_drop_loc_index ON yellow_taxi_trips ("DOLocationID");
CREATE INDEX yellow_pick_loc_index ON yellow_taxi_trips ("PULocationID");
CREATE INDEX taxi_loc_index ON taxi_zone ("LocationID");

VACUUM ANALYSE yellow_taxi_trips;
VACUUM ANALYSE taxi_zone;

--checking the database current memory and connections config parameters value
SHOW work_mem;
SHOW maintenance_work_mem;
SHOW max_connections;


-- Analyzing number of drop offs by date and drop off zone to understand the trend of the taxi bookings during the month.
SELECT
	(TPEP_DROPOFF_DATETIME::DATE) AS day_of_month,
	"DOLocationID",
	COUNT(1) as num_of_drops,
	MAX(total_amount) as highest_fee_of_day,
	MAX(passenger_count) as highest_passenger_count_of_day
FROM
	YELLOW_TAXI_ZONE_VIEW
GROUP BY
	1, 2
ORDER BY
	day_of_month ASC,
	"DOLocationID" ASC;

--Creating a materialized view for the joined data from the view from previous steps, so the table is not processed everytime we need the data thus reducing the query time for analysis on this table.
CREATE MATERIALIZED VIEW yellow_taxi_consolidated AS (
SELECT * FROM yellow_taxi_zone_view
);

SELECT * FROM yellow_taxi_consolidated
LIMIT 100;

--Applying query performance enhancement techniques on the materialized view to improve the query processing time.

CREATE INDEX idx_ytc_pickup_date ON yellow_taxi_consolidated ((tpep_pickup_datetime::date));
CREATE INDEX idx_ytc_dropoff_date ON yellow_taxi_consolidated ((tpep_dropoff_datetime::date));
CREATE INDEX idx_ytc_pickup_loc ON yellow_taxi_consolidated ("PULocationID");
CREATE INDEX idx_ytc_dropoff_loc ON yellow_taxi_consolidated ("DOLocationID");
CREATE INDEX idx_ytc_pickup_district ON yellow_taxi_consolidated ("PUBorough");
CREATE INDEX idx_ytc_dropoff_district ON yellow_taxi_consolidated ("DOBorough");

VACUUM ANALYSE yellow_taxi_consolidated;

--Finding the unique pick up locations of the yellow taxi trips.
SELECT DISTINCT
	("PUBorough")
FROM
	YELLOW_TAXI_CONSOLIDATED;
	
--Analyzing the fare revenue in a day by pick up location.
SELECT
	(TPEP_PICKUP_DATETIME::DATE) AS "date",
	"PUBorough",
	SUM(TOTAL_AMOUNT) AS TOTAL
FROM
	YELLOW_TAXI_CONSOLIDATED
GROUP BY
	1, 2
ORDER BY
	TOTAL DESC;