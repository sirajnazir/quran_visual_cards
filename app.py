"""Flask backend for Quran Visual Cards Pipeline."""
import json
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from models import Card, CardStore
from core_intelligence import (analyze_with_llm, generate_back_text_with_llm,
                                get_model_repository, analyze_single_theme,
                                analyze_single_framing)
from image_gen import (generate_card_spread, generate_card_front,
                       generate_card_back, generate_prompt_only,
                       generate_from_custom_prompt, refine_card_image,
                       split_spread_into_cards)
from config import (SECRET_KEY, DEBUG, HOST, PORT, EXPORT_DIR,
                    THEMES, MODEL_TYPES, VISUAL_TYPES, GOOGLE_AI_API_KEY)
from style_presets import get_preset, list_all_presets, PRESET_NAMES
from content_evaluator import evaluate_card, quick_evaluate, get_dimension_scores
from hero_character import get_hero_summary, list_hero_styles, list_poses, HERO_PRESETS
from quran_verses import get_verse, get_surah_verses, get_cache_stats
from tafsir import get_tafsir, get_tafsir_surah, get_tafsir_cache_stats
from surah_covers import (get_cover_url, get_all_covers, save_cover,
                          build_cover_prompt, build_category_cover_prompt,
                          get_surah_visual, build_verse_thumb_prompt,
                          get_verse_thumb_url, save_verse_thumb)

app = Flask(__name__)
app.secret_key = SECRET_KEY
store = CardStore()

os.makedirs(EXPORT_DIR, exist_ok=True)


@app.route("/")
def index():
    cards = store.get_all()
    return render_template("index.html",
                           cards=[c.to_dict() for c in cards],
                           themes=THEMES,
                           model_types=MODEL_TYPES,
                           has_google_key=bool(GOOGLE_AI_API_KEY),
                           has_anthropic_key=bool(os.environ.get("ANTHROPIC_API_KEY")))


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Analyze input text and return structured card data with model matching."""
    data = request.json
    title = data.get("title", "")
    category = data.get("category", "")
    analysis_text = data.get("analysis_text", "")

    if not title or not analysis_text:
        return jsonify({"error": "Title and analysis text are required"}), 400

    try:
        result = analyze_with_llm(title, category, analysis_text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/api/analyze-theme", methods=["POST"])
def analyze_theme():
    """Analyze a single theme from a multi-theme split."""
    data = request.json
    title = data.get("title", "")
    category = data.get("category", "")
    analysis_text = data.get("analysis_text", "")
    theme_data = data.get("theme_data", {})
    phase1_raw = data.get("phase1_raw", "")

    if not title or not analysis_text or not theme_data:
        return jsonify({"error": "title, analysis_text, and theme_data are required"}), 400

    try:
        result = analyze_single_theme(title, category, analysis_text, theme_data, phase1_raw)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Theme analysis failed: {str(e)}"}), 500


@app.route("/api/analyze-framing", methods=["POST"])
def analyze_framing():
    """Analyze content through a user-chosen framing/angle."""
    data = request.json
    title = data.get("title", "")
    category = data.get("category", "")
    analysis_text = data.get("analysis_text", "")
    framing_data = data.get("framing_data", {})
    phase1_raw = data.get("phase1_raw", "")

    if not title or not analysis_text or not framing_data:
        return jsonify({"error": "title, analysis_text, and framing_data are required"}), 400

    try:
        result = analyze_single_framing(title, category, analysis_text, framing_data, phase1_raw)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Framing analysis failed: {str(e)}"}), 500


@app.route("/api/cards", methods=["GET"])
def list_cards():
    """List all saved cards."""
    cards = store.get_all()
    return jsonify([c.to_dict() for c in cards])


@app.route("/api/cards", methods=["POST"])
def create_card():
    """Create and save a new card."""
    data = request.json
    card = Card(
        title=data.get("title", ""),
        category=data.get("category", ""),
        analysis_text=data.get("analysis_text", ""),
        model_type=data.get("model_type"),
        theme=data.get("theme"),
        front_data=data.get("front_data", {}),
        back_text=data.get("back_text", ""),
        card_number=data.get("card_number") or store.get_next_number(),
        arabic_terms=data.get("arabic_terms", []),
        steps=data.get("steps", []),
        quote=data.get("quote", ""),
        model_id=data.get("model_id"),
        visual_type=data.get("visual_type"),
        visual_type_secondary=data.get("visual_type_secondary"),
        is_islamic_content=data.get("is_islamic_content", False),
        islamic_elements=data.get("islamic_elements", []),
        model_confidence=data.get("model_confidence"),
        matched_model_name=data.get("matched_model_name", ""),
        surah_name=data.get("surah_name"),
        verse_number=data.get("verse_number"),
        verse_arabic=data.get("verse_arabic"),
        verse_english=data.get("verse_english"),
        image_url=data.get("image_url"),
    )
    saved = store.save_card(card)
    return jsonify(saved.to_dict()), 201


@app.route("/api/cards/<card_id>", methods=["GET"])
def get_card(card_id):
    """Get a specific card."""
    card = store.get_by_id(card_id)
    if not card:
        return jsonify({"error": "Card not found"}), 404
    return jsonify(card.to_dict())


@app.route("/api/cards/<card_id>", methods=["PUT"])
def update_card(card_id):
    """Update an existing card."""
    existing = store.get_by_id(card_id)
    if not existing:
        return jsonify({"error": "Card not found"}), 404

    data = request.json
    for key in ["title", "category", "analysis_text", "model_type", "theme",
                "front_data", "back_text", "card_number", "arabic_terms",
                "steps", "quote", "model_id", "visual_type",
                "visual_type_secondary", "is_islamic_content",
                "islamic_elements", "model_confidence", "matched_model_name",
                "surah_name", "verse_number", "verse_arabic", "verse_english",
                "image_url", "version"]:
        if key in data:
            setattr(existing, key, data[key])

    store.save_card(existing)
    return jsonify(existing.to_dict())


@app.route("/api/cards/<card_id>", methods=["DELETE"])
def delete_card(card_id):
    """Delete a card."""
    store.delete_card(card_id)
    return jsonify({"status": "deleted"})


@app.route("/api/generate-back-text", methods=["POST"])
def generate_back_text():
    """Generate back card text using LLM."""
    data = request.json
    result = generate_back_text_with_llm(
        title=data.get("title", ""),
        category=data.get("category", ""),
        model_type=data.get("model_type", ""),
        steps=data.get("steps", []),
        analysis_text=data.get("analysis_text", "")
    )
    if result:
        return jsonify({"back_text": result})
    return jsonify({"error": "Could not generate text (no API key?)"}), 400


@app.route("/api/generate-image", methods=["POST"])
def generate_image():
    """Generate card image(s) using Gemini image_gen."""
    data = request.json
    mode = data.get("mode", "spread")  # spread, front, or back

    # Set API key: client-provided > server config > env
    google_key = data.get("google_api_key", "") or GOOGLE_AI_API_KEY
    if google_key:
        os.environ["GOOGLE_AI_API_KEY"] = google_key

    if mode == "spread":
        result = generate_card_spread(data)
    elif mode == "front":
        result = generate_card_front(data)
    elif mode == "back":
        result = generate_card_back(data)
    else:
        return jsonify({"error": "Invalid mode. Use: spread, front, back"}), 400

    if result.get("error"):
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/generate-prompt", methods=["POST"])
def generate_prompt():
    """Get the image generation prompt without calling the API."""
    data = request.json
    mode = data.get("mode", "spread")
    prompt = generate_prompt_only(data, mode)
    return jsonify({"prompt": prompt, "mode": mode})


@app.route("/api/generate-custom-image", methods=["POST"])
def generate_custom_image():
    """Generate an image from a raw custom prompt (no prompt building)."""
    data = request.json
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    google_key = data.get("google_api_key", "") or GOOGLE_AI_API_KEY
    if google_key:
        os.environ["GOOGLE_AI_API_KEY"] = google_key

    result = generate_from_custom_prompt(prompt)
    if result.get("error"):
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/refine-image", methods=["POST"])
def refine_image():
    """Refine an existing card image with human-specified tweaks.

    Accepts the card data, the original prompt, and human refinement instructions.
    Generates a new image that preserves the baseline and applies only the requested changes.
    """
    data = request.json
    refinement_instructions = data.get("refinement_instructions", "").strip()
    if not refinement_instructions:
        return jsonify({"error": "Refinement instructions are required"}), 400

    original_prompt = data.get("original_prompt", "")
    original_image_b64 = data.get("original_image_b64", "")

    google_key = data.get("google_api_key", "") or GOOGLE_AI_API_KEY
    if google_key:
        os.environ["GOOGLE_AI_API_KEY"] = google_key

    result = refine_card_image(
        data, refinement_instructions,
        original_prompt or None,
        original_image_b64=original_image_b64 or None
    )
    if result.get("error"):
        return jsonify(result), 400

    # Include the refinement prompt in the response for transparency
    result["refinement_applied"] = refinement_instructions
    return jsonify(result)


@app.route("/api/split-cards", methods=["POST"])
def split_cards():
    """Split a spread image into separate front and back card images
    with transparent backgrounds.

    Accepts either:
      - 'image_b64': base64 data string (data:image/png;base64,...)
      - 'image_path': server file path (e.g. /static/images/spread_new_123.jpg)
    Returns front_b64, back_b64, and dimensions for each.
    """
    data = request.json
    image_b64 = data.get("image_b64", "")
    image_path = data.get("image_path", "")

    if not image_b64 and not image_path:
        return jsonify({"error": "No image provided"}), 400

    try:
        if image_b64:
            result = split_spread_into_cards(image_b64)
        else:
            # Load from file path — strip leading slash, resolve relative to app root
            fpath = image_path.lstrip("/")
            if not os.path.exists(fpath):
                return jsonify({"error": f"Image file not found: {fpath}"}), 400
            result = split_spread_into_cards(fpath)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Split failed: {str(e)}"}), 400


@app.route("/api/themes", methods=["GET"])
def get_themes():
    return jsonify(THEMES)


@app.route("/api/model-types", methods=["GET"])
def get_model_types():
    return jsonify(MODEL_TYPES)


@app.route("/exports/<path:filename>")
def serve_export(filename):
    return send_from_directory(EXPORT_DIR, filename)


@app.route("/api/mental-models", methods=["GET"])
def list_mental_models():
    """List all mental models from repository, with optional category filter."""
    repo = get_model_repository()
    if not repo.is_loaded:
        return jsonify({"error": "Mental models repository not loaded"}), 500

    category = request.args.get("category")
    models = repo.models

    if category:
        models = [m for m in models if m.get("category", "").lower() == category.lower()]

    # Return summary (not full detail) for list view
    summary = []
    for m in models:
        summary.append({
            "id": m["id"],
            "name": m["name"],
            "category": m.get("category", ""),
            "subcategory": m.get("subcategory", ""),
            "description": m.get("description", ""),
            "visual_type": m.get("visual_type", ""),
            "is_quranic": m.get("is_quranic", False),
            "difficulty": m.get("difficulty", ""),
        })

    return jsonify({
        "count": len(summary),
        "categories": repo.categories,
        "models": summary
    })


@app.route("/api/mental-models/<model_id>", methods=["GET"])
def get_mental_model(model_id):
    """Get full details of a specific mental model."""
    repo = get_model_repository()
    if not repo.is_loaded:
        return jsonify({"error": "Mental models repository not loaded"}), 500

    model = repo.get_model(model_id)
    if not model:
        return jsonify({"error": f"Model '{model_id}' not found"}), 404

    return jsonify(model)


@app.route("/api/mental-models/search", methods=["GET"])
def search_mental_models():
    """Search mental models by keyword."""
    repo = get_model_repository()
    if not repo.is_loaded:
        return jsonify({"error": "Mental models repository not loaded"}), 500

    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    results = []
    for m in repo.models:
        # Search across name, description, keywords, category
        searchable = " ".join([
            m.get("name", ""),
            m.get("description", ""),
            m.get("category", ""),
            " ".join(m.get("keywords", [])),
        ]).lower()

        if query in searchable:
            results.append({
                "id": m["id"],
                "name": m["name"],
                "category": m.get("category", ""),
                "description": m.get("description", ""),
                "visual_type": m.get("visual_type", ""),
                "is_quranic": m.get("is_quranic", False),
            })

    return jsonify({"query": query, "count": len(results), "results": results})


@app.route("/api/visual-types", methods=["GET"])
def list_visual_types():
    """List all available visual types."""
    return jsonify(VISUAL_TYPES)


@app.route("/api/style-presets", methods=["GET"])
def get_style_presets():
    """List all available card style presets."""
    return jsonify({
        "presets": list_all_presets(),
        "preset_names": PRESET_NAMES,
    })


@app.route("/api/style-presets/<preset_name>", methods=["GET"])
def get_style_preset(preset_name):
    """Get detailed info about a specific style preset."""
    preset = get_preset(preset_name)
    if preset["name"] == "Classic Sketch" and preset_name != "classic_sketch":
        return jsonify({"error": f"Preset '{preset_name}' not found"}), 404
    return jsonify(preset)


@app.route("/api/images", methods=["GET"])
def list_images():
    """List all generated card images in static/images/."""
    images_dir = os.path.join(os.path.dirname(__file__), "static", "images")
    if not os.path.isdir(images_dir):
        return jsonify([])
    files = sorted([
        f for f in os.listdir(images_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ])
    return jsonify([
        {"filename": f, "url": f"/static/images/{f}"}
        for f in files
    ])


@app.route("/api/evaluate-card", methods=["POST"])
def evaluate_card_content():
    """Evaluate card content quality before image generation."""
    data = request.json
    if not data:
        return jsonify({"error": "No card data provided"}), 400

    result = evaluate_card(data)
    return jsonify(result)


@app.route("/api/evaluate-card/quick", methods=["POST"])
def evaluate_card_quick():
    """Get a quick text summary of card evaluation."""
    data = request.json
    if not data:
        return jsonify({"error": "No card data provided"}), 400

    summary = quick_evaluate(data)
    scores = get_dimension_scores(data)
    return jsonify({
        "summary": summary,
        "dimension_scores": scores,
    })


@app.route("/api/hero-styles", methods=["GET"])
def get_hero_styles():
    """List available hero character styles."""
    styles = {}
    for name in list_hero_styles():
        styles[name] = get_hero_summary(name)
    return jsonify({
        "styles": styles,
        "style_names": list_hero_styles(),
    })


@app.route("/api/hero-styles/<style_name>/poses", methods=["GET"])
def get_hero_poses(style_name):
    """Get available poses for a hero style."""
    poses = list_poses(style_name)
    return jsonify({
        "style": style_name,
        "poses": poses,
    })


@app.route("/api/model-visual/<model_id>", methods=["GET"])
def get_model_visual(model_id):
    """Get visual representation metadata for a matched mental model.

    Returns the model's visual_description and other metadata
    for displaying a concept thumbnail in the analysis UI.
    """
    repo = get_model_repository()
    if not repo.is_loaded:
        return jsonify({"error": "Model repository not loaded"}), 503

    model = repo.get_model(model_id)
    if not model:
        return jsonify({"error": f"Model {model_id} not found"}), 404

    return jsonify({
        "model_id": model_id,
        "name": model.get("name", ""),
        "description": model.get("description", ""),
        "visual_description": model.get("visual_description", ""),
        "visual_type": model.get("visual_type", ""),
    })


@app.route("/api/generate-model-thumbnail", methods=["POST"])
def generate_model_thumbnail():
    """Generate a small thumbnail image for a model's essence/concept.

    Takes model_id and google_api_key, generates a 512x512 thumbnail
    using the model's visual_description via Gemini image generation.
    Returns the image as base64-encoded data.
    """
    data = request.json
    model_id = data.get("model_id", "")
    google_api_key = data.get("google_api_key", "")

    google_api_key = google_api_key or GOOGLE_AI_API_KEY
    if not model_id or not google_api_key:
        return jsonify({"error": "model_id and google_api_key are required"}), 400

    repo = get_model_repository()
    if not repo.is_loaded:
        return jsonify({"error": "Model repository not loaded"}), 503

    model = repo.get_model(model_id)
    if not model:
        return jsonify({"error": f"Model {model_id} not found"}), 404

    visual_description = model.get("visual_description", "")
    if not visual_description:
        return jsonify({"error": f"Model {model_id} has no visual_description"}), 400

    # Set API key and generate thumbnail using existing image generation pipeline
    os.environ["GOOGLE_AI_API_KEY"] = google_api_key

    prompt = (
        f"Simple clean hand-drawn sketch: {visual_description}. "
        f"Minimal black ink on white background. No text labels, no borders. "
        f"Just the concept diagram. Style: clean whiteboard sketch with confident line weight."
    )

    result = generate_from_custom_prompt(prompt)
    if result.get("error"):
        return jsonify(result), 500

    return jsonify({
        "model_id": model_id,
        "image_url": result.get("image_url", ""),
        "image_base64": result.get("image_base64", ""),
        "prompt_used": prompt,
    })


@app.route("/api/quran/verse/<int:surah>/<int:ayah>", methods=["GET"])
def fetch_quran_verse(surah, ayah):
    """Fetch Arabic text and English translation for a specific verse.

    Uses local cache first, then alquran.cloud API as fallback.
    Caches the result for future instant lookups.

    Returns JSON: {arabic, english, surah_name, surah_english, surah_number, ayah_number}
    """
    result = get_verse(surah, ayah)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@app.route("/api/quran/surah/<int:surah>", methods=["GET"])
def fetch_quran_surah(surah):
    """Fetch all verses for an entire surah (Arabic + English).

    More efficient than individual verse lookups — single API call,
    then everything is cached locally for future use.
    """
    result = get_surah_verses(surah)
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 404
    return jsonify({"surah": surah, "count": len(result), "verses": result})


@app.route("/api/quran/cache-stats", methods=["GET"])
def quran_cache_stats():
    """Get statistics about the local Quran verse cache."""
    return jsonify(get_cache_stats())


@app.route("/api/tafsir/<int:surah>/<int:ayah>", methods=["GET"])
def fetch_tafsir(surah, ayah):
    """Fetch Ibn Kathir tafsir for a specific verse."""
    result = get_tafsir(surah, ayah)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@app.route("/api/tafsir/surah/<int:surah>", methods=["GET"])
def fetch_tafsir_surah(surah):
    """Fetch Ibn Kathir tafsir for all verses in a surah (bulk prefetch)."""
    results = get_tafsir_surah(surah)
    return jsonify({"surah": surah, "count": len(results), "verses": results})


@app.route("/api/save-keys", methods=["POST"])
def save_api_keys():
    """Save API keys to .env file for persistence."""
    data = request.json
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    lines = {}
    # Read existing .env
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    lines[k.strip()] = v.strip()
    # Update with new keys
    if data.get("google_api_key"):
        lines["GOOGLE_AI_API_KEY"] = data["google_api_key"]
        os.environ["GOOGLE_AI_API_KEY"] = data["google_api_key"]
    if data.get("anthropic_api_key"):
        lines["ANTHROPIC_API_KEY"] = data["anthropic_api_key"]
        os.environ["ANTHROPIC_API_KEY"] = data["anthropic_api_key"]
    # Write .env
    with open(env_path, "w") as f:
        for k, v in lines.items():
            f.write(f"{k}={v}\n")
    return jsonify({"status": "saved", "has_google_key": bool(lines.get("GOOGLE_AI_API_KEY")),
                     "has_anthropic_key": bool(lines.get("ANTHROPIC_API_KEY"))})


@app.route("/api/key-status", methods=["GET"])
def key_status():
    """Check if API keys are configured."""
    return jsonify({
        "has_google_key": bool(os.environ.get("GOOGLE_AI_API_KEY", "") or GOOGLE_AI_API_KEY),
        "has_anthropic_key": bool(os.environ.get("ANTHROPIC_API_KEY", "")),
    })


@app.route("/api/covers", methods=["GET"])
def list_covers():
    """List all generated surah/category covers."""
    return jsonify(get_all_covers())


@app.route("/api/covers/generate", methods=["POST"])
def generate_cover():
    """Generate a cover image for a surah or category.

    Body: { type: "surah"|"category", number: 1, name: "Al-Fatihah", arabic: "..." }
    Returns: { url: "/static/covers/surah_001.png" }
    """
    data = request.json
    cover_type = data.get("type", "surah")
    google_key = data.get("google_api_key", "") or GOOGLE_AI_API_KEY
    if google_key:
        os.environ["GOOGLE_AI_API_KEY"] = google_key

    if not google_key:
        return jsonify({"error": "Google AI API key required"}), 400

    if cover_type == "surah":
        number = data.get("number", 1)
        name = data.get("name", "")
        arabic = data.get("arabic", "")
        # Check if already generated
        existing = get_cover_url(number)
        if existing:
            return jsonify({"url": existing, "cached": True})
        prompt = build_cover_prompt(number, name, arabic)
    else:
        cat_name = data.get("name", "")
        prompt = build_category_cover_prompt(cat_name)

    try:
        result = generate_from_custom_prompt(prompt)
        if result.get("error"):
            return jsonify(result), 500

        # Save the image
        if cover_type == "surah":
            number = data.get("number", 1)
            b64 = result.get("image_base64") or result.get("base64", "")
            if not b64 and result.get("url"):
                b64 = result["url"]
            url = save_cover(number, b64)
            return jsonify({"url": url, "cached": False})
        else:
            cat_name = data.get("name", "Unknown")
            b64 = result.get("image_base64") or result.get("base64", "")
            if not b64 and result.get("url"):
                b64 = result["url"]
            safe_name = cat_name.lower().replace(" ", "_").replace("&", "and")[:30]
            url = save_cover(f"cat_{safe_name}", b64, f"cat_{safe_name}.png")
            return jsonify({"url": url, "cached": False})

    except Exception as e:
        return jsonify({"error": f"Cover generation failed: {str(e)}"}), 500


@app.route("/api/covers/verse-thumb", methods=["POST"])
def generate_verse_thumbnail():
    """Generate a cinematic thumbnail for a specific verse card.

    Body: { card_id, title, category, back_text, verse_english, verse_ref }
    Returns: { url: "/static/covers/verse_abc123.png" }
    """
    data = request.json
    card_id = data.get("card_id", "")
    if not card_id:
        return jsonify({"error": "card_id required"}), 400

    # Check if already generated
    existing = get_verse_thumb_url(card_id)
    if existing:
        return jsonify({"url": existing, "cached": True})

    google_key = data.get("google_api_key", "") or GOOGLE_AI_API_KEY
    if google_key:
        os.environ["GOOGLE_AI_API_KEY"] = google_key
    if not google_key:
        return jsonify({"error": "Google AI API key required"}), 400

    prompt = build_verse_thumb_prompt(
        card_title=data.get("title", ""),
        verse_ref=data.get("verse_ref", ""),
        category=data.get("category", ""),
        back_text=data.get("back_text", ""),
        verse_english=data.get("verse_english", ""),
    )

    try:
        result = generate_from_custom_prompt(prompt)
        if result.get("error"):
            return jsonify(result), 500

        b64 = result.get("image_base64") or result.get("base64", "")
        if not b64 and result.get("url"):
            b64 = result["url"]
        url = save_verse_thumb(card_id, b64)
        return jsonify({"url": url, "cached": False})
    except Exception as e:
        return jsonify({"error": f"Thumbnail generation failed: {str(e)}"}), 500


@app.route("/api/covers/surah-visuals", methods=["GET"])
def list_surah_visuals():
    """List all 114 surahs with their visual descriptions for cover generation."""
    from surah_covers import SURAH_VISUALS
    return jsonify(SURAH_VISUALS)


if __name__ == "__main__":
    print("\n  Quran Visual Cards Pipeline")
    print(f"  Running at http://localhost:{PORT}\n")
    app.run(host=HOST, port=PORT, debug=DEBUG)
