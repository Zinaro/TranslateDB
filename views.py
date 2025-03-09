# views.py
import cherrypy
from routes.data import ImportExport
from routes.translations import Translations
from routes.work import Work
from utils import update_jinja_globals, env, database


cherrypy.tools.update_jinja = cherrypy.Tool('before_request_body', update_jinja_globals)

class MyWebApp:
    def __init__(self):
        self.database = database
        self.translations = Translations()
        self.data = ImportExport()
        self.work = Work()


    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def index(self):
        if database.db is None:
            raise cherrypy.HTTPRedirect("/setup")
        collection_name = "translations"
        translations = self.database.get_data(collection_name)
        total_translations = len(translations)
        db_name = list(self.database.config.keys())[0]
        database_name = self.database.config[db_name]["dbname"] if "mongodb" in self.database.config else "Unknown"
        template = env.get_template('index.html')
        return template.render(
            translations=translations,
            total_translations=total_translations,
            db_name=db_name,
            database_name=database_name,
            collection_name=collection_name,
            )
    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def setup(self):
        template = env.get_template('setup.html')
        return template.render()
    @cherrypy.expose
    def save_config(self, dbType, dbHost, dbName, dbUser=None, dbPassword=None):
        database.save_config(dbType, dbHost, dbName, dbUser, dbPassword)
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def signin(self):
        template = env.get_template('signin.html')
        return template.render()
    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def signup(self):
        template = env.get_template('signup.html')
        return template.render()
    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def err404(self):
        template = env.get_template('404.html')
        return template.render()
        
    def error_page_404(status, message, traceback, version):
        cherrypy.response.headers['Content-Type'] = 'text/html; charset=utf-8'
        template = env.get_template('404.html')
        return template.render()


