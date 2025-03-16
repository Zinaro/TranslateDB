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
            MAX_SIZE = 10 * 1024 * 1024
            if hasattr(import_file.file, 'seek') and hasattr(import_file.file, 'tell'):
                import_file.file.seek(0, 2)
                size = import_file.file.tell()
                import_file.file.seek(0)
                if size > MAX_SIZE:
                    cherrypy.response.status = 413 
                    return json.dumps({"success": False, "error": "File too large"})
            CHUNK_SIZE = 1024 * 1024
            content_chunks = []
            while True:
                chunk = import_file.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                content_chunks.append(chunk)
            uploaded_content = b''.join(content_chunks).decode('utf-8')
            translations = []
            untranslated_count = 0
            seen_english = set()
            all_existing_translations = set([item["english"] for item in translation_model.get_all_translations()])
            all_existing_untranslated = set([item["english"] for item in untranslated_model.get_all_translations()])
            try:
                data = json.loads(uploaded_content)
                if not isinstance(data, list):
                    raise ValueError("JSON data must be a list")
                
                for item in data:
                    english = item.get("english", "").strip()
                    kurdish = item.get("kurdish", "").strip()
                    if not english or english in seen_english or english in all_existing_translations or english in all_existing_untranslated:
                        continue
                    seen_english.add(english)
                    if kurdish:
                        translations.append({"english": english, "kurdish": kurdish})
                    else:
                        untranslated_model.insert_translation({"english": english, "kurdish": ""})
                        all_existing_untranslated.add(english)
                        untranslated_count += 1

            except (json.JSONDecodeError, ValueError) as json_error:
                translations = []
                lines = uploaded_content.strip().split('\n')
                current_english = None

                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('msgctxt'):
                        continue

                    if line.startswith('msgid'):
                        current_english = line[len('msgid'):].strip().strip('\"')
                        if (not current_english or 
                            current_english in seen_english or 
                            current_english in all_existing_translations or
                            current_english in all_existing_untranslated):
                            current_english = None
                        else:
                            seen_english.add(current_english)
                    elif line.startswith('msgstr'):
                        if current_english is None:
                            continue
                        current_kurdish = line[len('msgstr'):].strip().strip('"')
                        if current_kurdish:
                            translations.append({"english": current_english, "kurdish": current_kurdish})
                        else:
                            untranslated_model.insert_translation({"english": current_english, "kurdish": ""})
                            all_existing_untranslated.add(current_english)
                            untranslated_count += 1
                        current_kurdish = current_english = None
                    elif any(separator in line for separator in [":", "=", ","]):
                        separator_used = next((sep for sep in [":", "=", ","] if sep in line), None)
                        key, value = line.split(separator_used, 1)
                        key = key.strip().lower()
                        value = value.strip()

                        if key in ["en", "english", "msgid"]:
                            if value and value not in seen_english and value not in all_existing_translations and value not in all_existing_untranslated:
                                current_english = value
                                seen_english.add(value)
                            else:
                                current_english = None
                        elif key in ["ku", "kurdish", "msgstr"]:
                            if current_english is None:
                                continue
                            if value:
                                translations.append({"english": current_english, "kurdish": value})
                            else:
                                untranslated_model.insert_translation({"english": current_english, "kurdish": ""})
                                all_existing_untranslated.add(current_english)
                                untranslated_count += 1
                            current_english = None

            if not translations and untranslated_count == 0:
                raise ValueError("No valid translations or untranslated entries found to import")

            inserted_count = 0
            for translation in translations:
                if translation["english"] not in all_existing_translations:
                    translation_model.insert_translation(translation)
                    inserted_count += 1

            return json.dumps({
                "success": True,
                "message": f"{inserted_count} translations and {untranslated_count} untranslated entries imported successfully."
            })

        except Exception as e:
            cherrypy.response.status = 500
            return json.dumps({
                "success": False,
                "error": f"Failed to import data: {str(e)}",
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
        
    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    def delete_untranslated(self):
        try:
            untranslated_model.delete_all_translations()
            return json.dumps({
                "success": True,
                "message": "All untranslated have been deleted successfully."
            })
        except Exception as e:
            cherrypy.response.status = 500
            return json.dumps({
                "success": False,
                "error": "Failed to delete untranslated.",
                "details": str(e)
            })