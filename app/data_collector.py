import os
import pandas as pd
import snowflake.connector
import boto3
import shutil
from botocore.exceptions import ClientError

LOCAL_DATA_DIR = "csv_data"

class DataCollector:
    def __init__(self, query=None):
        self.dataset = None
        self.query = query
        self.dataset_location=None

    def transfer_local_data2folder(self, src_folder_path=None):
        try:
            if os.listdir(LOCAL_DATA_DIR) == []:
                # Moved local files to designated folder
                if src_folder_path:
                    shutil.copytree(src_folder_path, LOCAL_DATA_DIR)
            else:
                print("Files already in local dir: {}".format(os.listdir(LOCAL_DATA_DIR)))
            self.dataset_location = "local"
            return True

        except Exception as e:
            print(f"Error loading local data: {str(e)}")
            return False

    def pull_data_from_snowflake(self, connection_params, query):
        if self.query:
            query = self.query
        else:
            query = "SELECT * FROM your_table join your_table2 join your_table3"
        try:
            # Connect to Snowflake database
            conn = snowflake.connector.connect(**connection_params)
            # Execute SQL query
            cursor = conn.cursor()
            cursor.execute(query)
            # Fetch data into a DataFrame
            columns = [col[0] for col in cursor.description]
            data = cursor.fetchall()
            self.dataset = pd.DataFrame(data, columns=columns)
            return True
        except Exception as e:
            print(f"Error pulling data from Snowflake: {str(e)}")
            return False


    def pull_data_from_s3_bucket(self, bucket_name, object_key):
        try:
            # Initialize S3 client
            s3 = boto3.client('s3')
            # Download data from S3 bucket
            obj = s3.get_object(Bucket=bucket_name, Key=object_key)
            self.dataset = pd.read_csv(obj['Body'])
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == "NoSuchKey":
                print("The object does not exist.")
            else:
                print(f"Error pulling data from S3 Bucket: {str(e)}")
            return False


    def save_dataset_to_snowflake(self, connection_params, table_name):
        try:
            # Connect to Snowflake database
            conn = snowflake.connector.connect(**connection_params)
            # Write DataFrame to Snowflake table
            self.dataset.to_sql(table_name, conn, index=False, if_exists='replace')
            self.dataset_location = "snowflake"
            return True
        except Exception as e:
            print(f"Error saving dataset to Snowflake: {str(e)}")
            return False

    def save_dataset_to_s3_bucket(self, bucket_name, object_key):
        try:
            # Initialize S3 client
            s3 = boto3.client('s3')
            # Upload DataFrame to S3 bucket
            s3.put_object(Body=self.dataset.to_csv(index=False), Bucket=bucket_name, Key=object_key)
            self.dataset_location = "s3"
            return True
        except ClientError as e:
            print(f"Error saving dataset to S3 Bucket: {str(e)}")
            return False



if __name__ == "__main__":
    # Initialize DataCollector object
    collector = DataCollector()
    collector.transfer_local_data2folder()

    