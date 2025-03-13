#!/usr/bin/env python
# coding: utf-8 

import os
import pyarrow.parquet as pq
import argparse
import pandas as pd
from sqlalchemy import create_engine

def main(params):

    user = params.user
    password = params.password
    host = params.host
    port = params.port
    database = params.db
    table = params.table
    url = params.url  

    source_name = 'trips.parquet'

    #Downloading and storing the source data file
    os.system(f'wget -nc {url} -O {source_name}')

    #Reading the parquet file
    trips_parquet = pq.ParquetFile(source_name)
    
    #Exploratory Analysis of the first 100 rows of data (by creating a batch and reading 100 rows from 1st batch)
    batch_iter_temp = trips_parquet.iter_batches(batch_size=100)
    df_temp = next(batch_iter_temp).to_pandas()
    print(df_temp.head())

    print(df_temp.info())

    #Converting the data type of the date fields which are text type to datetime data type
    #df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    #df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])

    #Getting the schema SQL query to create a table of similar data types to target database
    print(pd.io.sql.get_schema(df_temp, f'{table}')) # type: ignore

    #Connecting to the target database
    postgres_engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    postgres_engine.connect()

    #Getting schema/table creation query compatible to postgresql database
    print(pd.io.sql.get_schema(df_temp, f'{table}', con=postgres_engine)) # type: ignore

    #Reading the data in pandas dataframe in batches of 0.2M rows
    batch_iter = trips_parquet.iter_batches(batch_size=200000)
    df = next(batch_iter).to_pandas()

    #Creating a table in Postgres DB using the schema created using pd.io in previous steps
    df.head(n=0).to_sql(name=table, con=postgres_engine, if_exists='replace', index=False)

    #Appending the 1st chunk of 200,000 rows within the table "yellow_taxi_data"
    df.to_sql(name=table, con=postgres_engine, if_exists='append', index=False)

    #Appending the further remaining rows of data in chunks to the "yellow_taxi_data" table in Postgres DB
    from time import time

    while True:
        
        try:
            t_start = time()

            df = next(batch_iter).to_pandas(split_blocks=True, self_destruct=True)

            #df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
            #df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])

            df.to_sql(name=table, con=postgres_engine, if_exists='append', index=False)

            t_end = time()

            print('Another chunk inserted..., time taken %.3f' % (t_end - t_start))
        
        except StopIteration:
            
            print("All chunks processed")
            break

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Ingest Parquet file data to Postgres DB')

    parser.add_argument('--user', help= 'username for the postgres server')
    parser.add_argument('--password', help= 'password for the postgres server')
    parser.add_argument('--host', help= 'host of the postgres server')
    parser.add_argument('--port', help= 'port of the postgres server')
    parser.add_argument('--db', help= 'database name for the postgres server')
    parser.add_argument('--table', help= 'table name where you want to write the results of Schema to')
    parser.add_argument('--url', help= 'url of the source data file')

    args = parser.parse_args()

    main(args)