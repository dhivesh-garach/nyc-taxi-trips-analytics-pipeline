from time import time
import pyarrow.parquet as pq
import pandas as pd
from sqlalchemy import create_engine

def ingest_data(user, password, host, port, database, table, source_file):
    print(table, source_file) 

    #Connecting to the target database
    postgres_engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    postgres_engine.connect()

    print('Connection to database established!')
    #Reading the parquet file
    trips_parquet = pq.ParquetFile(source_file)
    
    #Exploratory Analysis of the first 100 rows of data (by creating a batch and reading 100 rows from 1st batch)
    batch_iter_temp = trips_parquet.iter_batches(batch_size=100)
    df_temp = next(batch_iter_temp).to_pandas()

    print(df_temp.info())

    #Getting the schema SQL query to create a table of similar data types to target database
    print(pd.io.sql.get_schema(df_temp, f'{table}')) # type: ignore

    #Getting schema/table creation query compatible to postgresql database
    print(pd.io.sql.get_schema(df_temp, f'{table}', con=postgres_engine)) # type: ignore

    #Reading the data in pandas dataframe in batches of 0.2M rows
    batch_iter = trips_parquet.iter_batches(batch_size=200000)
    df = next(batch_iter).to_pandas()

    #Creating a table in Postgres DB using the schema created using pd.io in previous steps
    df.head(n=0).to_sql(name=table, con=postgres_engine, if_exists='replace', index=False)
    
    t_start = time()
    #Appending the 1st chunk of 200,000 rows within the table "yellow_taxi_data"
    df.to_sql(name=table, con=postgres_engine, if_exists='append', index=False)

    t_end = time()

    print('Inserted first chunk, time taken %.3f' % (t_end - t_start))

    #Appending further remaining records in chunks to the "yellow_taxi_data" table in Postgres DB

    while True:
        
        try:
            t_start = time()

            df = next(batch_iter).to_pandas(split_blocks=True, self_destruct=True)

            #df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
            #df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])

            df.to_sql(name=table, con=postgres_engine, if_exists='append', index=False)

            t_end = time()

            print('Another chunk inserted, time taken %.3f' % (t_end - t_start))
        
        except StopIteration:
            
            print("All chunks processed")
            break