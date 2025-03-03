#docker config file
FROM python:latest

RUN apt-get install wget
RUN pip install pandas numpy sqlalchemy pyarrow psycopg2 argparse

WORKDIR /app

COPY ingest_data_script.py ingest_data_script.py

ENTRYPOINT [ "python", "ingest_data_script.py" ]