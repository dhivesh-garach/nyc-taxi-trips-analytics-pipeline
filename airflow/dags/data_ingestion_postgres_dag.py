import os
from datetime import datetime
from airflow import DAG
from ingest_data_postgres_task import ingest_data
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

AIRFLOW_HOME = os.getenv('AIRFLOW_HOME')

PG_HOST = os.getenv('PG_HOST')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_PORT = os.getenv('PG_PORT')
PG_DATABASE = os.getenv('PG_DATABASE')

FILE_DATE = "{{execution_date.strftime('%Y-%m')}}"
SOURCE_URL_PREFIX = 'https://d37ci6vzurychx.cloudfront.net/trip-data'
SOURCE_FILE_NAME = f'yellow_tripdata_{FILE_DATE}.parquet'
OUTPUT_FILE_PATH = f'{AIRFLOW_HOME}/yellow_taxi_{FILE_DATE}.parquet'


data_ingestion_postgres_worflow = DAG (
    dag_id= "data_ingestion_postgres_dag",
    schedule_interval="0 6 2 * *",
    start_date=datetime(2024, 1, 1)
)

with data_ingestion_postgres_worflow:

    download_source_data_task = BashOperator(
        task_id='download_source_data',
        bash_command=f'curl -sSL {SOURCE_URL_PREFIX}/{SOURCE_FILE_NAME} > {OUTPUT_FILE_PATH}'
    )

    ingest_to_postgres_task = PythonOperator(
        task_id='ingest_data_to_postgres',
        python_callable=ingest_data,
        op_kwargs = dict(
            user = PG_USER,
            password = PG_PASSWORD,
            host = PG_HOST,
            port = PG_PORT,
            database = PG_DATABASE,
            table = 'yellow_taxi_{{execution_date.strftime(\'%Y_%m\')}}',
            source_file = OUTPUT_FILE_PATH
        )   
    )

    download_source_data_task >> ingest_to_postgres_task