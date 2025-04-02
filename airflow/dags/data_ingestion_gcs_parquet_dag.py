import os

from airflow import DAG
from datetime import datetime
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from google.cloud import storage
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")

file_date = "{{execution_date.strftime('%Y-%m')}}"
dataset_file = f"yellow_tripdata_{file_date}.parquet"
dataset_url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{dataset_file}"
path_to_local_home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
parquet_file = f"yellow_tripdata_{file_date}.parquet"
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'taxi_rides_dataset')


# NOTE: takes 20 mins, at an upload speed of 800kbps. Faster if your internet has a better upload speed
def upload_to_gcs(bucket, object_name, local_file):
    """
    Ref: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python
    :param bucket: GCS bucket name
    :param object_name: target path & file-name
    :param local_file: source path & file-name
    :return:
    """
    # WORKAROUND to prevent timeout for files > 25 MB.
    # (Ref: https://github.com/googleapis/python-storage/issues/74)
    storage.blob._MAX_MULTIPART_SIZE = 5 * 1024 * 1024  # 25 MB
    storage.blob._DEFAULT_CHUNKSIZE = 5 * 1024 * 1024  # 25 MB
    # End of Workaround

    client = storage.Client()
    bucket = client.bucket(bucket)

    blob = bucket.blob(object_name)
    blob.upload_from_filename(local_file)

    print("The dataset uploaded successfully to GCS bucket!")


# NOTE: DAG declaration - using a Context Manager (an implicit way)
with DAG(
    dag_id="data_ingestion_gcs_parquet_dag",
    start_date= datetime(2024, 1, 1),
    end_date= datetime(2024, 12, 31),
    schedule_interval="0 6 2 * *",
    catchup=True,
    max_active_runs=3,
    tags=['gcp_pipeline'],
) as dag:

    download_dataset_task = BashOperator(
        task_id="download_dataset_task",
        bash_command= f"""
        curl -sSL {dataset_url} > {path_to_local_home}/{parquet_file} &&
        echo "Source dataset downloaded successfully!"
        """
    )

    local_to_gcs_upload_task = PythonOperator(
        task_id="local_to_gcs_task",
        python_callable=upload_to_gcs,
        op_kwargs={
            "bucket": BUCKET,
            "object_name": f"raw/{parquet_file}",
            "local_file": f"{path_to_local_home}/{parquet_file}",
        },
    )

    bigquery_external_table_task = BigQueryCreateExternalTableOperator(
        task_id="bigquery_external_table_task",
        table_resource={
            "tableReference": {
                "projectId": PROJECT_ID,
                "datasetId": BIGQUERY_DATASET,
                "tableId": f"yellow_taxi_external_{file_date}",
            },
            "externalDataConfiguration": {
                "sourceFormat": "PARQUET",
                "sourceUris": [f"gs://{BUCKET}/raw/{parquet_file}"],
            },
        },
    )

    download_dataset_task >> local_to_gcs_upload_task >> bigquery_external_table_task