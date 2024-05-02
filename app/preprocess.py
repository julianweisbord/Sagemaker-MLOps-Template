import os
import pandas as pd
import snowflake.connector
import redis
import boto3
from botocore.exceptions import ClientError
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder


class Preprocess:
    def __init__(self):
        self.dataset = None

    def load_dataset(self, source, **kwargs):
        if source == "local":
            # file_path = kwargs.get('file_path')
           
            usage_df = pd.read_csv("csv_data/usage_actions.csv")
            # noncusts_df = pd.read_csv("csv_data/noncustomers.csv")
            custs_df = pd.read_csv("csv_data/customers.csv")
        
            # custs_leads_df = pd.concat([custs_df, noncusts_df])
            # data_df = pd.merge(usage_df, custs_leads_df, on="id") 
            data_df = pd.merge(usage_df, custs_df, on="id") 
            # Clean up merged dataframe files
            data_df = self.data_cleaning(df=data_df)

            # Remove all rows that have a when_timestamp after CLOSEDATE so they are not included
            data_df = data_df[data_df["WHEN_TIMESTAMP"] <= data_df["CLOSEDATE"]]

            # Calculate the difference between CLOSEDATE and WHEN_TIMESTAMP
            data_df['difference'] = (data_df['CLOSEDATE'] - data_df['WHEN_TIMESTAMP']).dt.days

            # Add "within30" column based on conditions
            data_df['converted_within30'] = (data_df['difference'] >= 0) & (data_df['difference'] <= 30)

            # Convert boolean values to integers (1 for True, 0 for False)
            data_df['converted_within30'] = data_df['converted_within30'].astype(int)

            # Drop the temporary "difference" column
            data_df.drop('difference', axis=1, inplace=True)

            # print("data_df['converted_within30'] ==0 ", data_df[data_df['converted_within30'] == 0])
            # print("data_df['converted_within30'] ==1: ", data_df[data_df['converted_within30'] == 1])


            # Add Converted Within 30 days Column
            self.dataset = data_df

        elif source == "snowflake":
            connection_params = kwargs.get('connection_params')
            query = kwargs.get('query')
            if connection_params and query:
                try:
                    conn = snowflake.connector.connect(**connection_params)
                    cursor = conn.cursor()
                    cursor.execute(query)
                    columns = [col[0] for col in cursor.description]
                    data = cursor.fetchall()
                    self.dataset = pd.DataFrame(data, columns=columns)
                except Exception as e:
                    print(f"Error loading dataset from Snowflake: {str(e)}")
            else:
                print("Error: Missing connection_params or query argument for Snowflake dataset.")
        elif source == "redis":
            host = kwargs.get('host')
            port = kwargs.get('port')
            db = kwargs.get('db')
            key = kwargs.get('key')
            if host and port and db and key:
                try:
                    r = redis.Redis(host=host, port=port, db=db)
                    data = r.get(key)
                    self.dataset = pd.read_json(data)
                except Exception as e:
                    print(f"Error loading dataset from Redis Cache: {str(e)}")
            else:
                print("Error: Missing host, port, db, or key argument for Redis dataset.")
        elif source == "s3":
            bucket_name = kwargs.get('bucket_name')
            object_key = kwargs.get('object_key')
            if bucket_name and object_key:
                try:
                    s3 = boto3.client('s3')
                    obj = s3.get_object(Bucket=bucket_name, Key=object_key)
                    self.dataset = pd.read_csv(obj['Body'])
                except ClientError as e:
                    print(f"Error loading dataset from S3 Bucket: {str(e)}")
            else:
                print("Error: Missing bucket_name or object_key argument for S3 dataset.")
        else:
            print("Error: Invalid source argument. Choose from 'local', 'snowflake', 'redis', or 's3'.")

    def drop_unneeded_cols(self, columns):
        self.dataset.drop(columns, axis=1, inplace=True) 

    def replace_missing_vals(self):
        # Replace missing or None/NaN values with 0
        pass

    def data_cleaning(self, df=None, text_cols=None):
        if df is not None:
            self.dataset = df
        # Drop duplicates
        self.dataset = self.dataset.drop_duplicates()

        # Handle missing values
        # self.dataset.fillna(method='ffill', inplace=True)  # Forward fill missing values
        # self.dataset.dropna(inplace=True)  # Drop rows with any missing values


        # Remove low coorelated features
        # self.dataset = self.dataset.drop(['column1', 'column2'], axis=1)

        # Convert data types
        # Convert NaN values to zero
        self.dataset['MRR'] = self.dataset['MRR'].fillna(0)
        self.dataset['CLOSEDATE'] = self.dataset['CLOSEDATE'].fillna(0)
        self.dataset['CLOSEDATE'] = pd.to_datetime(self.dataset['CLOSEDATE'])
        self.dataset['WHEN_TIMESTAMP'] = pd.to_datetime(self.dataset['WHEN_TIMESTAMP'])
        self.dataset = self.dataset.sort_values(by="WHEN_TIMESTAMP", ascending=False)

        # Convert any values that cannot be negative to zero
        self.dataset.loc[self.dataset['MRR'] < 0, 'MRR'] = 0

        # Remove special characters and whitespace
        if text_cols:
            self.dataset["text_cols"] = self.dataset["text_cols"].str.replace('[^a-zA-Z0-9\s]', '')
            self.dataset["text_cols"] = self.dataset["text_cols"].str.strip()

        # Ensure unique identifiers
        # self.dataset['id_column'] = self.dataset.groupby('id_column').ngroup()

        # Convert ids to uuids

        return self.dataset


    def data_normalization(self, columns):
        # Min-max normalization
        scaler = MinMaxScaler()
        self.dataset[columns] = scaler.fit_transform(self.dataset[columns])

    def data_standardization(self, columns):
        scaler = StandardScaler()
        self.dataset[columns] = scaler.fit_transform(self.dataset[columns])

    def categorical_variable_encoding(self, columns):
        # Label encoding for categorical variables
        encoder = LabelEncoder()
        for col in columns:
            self.dataset[col] = encoder.fit_transform(self.dataset[col])

    def save_dataset_to_local_folder(self, folder_path):
        try:
            self.dataset.to_csv(os.path.join(folder_path, 'processed_dataset.csv'), index=False)
            return True
        except Exception as e:
            print(f"Error saving processed dataset to local folder: {str(e)}")
            return False

    def save_dataset_to_snowflake(self, connection_params, table_name):
        try:
            conn = snowflake.connector.connect(**connection_params)
            self.dataset.to_sql(table_name, conn, index=False, if_exists='replace')
            return True
        except Exception as e:
            print(f"Error saving processed dataset to Snowflake: {str(e)}")
            return False

    def save_dataset_to_redis_cache(self, host, port, db, key):
        try:
            r = redis.Redis(host=host, port=port, db=db)
            data_json = self.dataset.to_json()
            r.set(key, data_json)
            return True
        except Exception as e:
            print(f"Error saving processed dataset to Redis Cache: {str(e)}")
            return False

    def save_dataset_to_s3_bucket(self, bucket_name, object_key):
        try:
            s3 = boto3.client('s3')
            s3.put_object(Body=self.dataset.to_csv(index=False), Bucket=bucket_name, Key=object_key)
            return True
        except ClientError as e:
            print(f"Error saving processed dataset to S3 Bucket: {str(e)}")
            return False



if __name__ == "__main__":
    # Initialize Preprocess object
    preprocessor = Preprocess()

    # Load dataset from local folder
    preprocessor.load_dataset(source="local")

    preprocessor.drop_unneeded_cols(columns=["WHEN_TIMESTAMP", "CLOSEDATE"])

    # Perform data preprocessing steps
    # preprocessor.data_cleaning()

    # Perform additional preprocessing steps
    preprocessor.categorical_variable_encoding(columns=["EMPLOYEE_RANGE", "INDUSTRY"])

    preprocessor.data_normalization(columns=['ACTIONS_CRM_CONTACTS', 'ACTIONS_CRM_COMPANIES', 'ACTIONS_CRM_DEALS', 'ACTIONS_EMAIL', 'USERS_CRM_CONTACTS',
       'USERS_CRM_COMPANIES', 'USERS_CRM_DEALS', 'MRR', 'ALEXA_RANK', 'USERS_EMAIL'])

    print("preprocessor.dataset.head(): ", preprocessor.dataset.head())
    # Save processed dataset to local folder
    preprocessor.save_dataset_to_local_folder("csv_data")

    # Save processed dataset to S3
    preprocessor.save_dataset_to_s3_bucket(bucket_name, object_key)

    

