# routes/work.py
import os
import polib
import json

import cherrypy
from utils import update_jinja_globals, env, database, parse_csv, parse_po

cherrypy.tools.update_jinja = cherrypy.Tool('before_request_body', update_jinja_globals)
UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class Work:
    def __init__(self):
        self.original_file_path = None
        self.db = database

    @cherrypy.expose
    @cherrypy.tools.update_jinja()
    def index(self):
        template = env.get_template('work.html')
        return template.render()
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def upload(self, file):
        filepath = os.path.join(UPLOAD_DIR, file.filename)
        self.original_file_path = filepath
        with open(filepath, 'wb') as f:
            while True:
                data = file.file.read(8192)
                if not data:
                    break
                f.write(data)
        if filepath.endswith(".csv"):
            result = parse_csv(filepath)
        elif filepath.endswith(".po"):
            result = parse_po(filepath)
            if "translations" in result:
                result["translations"] = self.translate_po(result["translations"])
        else:
            return {"message": "Unsupported file format!", "translations": []}
        return result

    def translate_po(self, translations):
        collection_name = "translations"
        db_translations = self.db.get_data(collection_name, {}, {"english": 1, "kurdish": 1})
        translation_dict = {item["english"]: item["kurdish"] for item in db_translations if "english" in item and "kurdish" in item}
        for item in translations:
            if "msgid" in item and item["msgid"]:
                item["msgstr"] = translation_dict.get(item["msgid"], "")

        return translations
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def save_and_export(self):
        try:
            if not self.original_file_path or not os.path.exists(self.original_file_path):
                return {"error": "No original file found!"}
            raw_body = cherrypy.request.body.read().decode("utf-8")
            data = json.loads(raw_body)
            user_translations = {item["msgid"]: item for item in data.get("translations", [])}
            export_path = os.path.join(UPLOAD_DIR, "translated_export.po")

            with open(self.original_file_path, "r", encoding="utf-8") as infile, \
                 open(export_path, "w", encoding="utf-8") as outfile:

                inside_entry = False
                current_msgid = None
                updated_lines = []

                for line in infile:
                    stripped_line = line.strip()

                    if stripped_line.startswith("msgid"):
                        inside_entry = True
                        current_msgid = stripped_line[7:-1]
                    elif stripped_line.startswith("msgstr") and inside_entry:
                        inside_entry = False
                        if current_msgid in user_translations and user_translations[current_msgid].get("approved", False):
                            new_translation = user_translations[current_msgid]["msgstr"]
                            line = f'msgstr "{new_translation}"\n'
                    updated_lines.append(line)
                outfile.writelines(updated_lines)
            return {"message": "File is ready for download.", "download_url": "/work/export"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format in request body"}
        except Exception as e:
            return {"error": f"Failed to save and export: {str(e)}"}

    @cherrypy.expose
    def export(self):
        try:
            file_name = "translated_export.po"
            file_path = os.path.join(UPLOAD_DIR, file_name)

            if not os.path.exists(file_path):
                return json.dumps({"error": "File not found!"})

            cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
            cherrypy.response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
            
            with open(file_path, "rb") as f:
                return f.read()

        except Exception as e:
            cherrypy.response.status = 500
            return json.dumps({"error": "Failed to export file", "details": str(e)})