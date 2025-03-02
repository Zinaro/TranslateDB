# db.py
from pymongo import MongoClient
import json
import os

class Database:
    def __init__(self, config_path):
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
            return MongoClient(self.config['mongodb']['host'])[self.config['mongodb']['dbname']]
        '''
        elif 'mysql' in self.config:
            return pymysql.connect(host=self.config['mysql']['host'],
                                   user=self.config['mysql']['user'],
                                   password=self.config['mysql']['password'],
                                   db=self.config['mysql']['dbname'])
        elif 'postgresql' in self.config:
            return psycopg2.connect(host=self.config['postgresql']['host'],
                                    user=self.config['postgresql']['user'],
                                    password=self.config['postgresql']['password'],
                                    dbname=self.config['postgresql']['dbname'])
        '''

