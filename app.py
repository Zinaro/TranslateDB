import cherrypy
import os

# #eb1616
# #278e43

from routes.data import ImportExport
from routes.translations import Translations
from views import MyWebApp

def load_data_on_start():
    print("[INFO] Fetching initial translations from database...")
    Translations.load_translations()

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app = MyWebApp()
    
    config = {
        'global': {
            'server.socket_host': '127.0.0.1',
            'server.socket_port': 2000,
            'error_page.404': MyWebApp.error_page_404
        },
        '/': {
            'tools.staticdir.root': current_dir
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
        }
    }
    cherrypy.engine.subscribe('start', load_data_on_start)
    cherrypy.quickstart(app, '/', config)
    cherrypy.tree.mount(ImportExport(), '/data')

