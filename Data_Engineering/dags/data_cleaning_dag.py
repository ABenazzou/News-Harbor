from airflow import DAG
from airflow.decorators import task
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from datetime import datetime, timedelta
import logging    


@task(task_id="get_uncleaned_raw_files")
def get_uncleaned_raw_files():
    
    
    def get_data_files_from_s3_folder(s3_client, s3_folder):
        
        result = set()
        s3_bucket = s3_client.list_objects(Bucket=s3_bucket_name, Prefix=s3_folder)
        
        if "Contents" not in s3_bucket: return result
        
        clean_files = s3_bucket["Contents"]
        for file in clean_files:
            if ".csv" in file["Key"]: result.add(file["Key"])
        
        return result

    
    import boto3
    import configparser
    import os
        
    parser = configparser.ConfigParser()
    parser.read(os.path.join(os.path.dirname(__file__), '../config/config.conf'))

    # AWS
    aws_access_key = parser.get('aws', 'aws_access_key')
    aws_secret_key = parser.get('aws', 'aws_secret_key')
    s3_bucket_name = parser.get('aws', 's3_bucket_name')
    s3_client = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    
    raw_files = get_data_files_from_s3_folder(s3_client, "raw-data/")
    clean_raw_files = get_data_files_from_s3_folder(s3_client, "clean-data/")
    
    unclean_files = set()
    for file in raw_files:
        mapping_file = file.replace("raw-data/", "clean-data/").replace(".csv", "_cleaned.csv")
        if mapping_file not in clean_raw_files: unclean_files.add(file)
    
    logging.info("Unclean Files: %s", unclean_files)
    
    return unclean_files


@task(task_id="clean_data")
def clean_data(**kwargs):

    
    def clean_authors(authors_record):
    
        if type(authors_record) != str: return ["N/A"] # empty records
        
        authors = []
        
        # i scraped multiple elements, author is always the first element only
        authors_record_list = eval(authors_record)[0]

        if authors_record_list.startswith('By '):
            authors_record_list = authors_record_list[3:]
            
        authors_record_list = authors_record_list.replace(", ", " & ").replace(" and ", " & ").split("&")

        for author in authors_record_list:
            author_fullname = ' '.join(author.split()[:2])
            
            if author_fullname in ("BBC Arabic", "BBC News"): continue # By X, BBC Arabic & Y, BBC News
            
            authors.append(author_fullname)
            
        return authors
        
    
    def clean_array(array_record):
        
        if type(array_record) != str: return ["N/A"] # empty records
        
        correct_array_record = eval(array_record)
        
        return correct_array_record
    
    
    def clean_subtitle(subtitle):
        
        if type(subtitle) != str or (subtitle in ("Facebook", "Instagram") or len(subtitle) < 3):
            
            return "N/A"
        
        return subtitle
        
        
    def clean_csv(obj_key, csv_file):
        
        import pandas as pd
        
        df = pd.read_csv(csv_file)
        logging.info("Read File %s", obj_key)
        
        # if we scraped the same article from 2 different menus, the 2nd menu is in topics
        df.drop_duplicates(subset=["id"], inplace=True)
        
        # no need to cast at this step as we are not loading to mongoDB yet for types
        
        # RENAME COLS
        df.rename(columns={'submenu': 'subcategory', 'menu': 'category'}, inplace=True)

        # id is clean and full
        # title is clean
        
        # subtitle does not exist sometimes but short words are bolded
        df['subtitle'] = df['subtitle'].apply(lambda record: clean_subtitle(record))
        
        # fulltext is clean, na to be filled
        
        # topics needs to be fixed => additional '' in the file
        df['topic'] = df['topics'].apply(lambda record: clean_array(record))
        
        # images needs to be fixed => additional '' in the file
        df['images'] = df['images'].apply(lambda record: clean_array(record))
        
        # menus and submenus are clean
        
        # clean authors
        df['authors'] = df['authors'].apply(lambda record: clean_authors(record))

        # drop irrelevant data
        # we dont need empty full-text because our goals is scraping articles
        df.dropna(subset=['full_text'], inplace=True)
        
        # fill empty records for everything else
        df.fillna(value="N/A", inplace=True)
        
        csv_name = obj_key.split("raw-data/")[1].replace(".csv", "_cleaned.csv")
        csv_path = f"./data/{csv_name}"
        
        df.to_csv(csv_path, index=False)
        
        return {
            "name": csv_name,
            "path": csv_path
        }
        
        
    import boto3
    import configparser
    import os
    from io import StringIO
    
    task_instance = kwargs['ti']
    unclean_files = task_instance.xcom_pull(task_ids="get_uncleaned_raw_files")
    
    parser = configparser.ConfigParser()
    parser.read(os.path.join(os.path.dirname(__file__), '../config/config.conf'))
    
    clean_files = []

    # AWS
    aws_access_key = parser.get('aws', 'aws_access_key')
    aws_secret_key = parser.get('aws', 'aws_secret_key')
    s3_bucket_name = parser.get('aws', 's3_bucket_name')
    
    s3_client = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    
    for file in unclean_files:
        obj = s3_client.get_object(Bucket=s3_bucket_name, Key=file)
        csv_string = StringIO(obj['Body'].read().decode('utf-8'))
        
        clean_file = clean_csv(file, csv_string) # cleans file and returns {name: name, path: path}
        clean_files.append(clean_file)
    
    return clean_files


@task(task_id="upload_clean_data")
def upload_clean_data(**kwargs):
    
    import boto3
    from boto3.s3.transfer import S3Transfer
    import configparser
    import os
    
    parser = configparser.ConfigParser()
    parser.read(os.path.join(os.path.dirname(__file__), '../config/config.conf'))

    # AWS
    aws_access_key = parser.get('aws', 'aws_access_key')
    aws_secret_key = parser.get('aws', 'aws_secret_key')
    s3_bucket_name = parser.get('aws', 's3_bucket_name')
    
    task_instance = kwargs['ti']
    clean_files = task_instance.xcom_pull(task_ids="clean_data")
    
    s3_client = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    
    # got paths and names, upload to s3
    for file in clean_files:
        file_name = file["name"]
        file_path = file["path"]
        
        transfer = S3Transfer(s3_client)
        
        transfer.upload_file(file_path, s3_bucket_name, f"clean-data/{file_name}", extra_args={'ServerSideEncryption': "AES256"})


default_args = {
    'owner': 'Adnane',
    'depends_on_past': False, # Previous Fails doesn't stop it from triggering
    'start_date': datetime(2024, 1, 8), # January 8th, 2024 
    'end_date': datetime(2024, 1, 13), # January 13th, 2024
    'email': ['adnanebenzo194@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
        dag_id='clean_data_daily',
        default_args=default_args,
        schedule_interval='30 23 * * *', # after scrape runs
        tags=["Data Cleaning", "Data Engineering"] 
    ) as dag:
    
    wait_for_scraping_task = ExternalTaskSensor(
        task_id="wait_scraping_sensor",
        external_dag_id='scrape_bbc_daily',
        external_task_id='upload_scraped_data',
        allowed_states=['success'],
        check_existence=True
        # execution_delta default is the same execution date as the current dag
    )
    
    wait_for_scraping_task >> get_uncleaned_raw_files() >> clean_data() >> upload_clean_data()
    