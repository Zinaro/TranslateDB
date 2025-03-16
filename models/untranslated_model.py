# models/untranslated_model.py
from bson.objectid import ObjectId
from utils import database

class UntranslatedModel:
    def __init__(self):
        self.collection = database.get_collection('untranslated')

    def insert_translation(self, data):
        try:
            self.collection.insert_one(data)
        except Exception as e:
            print(f"[ERROR] insert_translation failed: {e}")

    def delete_all_translations(self):
        try:
            self.collection.delete_many({})
        except Exception as e:
            print(f"[ERROR] delete_all_translations failed: {e}")

    def get_all_translations(self):
        try:
            results = list(self.collection.find({}))
            return [
                {
                    "_id": str(item["_id"]),
                    "english": item["english"],
                    "kurdish": item.get("kurdish", ""),
                    "googletrans": item.get("googletrans", "")
                }
                for item in results
            ]
        except Exception as e:
            print(f"[ERROR] get_all_translations failed: {e}")
            return []

    def get_existing_translations_by_english(self, english_words):
        try:
            existing = self.collection.find({"english": {"$in": english_words}}, {"english": 1})
            return set(item["english"] for item in existing)
        except Exception as e:
            print(f"[ERROR] get_existing_translations_by_english failed: {e}")
            return set()

    def get_translation_by_english(self, english_word):
        try:
            return self.collection.find_one({"english": english_word})
        except Exception as e:
            print(f"[ERROR] get_translation_by_english failed: {e}")
            return None

    def delete_translation(self, translation_id):
        try:
            object_id = ObjectId(translation_id)
            result = self.collection.delete_one({"_id": object_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"[ERROR] delete_translation failed: {e}")
            return False

    def update_translation(self, translation_id, english, kurdish, googletrans=None):
        try:
            update_data = {"english": english, "kurdish": kurdish}
            if googletrans is not None:
                update_data["googletrans"] = googletrans

            object_id = ObjectId(translation_id)
            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"[ERROR] update_translation failed: {e}")
            return False


untranslated_model = UntranslatedModel()
untranslated_model.collection = database.get_collection('untranslated')