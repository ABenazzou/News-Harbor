FROM apache/airflow:2.8.0-python3.11
COPY requirements.txt /requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir --user -r /requirements.txt
