FROM apache/airflow:2.10.5

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends postgresql-client \
 && rm -rf /var/lib/apt/lists/*

USER airflow
COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /home/airflow/venv \
 && /home/airflow/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt
