FROM python:latest

RUN pip install pandas

ENTRYPOINT [ "bash" ]