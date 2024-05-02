import pandas as pd
import pickle as pkl
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

class Model:
    def __init__(self, dataset_path, location_type, cloud_path=None):
        self.dataset_path = dataset_path
        self.location_type = location_type  # Could be a local folder, S3, Snowflake, Redis, etc.
        self.cloud_path = cloud_path
        self.dataset = None

        self.hotlead_model = None
        self.best_mrr_model = None

        self.saved_mdl_path = None

        self.train_X = None
        self.train_y = None
        self.val_X = None
        self.val_y = None
        self.test_X = None
        self.test_y = None


    def load_dataset(self):
        if self.location_type == "local":
            self.dataset = pd.read_csv(self.dataset_path)
        
        elif self.location_type == "s3":
            pass
    
    def drop_additional_columns(self, columns):
        pass

    def split_datasets(self, test=False, percentages=[.8, .2]):
        if test:
            assert len(percentages) == 3
            # Split data into train, val, and  test:

        else:
           assert len(percentages) == 2
        
        # Split data into dependent and independent variables
        X = self.dataset.drop(["converted_within30"], axis=1)
        y = self.dataset["converted_within30"]
        # Split data into train and validation
        self.train_X, self.val_X, self.train_y, self.val_y = train_test_split(X, y, test_size=percentages[1], random_state=42)


    def define_hotlead_model(self):
        self.hotlead_model = XGBClassifier(objective='binary:logistic')
        print("self.hotlead_model: ", self.hotlead_model)
    
    def define_best_mrr_model(self):
        pass

    def tune_hyperparams(self):
        pass

    def train_model(self):
        self.hotlead_model.fit(self.train_X, self.train_y)


    def plot_mdl_train():
        pass

    def load_mdl_ckpt(self, file_path="xgboost_model.pkl"):
        with open(file_path, 'rb') as f:
            self.hotlead_model = pkl.load(f)


    def save_mdl_ckpt(self, file_path=None):
        if not file_path:
            file_path = "model.pkl"

        with open(file_path, 'wb') as f:
            pkl.dump(model, f)
        
        self.saved_mdl_path = file_path
    

    def evaluate_model(self):
        # Quick prediction test on val set
        y_val_pred = self.hotlead_model.predict(self.val_X)

        print(classification_report(self.val_y, y_val_pred))

    
    def predict(data):
        pass
        # TODO Predict Target vals of data


if __name__ == "__main__":
    
    model = Model(dataset_path="csv_data/processed_dataset.csv", location_type="local")
    model.load_dataset()

    model.split_datasets()  # Create train and validation datasets

    # Create Model Ensemble
    model.define_hotlead_model()
    model.define_best_mrr_model()

    # Train Models
    model.train_model()

    model.evaluate_model()