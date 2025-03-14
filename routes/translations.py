# routes/translations.py
import json
import cherrypy
from models.translation_model import translation_model
from models.untranslated_model import untranslated_model
from routes.untranslated import Untranslated
from utils import update_jinja_globals, env, database

cherrypy.tools.update_jinja = cherrypy.Tool('before_request_body', update_jinja_globals)

translations_cache = []
class Translations:
    def __init__(self):
        self.database = database
        self.untranslated = Untranslated()
        self.load_translations()


    @classmethod
    def load_translations(cls):
        global translations_cache
        translations_cache = translation_model.get_all_translations()
        print(f"[INFO] Cached {len(translations_cache)} translations.")

    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def index(self):
        translations = translation_model.get_all_translations()
        self.load_translations()
        template = env.get_template('translate/translations.html')
        return template.render( translations=translations)
    @cherrypy.expose
    def all(self):
        return json.dumps([
            {"_id": str(item["_id"]), "english": item["english"], "kurdish": item["kurdish"]}
            for item in translations_cache
        ])

    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def update(self):
        data = cherrypy.request.json
        if "id" in data and "english" in data and "kurdish" in data:
            if not data["kurdish"].strip():
                translation_model.delete_translation(data["id"])
                untranslated_model.insert_translation({"id": data["id"], "english": data["english"]})
                self.load_translations()
                return {"success": True}
            else:
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
    def add(self, english=None, kurdish=None):
        success_message = None
        success = None
        if cherrypy.request.method == "POST":
            if english and kurdish:
                existing = translation_model.get_existing_translations_by_english([english])
                if english in existing:
                    success_message = "This translation already exists!"
                    success = False
                else:
                    translation_model.add_translation(english, kurdish)
                    self.load_translations()
                    success_message = "Translation added successfully!"
                    success = True
            else:
                success_message = "Please fill in both fields."
                success = False
        return env.get_template("translate/add.html").render(
            success_message=success_message,
            success=success
        )
    
    @cherrypy.expose
    def search(self, query=None):
        print(f"[INFO] Search query: {query}", len(query))
        if not query:
            return json.dumps(translations_cache)
        query = query.lower()
        results = [
            {"_id": str(t["_id"]), "english": t["english"], "kurdish": t["kurdish"]}
            for t in translations_cache
            if query in t["english"].lower() or query in t["kurdish"].lower()
        ]
        results_sorted = sorted(results, key=lambda x: len(x["english"]))
        return json.dumps(results_sorted)
    
    @cherrypy.expose
    def refresh(self):
        self.load_translations()
        return
    
    