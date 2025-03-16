# routes/untranslated.py
import json
import cherrypy
from models.untranslated_model import untranslated_model
from models.translation_model import translation_model
from utils import update_jinja_globals, env, database

cherrypy.tools.update_jinja = cherrypy.Tool('before_request_body', update_jinja_globals)

untranslated_cache = []

class Untranslated:
    def __init__(self):
        self.database = database
        self.load_untranslated()

    @classmethod
    def load_untranslated(cls):
        global untranslated_cache

        untranslated_cache = untranslated_model.get_all_translations()
        print(f"[INFO] Cached {len(untranslated_cache)} untranslated entries.")

    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def index(self):
        untranslated = untranslated_model.get_all_translations()
        self.load_untranslated()
        template = env.get_template('translate/untranslated.html')
        return template.render(untranslated=untranslated)

    @cherrypy.expose
    def all(self):
        return json.dumps([
            {
                "_id": str(item["_id"]),
                "english": item["english"],
                "kurdish": item.get("kurdish", ""),
                "googletrans": item.get("googletrans", "")
            }
            for item in untranslated_cache
        ])

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def update(self):
        data = cherrypy.request.json
        if "id" in data and "english" in data and "kurdish" in data:
            if data["kurdish"].strip():
                translation_model.insert_translation({"english": data["english"], "kurdish": data["kurdish"]})
                untranslated_model.delete_translation(data["id"])
            else:
                untranslated_model.update_translation(data["id"], data["english"], data["kurdish"])
            self.load_untranslated()
            return {"success": True}
        return {"success": False, "error": "Missing parameters"}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def delete(self):
        data = cherrypy.request.json
        if "id" in data:
            success = untranslated_model.delete_translation(data["id"])
            if success:
                self.load_untranslated()
            return {"success": success}
        return {"success": False, "error": "Missing parameters"}

    @cherrypy.expose
    def search(self, query=None):
        if not query:
            return json.dumps(untranslated_cache)
        query = query.lower()
        results = [
            {"_id": str(t["_id"]), "english": t["english"], "kurdish": t["kurdish"]}
            for t in untranslated_cache
            if query in t["english"].lower()
        ]
        results_sorted = sorted(results, key=lambda x: len(x["english"]))
        return json.dumps(results_sorted)

    @cherrypy.expose
    def refresh(self):
        self.load_untranslated()
        return
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def google_translate(self):
        data = cherrypy.request.json
        if "id" in data and "english" in data:
            try:
                from services.google_translation_service import GoogleTranslationService
                translator = GoogleTranslationService()
                kurdish_translation = translator.translate_text(data["english"])

                if kurdish_translation: 
                    untranslated_model.update_translation(data["id"], data["english"], "", kurdish_translation)
                    self.load_untranslated()
                    return {"success": True, "googletrans": kurdish_translation}
                return {"success": False, "error": "Translation failed"}

            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Missing parameters"}

