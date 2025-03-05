# models/translation_model.py
import json

from bson.objectid import ObjectId
from utils import database

class TranslationModel:
    def __init__(self):
        self.collection = database.get_collection('translations')

    def add_translation(self, english, kurdish):
        try:
            result = self.collection.insert_one({"english": english, "kurdish": kurdish})
            return str(result.inserted_id)
        except Exception as e:
            print(f"[ERROR] add_translation failed: {e}")
            return None


    def get_all_translations(self):
        try:
            results = list(self.collection.find({}))
            return [
                {"_id": str(item["_id"]), "english": item.get("english", ""), "kurdish": item.get("kurdish", "")}
                for item in results
            ]
        except Exception as e:
            print(f"[ERROR] get_all_translations failed: {e}")
            return []


    def update_translation(self, translation_id, english, kurdish):
        try:
            object_id = ObjectId(translation_id)
            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": {"english": english, "kurdish": kurdish}}
            )
            return result.modified_count > 0 
        except Exception as e:
            print(f"[ERROR] update_translation failed: {e}")
            return False

    def delete_translation(self, translation_id):
        try:
            object_id = ObjectId(translation_id)
            result = self.collection.delete_one({"_id": object_id})
            return result.deleted_count > 0 
        except Exception as e:
            print(f"[ERROR] delete_translation failed: {e}")
            return False


    def search_translations(self, query):
        try:
            regex_query = {"$regex": query, "$options": "i"}
            results = self.collection.find({
                "$or": [
                    {"english": regex_query},
                    {"kurdish": regex_query}
                ]
            })
            return json.dumps([
                {"_id": str(item["_id"]), "english": item["english"], "kurdish": item["kurdish"]}
                for item in results
            ])
        except Exception as e:
            print(f"[ERROR] search_translations failed: {e}")
            return json.dumps([])

translation_model = TranslationModel()
