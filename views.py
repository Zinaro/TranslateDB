import cherrypy
from jinja2 import Environment, FileSystemLoader
from db import Database
import os

env = Environment(loader=FileSystemLoader('templates'))
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
database = Database(config_path)

class MyWebApp:
    @cherrypy.expose
    def index(self):
        if database.db is None:
            raise cherrypy.HTTPRedirect("/setup")
        template = env.get_template('index.html')
        return template.render()
    @cherrypy.expose
    def setup(self):
        template = env.get_template('setup.html')
        return template.render()
    @cherrypy.expose
    def save_config(self, dbType, dbHost, dbName, dbUser=None, dbPassword=None):
        database.save_config(dbType, dbHost, dbName, dbUser, dbPassword)
        raise cherrypy.HTTPRedirect("/")
    
    @cherrypy.expose
    def blank(self):
        template = env.get_template('blank.html')
        return template.render()
    @cherrypy.expose
    def button(self):
        template = env.get_template('button.html')
        return template.render()
    @cherrypy.expose
    def chart(self):
        template = env.get_template('chart.html')
        return template.render()
    @cherrypy.expose
    def element(self):
        template = env.get_template('element.html')
        return template.render()
    @cherrypy.expose
    def form(self):
        template = env.get_template('form.html')
        return template.render()
    @cherrypy.expose
    def signin(self):
        template = env.get_template('signin.html')
        return template.render()
    @cherrypy.expose
    def signup(self):
        template = env.get_template('signup.html')
        return template.render()
    @cherrypy.expose
    def table(self):
        template = env.get_template('table.html')
        return template.render()
    @cherrypy.expose
    def typography(self):
        template = env.get_template('typography.html')
        return template.render()
    @cherrypy.expose
    def widget(self):
        template = env.get_template('widget.html')
        return template.render()
    @cherrypy.expose
    def err404(self):
        template = env.get_template('404.html')
        return template.render()
        
    def error_page_404(status, message, traceback, version):
        cherrypy.response.headers['Content-Type'] = 'text/html; charset=utf-8'
        template = env.get_template('404.html')
        return template.render()

