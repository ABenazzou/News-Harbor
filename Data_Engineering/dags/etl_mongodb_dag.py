from airflow import DAG
from airflow.decorators import task
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from datetime import datetime, timedelta
import logging    
from pymongo import MongoClient
import boto3
import configparser
import os

@task(task_id="identify_delta_load")
def identify_delta_load():
    
    
    def get_available_data(s3_client):
        
        result = set()
        s3_bucket = s3_client.list_objects(Bucket=s3_bucket_name, Prefix="clean-data/")
        
        if "Contents" not in s3_bucket: return result
        
        clean_files = s3_bucket["Contents"]
        for file in clean_files:
            if ".csv" in file["Key"]: result.add(file["Key"])
        
        return result
    
        
    parser = configparser.ConfigParser()
    parser.read(os.path.join(os.path.dirname(__file__), '../config/config.conf'))

    # AWS
    aws_access_key = parser.get('aws', 'aws_access_key')
    aws_secret_key = parser.get('aws', 'aws_secret_key')
    s3_bucket_name = parser.get('aws', 's3_bucket_name')
    s3_client = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    
    # MONGO DB
    host_address = parser.get('mongodb', 'host_address')
    port = parser.get('mongodb', 'port')
    username = parser.get('mongodb', 'username')
    password = parser.get('mongodb', 'password')
    tls = parser.get('mongodb', 'tlsClientCertificate')
    tlsCA = parser.get('mongodb', 'tlsCA')
    
    connection_string = f"mongodb://{username}:{password.replace('AT', '%40')}@{host_address}:{port}/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.1.1"
    client = MongoClient(connection_string, tls=True, tlsCertificateKeyFile=tls, tlsCAFile=tlsCA, tlsAllowInvalidCertificates=True)
    news_harbor_db = client["News-Harbor"]
    imported_files_collection = news_harbor_db["imported-files"]
    
    available_files = get_available_data(s3_client)
    
    files_to_import = []
    
    for file in available_files:
        
        is_already_imported = imported_files_collection.find_one({'file_name': file})
        
        if is_already_imported: continue
        
        files_to_import.append(file)
    
    files_to_import.sort(key=lambda filename: filename.split("BBC_DATA_")[-1])
    return files_to_import
        

@task(task_id="transform_and_load_data")
def extract_transform_and_load_data(**kwargs):
    
    import pandas as pd
    from io import StringIO
    
    
    def extract_data(s3_client, file_name):
        
        obj = s3_client.get_object(Bucket=s3_bucket_name, Key=file_name)
        csv_string = StringIO(obj['Body'].read().decode('utf-8'))
        df = pd.read_csv(csv_string)
        return df
    
    
    def transform_data(csv_dataframe):
        
        df['uri'] = df['uri'].astype(str)
        df['title'] = df['title'].astype(str)
        df['subtitle'] = df['subtitle'].astype(str)
        df['date_posted'] = pd.to_datetime(df['date_posted'], format='%Y-%m-%d')
        df['full_text'] = df['full_text'].astype(str)
        df['topics'] = df['topics'].apply(lambda record: eval(str(record)))
        df['images'] = df['images'].apply(lambda record: eval(str(record)))
        df['authors'] = df['authors'].apply(lambda record: eval(str(record)))
        df['category'] = df['category'].astype(str)
        df['subcategory'] = df['subcategory'].astype(str)
        
        data = df.to_dict('records')
        
        schemaless_data = []
        for record in data:
            schemaless_record = {}
            for key, value in record.items():
                if type(value) == list and "" in value:
                    value = [item for item in value if item != ""]
                    
                if type(value) == str and value in ("N/A", "nan") or type(value) == list and "N/A" in value:
                    continue
                else:
                    schemaless_record[key] = value
                    
            schemaless_data.append(schemaless_record)
                    
        return schemaless_data
        
    
    def load_data(data, collection):
        
        logging.info("Loading data")
        
        for record in data:    
            collection.find_one_and_replace({"uri": record["uri"]}, record, upsert=True)
    

    task_instance = kwargs['ti']
    files_to_import = task_instance.xcom_pull(task_ids="identify_delta_load")
    
    parser = configparser.ConfigParser()
    parser.read(os.path.join(os.path.dirname(__file__), '../config/config.conf'))

    # AWS
    aws_access_key = parser.get('aws', 'aws_access_key')
    aws_secret_key = parser.get('aws', 'aws_secret_key')
    s3_bucket_name = parser.get('aws', 's3_bucket_name')
    s3_client = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    
    host_address = parser.get('mongodb', 'host_address')
    port = parser.get('mongodb', 'port')
    username = parser.get('mongodb', 'username')
    password = parser.get('mongodb', 'password')
    tls = parser.get('mongodb', 'tlsClientCertificate')
    tlsCA = parser.get('mongodb', 'tlsCA')

    connection_string = f"mongodb://{username}:{password.replace('AT', '%40')}@{host_address}:{port}/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.1.1"
    client = MongoClient(connection_string, tls=True, tlsCertificateKeyFile=tls, tlsCAFile=tlsCA, tlsAllowInvalidCertificates=True)
    news_harbor_db = client["News-Harbor"]
    bbc_news_collection = news_harbor_db["bbc-articles"]
    imported_files_collection = news_harbor_db["imported-files"]
    
    for file in files_to_import:
        
        logging.info("Processsing file %s", file)
        
        df = extract_data(s3_client, file)
        transformed_df = transform_data(df)
        load_data(transformed_df, bbc_news_collection)
        
        # add file name to imported files in mongo db
        imported_files_collection.insert_one({
            "file_name": file
        })


default_args = {
    'owner': 'Adnane',
    'depends_on_past': False, # Previous Fails doesn't stop it from triggering
    'start_date': datetime(2024, 1, 9), # January 8th, 2024 
    'end_date': datetime(2024, 1, 12), # January 13th, 2024
    'email': ['adnanebenzo194@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
        dag_id='etl_s3_to_mongodb',
        default_args=default_args,
        schedule_interval='55 23 * * *', # after scrape runs
        tags=["Databases", "ETL", "MongoDB"] 
    ) as dag:
    
    wait_for_cleaning_task = ExternalTaskSensor(
        task_id="wait_cleaning_sensor",
        external_dag_id='clean_data_daily',
        external_task_id='upload_clean_data',
        allowed_states=['success'],
        check_existence=True,
        execution_delta=timedelta(minutes=25)
    )
    
    wait_for_cleaning_task >> identify_delta_load() >> extract_transform_and_load_data()
    