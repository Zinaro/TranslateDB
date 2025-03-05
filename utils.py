import cherrypy
from jinja2 import Environment, FileSystemLoader
import os

from db import Database

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
