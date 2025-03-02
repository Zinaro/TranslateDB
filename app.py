import cherrypy
import os
# #eb1616
from views import MyWebApp

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config = {
        'global': {
            'server.socket_host': '127.0.0.1',
            'server.socket_port': 2001,
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
    cherrypy.quickstart(MyWebApp(), '/', config)
