# routes/data.py    
import json
import cherrypy
from models.translation_model import translation_model
from models.untranslated_model import untranslated_model
from utils import database, env, update_jinja_globals

cherrypy.tools.update_jinja = cherrypy.Tool('before_request_body', update_jinja_globals)


class ImportExport:
    def __init__(self):
        self.database = database

    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def index(self):
        template = env.get_template('data.html')
        return template.render()

    @cherrypy.expose
    def export(self):
        db_config = self.database.config.get("mongodb", {})
        db_name = db_config.get("dbname", "database")
        try:
            translations = translation_model.get_all_translations()
            if not translations:
                return json.dumps({"error": "No data found in the database!"})
            file_name = f"{db_name}_export.json"
            file_content = json.dumps(translations, indent=4, ensure_ascii=False)
            cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
            cherrypy.response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return file_content.encode('utf-8')
        except Exception as e:
            cherrypy.response.status = 500
            return json.dumps({"error": "Failed to export data", "details": str(e)})


    @cherrypy.expose
    def import_data(self, import_file=None):
        if import_file is None:
            cherrypy.response.status = 400
            return json.dumps({"success": False, "error": "No file uploaded"})

        try:
            uploaded_content = import_file.file.read().decode('utf-8')
            translations, untranslated = [], []

            try:
                data = json.loads(uploaded_content)
                if not isinstance(data, list):
                    raise ValueError
                for item in data:
                    english = item.get("english", "").strip()
                    kurdish = item.get("kurdish", "").strip()
                    if english and kurdish:
                        translations.append({"english": english, "kurdish": kurdish})
                    elif english and not kurdish:
                        untranslated_model.insert_translation({"english": english, "kurdish": ""})

            except json.JSONDecodeError:
                translations = []
                lines = uploaded_content.strip().split('\n')
                current_english = None

                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('msgctxt'):
                        continue

                    if line.startswith('msgid'):
                        current_english = line[len('msgid'):].strip().strip('\"')
                    elif line.startswith('msgstr'):
                        current_kurdish = line[len('msgstr'):].strip().strip('"')
                        if current_english:
                            if current_kurdish:
                                translations.append({"english": current_english, "kurdish": current_kurdish})
                            else:
                                untranslated_model.insert_translation({"english": current_english, "kurdish": ""})
                        current_kurdish = current_english = None
                    elif any(separator in line for separator in [":", "=", ","]):
                        separator_used = next((sep for sep in [":", "=", ","] if sep in line), None)
                        key, value = line.split(separator_used, 1)
                        key = key.strip().lower()
                        value = value.strip()

                        if key in ["en", "english", "msgid"]:
                            current_english = value
                        elif key in ["ku", "kurdish", "msgstr"]:
                            if current_english:
                                if value:
                                    translations.append({"english": current_english, "kurdish": value})
                                else:
                                    untranslated_model.insert_translation({"english": current_english, "kurdish": ""})
                            current_english = None

            if not translations:
                raise ValueError("No valid translations found to import")

            inserted_count = 0
            existing_english_words = translation_model.get_existing_translations_by_english(
                [t["english"] for t in translations])

            for translation in translations:
                if translation["english"] not in existing_english_words:
                    translation_model.insert_translation(translation)
                    inserted_count += 1

            return json.dumps({
                "success": True,
                "message": f"{inserted_count} translations imported successfully."
            })

        except Exception as e:
            cherrypy.response.status = 500
            return json.dumps({
                "success": False,
                "error": f"Failed to import data, {e}",
                "details": str(e)
            })





    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    def delete_all(self):
        try:
            translation_model.delete_all_translations()
            return json.dumps({
                "success": True,
                "message": "All translations have been deleted successfully."
            })
        except Exception as e:
            cherrypy.response.status = 500
            return json.dumps({
                "success": False,
                "error": "Failed to delete translations.",
                "details": str(e)
            })