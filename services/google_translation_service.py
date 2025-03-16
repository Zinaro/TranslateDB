# services/google_translation_service.py

import asyncio
from googletrans import Translator
from models.untranslated_model import untranslated_model

class GoogleTranslationService:
    def __init__(self):
        self.translator = Translator()

    async def async_translate_text(self, english_text):
        try:
            print(f"[DEBUG] Translating: {english_text}")
            translated = await self.translator.translate(english_text, src='en', dest='ku')
            print(f"[DEBUG] Translated '{english_text}' to '{translated.text}'")
            return translated.text
        except Exception as e:
            print(f"[ERROR] Translation failed for '{english_text}': {e}")
            return None

    def translate_text(self, english_text):
        return asyncio.run(self.async_translate_text(english_text))

    def translate_and_store_all(self):
        print("[INFO] Fetching untranslated entries...")
        untranslated_entries = untranslated_model.get_all_translations()
        print(f"[INFO] Total untranslated entries found: {len(untranslated_entries)}")

        for entry in untranslated_entries:
            english_text = entry["english"]
            print(f"[DEBUG] Processing: {english_text}")

            if entry.get("googletrans"):
                print(f"[INFO] Skipping already cached: {english_text}")
                continue

            kurdish_text = self.translate_text(english_text)
            if kurdish_text:
                try:
                    print(f"[DEBUG] Updating googletrans for: {english_text}")
                    untranslated_model.update_translation(
                        entry["_id"],
                        english_text,
                        entry.get("kurdish", ""),
                        kurdish_text
                    )
                    print(f"[INFO] Successfully updated: {english_text} -> {kurdish_text}")
                except Exception as e:
                    print(f"[ERROR] Failed to update translation: {e}")
            else:
                print(f"[ERROR] Failed to translate: {english_text}")


