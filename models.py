"""Data models for Quran Visual Cards"""
import json
import os
import uuid
from datetime import datetime
from config import CARDS_DB, DATA_DIR


class Card:
    def __init__(self, title, category, analysis_text, model_type=None,
                 theme=None, front_data=None, back_text=None,
                 card_number=None, card_id=None, created_at=None,
                 arabic_terms=None, steps=None, quote=None,
                 # New fields for enhanced matching
                 model_id=None, visual_type=None, visual_type_secondary=None,
                 is_islamic_content=None, islamic_elements=None,
                 model_confidence=None, matched_model_name=None,
                 # New fields for Quran verse references
                 surah_name=None, verse_number=None, verse_arabic=None, verse_english=None,
                 # Image association
                 image_url=None, version=None):
        self.id = card_id or str(uuid.uuid4())[:8]
        self.title = title
        self.category = category
        self.analysis_text = analysis_text
        self.model_type = model_type  # sequential_chain, tripod, etc. (legacy)
        self.theme = theme  # cool_mint or warm_parchment
        self.front_data = front_data or {}
        self.back_text = back_text or ""
        self.card_number = card_number or 1
        self.arabic_terms = arabic_terms or []
        self.steps = steps or []
        self.quote = quote or ""
        self.created_at = created_at or datetime.now().isoformat()
        # Enhanced matching fields
        self.model_id = model_id  # Reference to mental_models.json entry
        self.visual_type = visual_type  # Primary visual diagram type
        self.visual_type_secondary = visual_type_secondary  # Alternative
        self.is_islamic_content = is_islamic_content if is_islamic_content is not None else False
        self.islamic_elements = islamic_elements or []
        self.model_confidence = model_confidence  # 0.0-1.0 match score
        self.matched_model_name = matched_model_name  # Display name of matched model
        # Quran verse reference fields
        self.surah_name = surah_name
        self.verse_number = verse_number
        self.verse_arabic = verse_arabic
        self.verse_english = verse_english
        self.image_url = image_url
        self.version = version or 1

    def to_dict(self):
        d = {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "analysis_text": self.analysis_text,
            "model_type": self.model_type,
            "theme": self.theme,
            "front_data": self.front_data,
            "back_text": self.back_text,
            "card_number": self.card_number,
            "arabic_terms": self.arabic_terms,
            "steps": self.steps,
            "quote": self.quote,
            "created_at": self.created_at,
        }
        # Include enhanced fields only if set (backward compatible)
        if self.model_id:
            d["model_id"] = self.model_id
        if self.visual_type:
            d["visual_type"] = self.visual_type
        if self.visual_type_secondary:
            d["visual_type_secondary"] = self.visual_type_secondary
        if self.is_islamic_content:
            d["is_islamic_content"] = self.is_islamic_content
        if self.islamic_elements:
            d["islamic_elements"] = self.islamic_elements
        if self.model_confidence is not None:
            d["model_confidence"] = self.model_confidence
        if self.matched_model_name:
            d["matched_model_name"] = self.matched_model_name
        # Quran verse reference fields
        if self.surah_name:
            d["surah_name"] = self.surah_name
        if self.verse_number:
            d["verse_number"] = self.verse_number
        if self.verse_arabic:
            d["verse_arabic"] = self.verse_arabic
        if self.verse_english:
            d["verse_english"] = self.verse_english
        if self.image_url:
            d["image_url"] = self.image_url
        d["version"] = self.version or 1
        return d

    @classmethod
    def from_dict(cls, d):
        return cls(
            title=d["title"],
            category=d["category"],
            analysis_text=d.get("analysis_text", ""),
            model_type=d.get("model_type"),
            theme=d.get("theme"),
            front_data=d.get("front_data", {}),
            back_text=d.get("back_text", ""),
            card_number=d.get("card_number", 1),
            card_id=d.get("id"),
            created_at=d.get("created_at"),
            arabic_terms=d.get("arabic_terms", []),
            steps=d.get("steps", []),
            quote=d.get("quote", ""),
            # New fields — gracefully default if missing
            model_id=d.get("model_id"),
            visual_type=d.get("visual_type"),
            visual_type_secondary=d.get("visual_type_secondary"),
            is_islamic_content=d.get("is_islamic_content", False),
            islamic_elements=d.get("islamic_elements", []),
            model_confidence=d.get("model_confidence"),
            matched_model_name=d.get("matched_model_name"),
            # Quran verse reference fields
            surah_name=d.get("surah_name"),
            verse_number=d.get("verse_number"),
            verse_arabic=d.get("verse_arabic"),
            verse_english=d.get("verse_english"),
            image_url=d.get("image_url"),
            version=d.get("version", 1),
        )


class CardStore:
    """JSON file-based card storage."""

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(CARDS_DB):
            self._save([])

    def _load(self):
        with open(CARDS_DB, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, cards):
        with open(CARDS_DB, "w", encoding="utf-8") as f:
            json.dump(cards, f, indent=2, ensure_ascii=False)

    def get_all(self):
        data = self._load()
        return [Card.from_dict(d) for d in data]

    def get_by_id(self, card_id):
        data = self._load()
        for d in data:
            if d["id"] == card_id:
                return Card.from_dict(d)
        return None

    def save_card(self, card):
        data = self._load()
        # Update if exists
        for i, d in enumerate(data):
            if d["id"] == card.id:
                data[i] = card.to_dict()
                self._save(data)
                return card
        # New card - auto-number
        if not card.card_number or card.card_number == 1:
            card.card_number = len(data) + 1
        data.append(card.to_dict())
        self._save(data)
        return card

    def delete_card(self, card_id):
        data = self._load()
        data = [d for d in data if d["id"] != card_id]
        self._save(data)

    def get_next_number(self):
        data = self._load()
        return len(data) + 1
