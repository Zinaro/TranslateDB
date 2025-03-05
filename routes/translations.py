# routes/translations.py
import json
import cherrypy
from models.translation_model import translation_model
from utils import update_jinja_globals, env, database

cherrypy.tools.update_jinja = cherrypy.Tool('before_request_body', update_jinja_globals)

translations_cache = []
class Translations:
    def __init__(self):
        self.database = database

    @classmethod
    def load_translations(cls):
        global translations_cache
        translations_cache = translation_model.get_all_translations()
        print(f"[INFO] Cached {len(translations_cache)} translations.")

    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def index(self):
        translations = translation_model.get_all_translations()
        template = env.get_template('translate/translations.html')
        return template.render( translations=translations)
    @cherrypy.expose
    def all(self):
        return json.dumps([
            {"_id": str(item["_id"]), "english": item["english"], "kurdish": item["kurdish"]}
            for item in translations_cache
        ])

   
    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def add(self, english=None, kurdish=None):
        if cherrypy.request.method == "POST":
            if english and kurdish:
                translation_model.add_translation(english, kurdish)
                self.load_translations()
                return self.render_add_page("Translation added successfully!")
            else:
                return self.render_add_page("Please fill in both fields.")
        return self.render_add_page()
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def update(self):
        data = cherrypy.request.json
        if "id" in data and "english" in data and "kurdish" in data:
            success = translation_model.update_translation(data["id"], data["english"], data["kurdish"])
            if success:
                self.load_translations()
            return {"success": success}
        return {"success": False, "error": "Missing parameters"}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def delete(self):
        data = cherrypy.request.json
        if "id" in data:
            success = translation_model.delete_translation(data["id"])
            if success:
                self.load_translations() 
            return {"success": success}
        return {"success": False, "error": "Missing parameters"}


    
    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def render_add_page(self, success_message=None):
        return env.get_template("translate/add.html").render(success_message=success_message)
    
    @cherrypy.expose
    def search(self, query=None):
        print(f"[INFO] Search query: {query}", len(query))
        if not query:
            return json.dumps([])
        query = query.lower()
        results = [
            {"_id": str(t["_id"]), "english": t["english"], "kurdish": t["kurdish"]}
            for t in translation_model.get_all_translations()
            if query in t["english"].lower() or query in t["kurdish"].lower()
        ]
        if len(query) == 0 or query == '':
            results = translation_model.get_all_translations()
        return json.dumps(results)
    
    