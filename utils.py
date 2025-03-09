# utils.py

import cherrypy
from jinja2 import Environment, FileSystemLoader
import os
import csv
import polib

from db import Database


UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

env = Environment(loader=FileSystemLoader('templates'), auto_reload=True)
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
database = Database(config_path)

def update_jinja_globals():
    env.globals['request'] = {
        "path": cherrypy.request.path_info,
        "full_url": cherrypy.url(),
        "method": cherrypy.request.method,
        "query_string": cherrypy.request.query_string
    }

def parse_csv(filepath):
    translations = []
    try:
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 2:
                    translations.append({"english": row[0].strip(), "kurdish": row[1].strip()})
    except Exception as e:
        return {"error": f"CSV read error: {str(e)}", "translations": []}
    
    return {"message": "CSV file parsed successfully.", "translations": translations}

def parse_po(filepath):
    translations = []
    try:
        po_file = polib.pofile(filepath)
        for entry in po_file:
            translations.append({"msgid": entry.msgid, "msgstr": entry.msgstr})
    except Exception as e:
        return {"error": f"PO read error: {str(e)}", "translations": []}
    
    return {"message": "PO file parsed successfully.", "translations": translations}