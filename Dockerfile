FROM python:latest

RUN pip install pandas

WORKDIR /app

COPY transformations.py transformations.py

ENTRYPOINT [ "bash" ]