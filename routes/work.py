# routes/work.py
import cherrypy
from utils import update_jinja_globals, env

cherrypy.tools.update_jinja = cherrypy.Tool('before_request_body', update_jinja_globals)

class Work:
    def __init__(self):
        pass

    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def index(self):
        template = env.get_template('work.html')
        return template.render()





