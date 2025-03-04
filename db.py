# db.py
from pymongo import MongoClient
import json
import os

class Database:
    _instance = None 
    
    def __new__(cls, config_path):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.init_db(config_path)
        return cls._instance

    def init_db(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()
        self.db = self.connect_to_db()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return None

    def save_config(self, dbType, dbHost, dbName, dbUser=None, dbPassword=None):
        config_data = {
            dbType.lower(): {
                "host": dbHost,
                "dbname": dbName,
                "user": dbUser,
                "password": dbPassword
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=4)
        self.config = self.load_config()
        self.db = self.connect_to_db()

    def connect_to_db(self):
        if not self.config:
            return None
        if 'mongodb' in self.config:
            print("[INFO] Establishing a MongoDB connection...")
            return MongoClient(self.config['mongodb']['host'])[self.config['mongodb']['dbname']]
    def get_collection(self, collection_name):
        if self.db is not None:
            return self.db[collection_name]
        return None
    def get_data(self, collection_name, query=None, projection=None):
        if self.db is None:
            print("[ERROR] Database connection not found!")
            return []
        collection = self.get_collection(collection_name)
        if collection is not None:
            return list(collection.find(query or {}, projection or {"_id": 0}))
        return []

