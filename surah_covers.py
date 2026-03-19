"""Surah cover image generation for gallery thumbnails.

Generates cinematic digital art covers for each surah based on
its title meaning, themes, and narrative content. Uses Gemini
image generation with Islamic guardrails.

Covers are cached as files in static/covers/ for instant loading.
"""
import os
import json
import base64
from datetime import datetime

COVERS_DIR = os.path.join(os.path.dirname(__file__), "static", "covers")
COVERS_INDEX = os.path.join(COVERS_DIR, "index.json")

os.makedirs(COVERS_DIR, exist_ok=True)


def _load_index():
    if os.path.exists(COVERS_INDEX):
        with open(COVERS_INDEX, "r") as f:
            return json.load(f)
    return {}


def _save_index(idx):
    with open(COVERS_INDEX, "w") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)


def get_cover_url(surah_number):
    """Get the URL for a surah cover if it exists."""
    idx = _load_index()
    key = str(surah_number)
    if key in idx:
        return idx[key].get("url")
    return None


def get_all_covers():
    """Get all generated covers as {surah_number: url}."""
    idx = _load_index()
    return {k: v.get("url") for k, v in idx.items() if v.get("url")}


def save_cover(surah_number, image_data, filename=None):
    """Save a generated cover image and update index."""
    if not filename:
        filename = f"surah_{surah_number:03d}.png"
    filepath = os.path.join(COVERS_DIR, filename)

    # Handle base64 data
    if image_data.startswith("data:"):
        # Strip data URI prefix
        b64 = image_data.split(",", 1)[1]
    else:
        b64 = image_data

    with open(filepath, "wb") as f:
        f.write(base64.b64decode(b64))

    url = f"/static/covers/{filename}"
    idx = _load_index()
    idx[str(surah_number)] = {
        "url": url,
        "filename": filename,
        "generated_at": datetime.now().isoformat(),
    }
    _save_index(idx)
    return url


# ============================================
# SURAH VISUAL DESCRIPTIONS
# Each surah has a creative visual concept for its cover image
# ============================================
SURAH_VISUALS = {
    1: {"en": "The Opening", "visual": "A grand white marble mosque interior with soaring arches and golden light streaming through ornate windows, a lone figure in white praying on a luminous prayer mat, divine light rays converging from above"},
    2: {"en": "The Cow", "visual": "A majestic golden-brown cow standing in a lush green meadow at golden hour, ancient Middle Eastern landscape behind with rolling hills, warm cinematic sunset lighting"},
    3: {"en": "The Family of Imran", "visual": "An ancient noble family gathered in a grand courtyard with Islamic arches and gardens, soft golden light, the atmosphere of devotion and legacy, warm tones"},
    4: {"en": "The Women", "visual": "A group of dignified women in flowing garments walking through a beautiful Islamic garden with fountains and jasmine flowers, empowering composition, golden hour light"},
    5: {"en": "The Spread Table", "visual": "A magnificent feast table descending from golden clouds, laden with bread and fruits, set in a desert landscape, miraculous divine provision, cinematic warm light"},
    6: {"en": "The Cattle", "visual": "A herd of noble cattle grazing on vast green plains under a dramatic sky with golden clouds, ancient Arabian landscape, epic wide-angle cinematic shot"},
    7: {"en": "The Heights", "visual": "A dramatic elevated ridge between two vast landscapes — paradise gardens on one side, barren wasteland on the other, a figure standing at the pinnacle, epic scale"},
    8: {"en": "The Spoils of War", "visual": "An ancient battlefield at dawn with golden light breaking through dramatic clouds, scattered banners and shields on sand, atmosphere of divine victory"},
    9: {"en": "The Repentance", "visual": "A lone traveler kneeling in a vast desert at dawn, hands raised in supplication, golden light breaking through storm clouds above, emotional spiritual atmosphere"},
    10: {"en": "Jonah", "visual": "A massive whale swimming through deep turquoise ocean, shafts of golden sunlight penetrating the water from above, underwater cinematic shot, awe-inspiring scale"},
    11: {"en": "Hud", "visual": "Ancient towering cliff dwellings carved into red sandstone, a prophet figure standing before them, dramatic storm clouds gathering, epic archaeological landscape"},
    12: {"en": "Joseph", "visual": "A deep ancient stone well in a golden desert with a caravan of camels silhouetted against a magnificent sunset, a bright star shining above, cinematic desert epic"},
    13: {"en": "The Thunder", "visual": "Dramatic lightning bolts striking across a vast desert sky, thunder clouds illuminated from within by golden light, a lone tree standing resilient, raw power of nature"},
    14: {"en": "Abraham", "visual": "The Kaaba in Mecca under a dramatic golden sunset sky with towering clouds, the ancient cubic structure with its black cloth, majestic and awe-inspiring, no people shown"},
    15: {"en": "The Rocky Tract", "visual": "Ancient carved rock formations in a dramatic desert canyon, reminiscent of Petra or Mada'in Saleh, golden hour light casting long shadows, archaeological wonder"},
    16: {"en": "The Bee", "visual": "A detailed close-up of honeybees on a honeycomb with golden honey dripping, surrounded by wildflowers and blossoms, warm macro photography style, nature's miracle"},
    17: {"en": "The Night Journey", "visual": "A luminous winged celestial horse (Buraq) soaring through a starlit night sky with a crescent moon, streaks of light trailing behind, cosmic spiritual journey"},
    18: {"en": "The Cave", "visual": "A mysterious cave entrance with golden light streaming in, silhouettes of sleeping figures inside, lush vines growing around the entrance, mystical atmosphere"},
    19: {"en": "Mary", "visual": "A serene palm tree in a peaceful oasis with a spring of water at its base, soft divine light from above, dates hanging from branches, tranquil sacred atmosphere"},
    20: {"en": "Ta-Ha", "visual": "A burning bush on a mountainside at night, emitting golden-white divine light, a lone figure approaching with staff in hand, Mount Sinai, sacred moment"},
    21: {"en": "The Prophets", "visual": "A grand assembly of noble figures standing together on a mountaintop at golden hour, silhouetted against a magnificent sky, unity of prophetic mission"},
    22: {"en": "The Pilgrimage", "visual": "Aerial view of pilgrims circumambulating a sacred site at golden hour, wearing white garments, forming concentric circles, spiritual unity, warm tones"},
    23: {"en": "The Believers", "visual": "A group of devoted worshippers standing in humble prayer at dawn, golden light washing over them, mosque silhouette in background, spiritual serenity"},
    24: {"en": "The Light", "visual": "A magnificent crystal lamp in an ornate niche radiating brilliant golden-white light that fills the entire frame, Islamic geometric patterns in the light rays"},
    25: {"en": "The Criterion", "visual": "A great luminous book open in the sky splitting darkness and light, one side golden and radiant, the other side shadowed, cosmic scale of truth vs falsehood"},
    26: {"en": "The Poets", "visual": "An elegant Arabic calligraphy quill writing flowing golden text on ancient parchment, ink drops forming beautiful patterns, scholarly artistic atmosphere"},
    27: {"en": "The Ant", "visual": "A detailed cinematic shot of organized ants forming intricate patterns on golden desert sand, with a vast kingdom visible in the background, micro-to-macro perspective"},
    28: {"en": "The Stories", "visual": "An ancient open scroll unfurling across a dramatic landscape, with scenes from different eras visible within, golden light illuminating the narrative, epic storytelling"},
    29: {"en": "The Spider", "visual": "An intricate spider web glistening with morning dew drops that catch golden sunlight like jewels, delicate yet fragile, a metaphor rendered beautifully in nature"},
    30: {"en": "The Romans", "visual": "Ancient Roman-style ruins and columns at sunset, dramatic sky with golden clouds, the rise and fall of empires captured in one cinematic frame"},
    31: {"en": "Luqman", "visual": "A wise elderly figure sitting under a great ancient tree teaching a young child, warm golden light filtering through leaves, intimate moment of wisdom transfer"},
    32: {"en": "The Prostration", "visual": "A lone figure in deep prostration (sujud) on a prayer mat, forehead touching ground, in a vast empty mosque with golden light streaming in from above"},
    33: {"en": "The Combined Forces", "visual": "A fortified ancient city with defensive trenches at sunset, dramatic clouds and wind, banners flying, atmosphere of steadfast resilience against overwhelming odds"},
    34: {"en": "Sheba", "visual": "A magnificent ancient palace with lush hanging gardens and flowing water channels in a desert setting, Queen of Sheba's legendary kingdom, golden opulence"},
    35: {"en": "Originator", "visual": "A cosmic scene of creation — galaxies, nebulae, and stars being formed in swirling golden and deep blue cosmic dust, divine creative power at universal scale"},
    36: {"en": "Ya-Sin (Heart of Quran)", "visual": "A radiant heart made of golden light pulsing at the center of an open Quran, the pages glowing with divine energy, the spiritual core, warm ethereal light"},
    37: {"en": "Those Lined Up", "visual": "Rows of luminous angelic figures standing in perfect formation against a cosmic starfield, golden light emanating from their forms, celestial army, awe-inspiring"},
    38: {"en": "Sad", "visual": "King David (Dawud) seated on a golden throne in a magnificent court, holding a glowing psalm scroll, mountains and nature bowing around him, royal divine authority"},
    39: {"en": "The Groups", "visual": "Two distinct groups of people walking toward different horizons — one toward golden light and gardens, one toward darkness, dramatic sky, fate divergence"},
    40: {"en": "The Forgiver", "visual": "A vast ocean of divine mercy represented as golden light flooding through parting storm clouds over a darkened landscape, overwhelming forgiveness, cinematic scale"},
    41: {"en": "Explained in Detail", "visual": "An intricate unfurling golden scroll with detailed Arabic calligraphy, layers upon layers of revealed wisdom, warm scholarly atmosphere with candlelight"},
    42: {"en": "The Consultation", "visual": "A circle of wise figures seated in an ornate council chamber having deep discussion, warm lamp light, Islamic architectural arches, democratic deliberation"},
    43: {"en": "The Gold Adornments", "visual": "Magnificent golden ornate Islamic geometric decorations and arabesque patterns cascading through space, luxurious yet ultimately temporal beauty, opulent warm tones"},
    44: {"en": "The Smoke", "visual": "A dramatic sky filled with ominous golden-gray smoke over a vast landscape, sun barely visible through the haze, foreboding yet cinematic atmosphere"},
    45: {"en": "The Kneeling", "visual": "A vast crowd of humanity kneeling on a white plain under a cosmic sky, the Day of Judgment atmosphere, dramatic golden light breaking through, humbling scale"},
    46: {"en": "The Sand Dunes", "visual": "Massive golden sand dunes in the Arabian Empty Quarter under a dramatic sky, wind carrying sand across the peaks, ancient civilization remnants barely visible"},
    47: {"en": "Muhammad", "visual": "The green dome of the Prophet's Mosque in Medina at golden hour, birds circling above, warm reverent light, the city of the Prophet, no human figures"},
    48: {"en": "The Victory", "visual": "A great city gate opening wide with golden light flooding through, victorious banners waving, olive branches and peace, the conquest of Mecca atmosphere"},
    49: {"en": "The Dwellings", "visual": "A beautiful Islamic courtyard with multiple rooms, gardens, and gathering spaces, community life, warm golden afternoon light, architectural harmony"},
    50: {"en": "Qaf", "visual": "A vast cosmic landscape with towering mountains under a canopy of stars, the letter Qaf glowing in golden Arabic calligraphy against the sky, creation's grandeur"},
    51: {"en": "The Scattering Winds", "visual": "Powerful winds scattering golden desert sand into dramatic spiral patterns across a vast landscape, forces of nature in cinematic motion, raw atmospheric power"},
    52: {"en": "The Mount", "visual": "Mount Sinai at dawn, the peak shrouded in luminous golden clouds, a path leading upward through rocky terrain, sacred mountain, epic landscape photography"},
    53: {"en": "The Star", "visual": "A single brilliant star falling through a deep cosmic sky, trailing golden light, the Pleiades visible in background, astronomical wonder, cosmic revelation"},
    54: {"en": "The Moon", "visual": "A dramatic full moon splitting in two against a starfield sky, golden light emanating from the split, one of the great signs, supernatural cosmic event"},
    55: {"en": "The Most Merciful", "visual": "An infinite garden of paradise with flowing rivers, fruit trees, and flowers in impossible colors, golden light everywhere, ultimate divine beauty and mercy"},
    56: {"en": "The Inevitable Event", "visual": "A cosmic cataclysm — mountains crumbling like wool, stars scattered, earth shaking, all rendered in dramatic cinematic golden and deep purple tones, Day of Judgment"},
    57: {"en": "The Iron", "visual": "A meteorite of glowing iron descending through Earth's atmosphere, trailing fire and golden light, cosmic origin of iron, dramatic space-to-earth perspective"},
    58: {"en": "The Pleading Woman", "visual": "A dignified woman standing before a council, pleading her case with raised hands, golden light behind her, justice being sought, powerful emotional composition"},
    59: {"en": "The Exile", "visual": "A group departing through a fortified city gate at dawn, carrying belongings, dramatic golden sky, the departure and exile, emotional cinematic wide shot"},
    60: {"en": "The Woman Examined", "visual": "A solemn ceremony of covenant — hands clasped in oath under golden light, symbolic of allegiance and truth, sacred trust between people, warm atmosphere"},
    61: {"en": "The Ranks", "visual": "Rows of steadfast soldiers standing like a solid structure, shields forming a wall, golden light behind them, unity as strong as reinforced concrete"},
    62: {"en": "Friday", "visual": "A magnificent mosque at Friday prayer time, golden minaret against blue sky, crowds gathering, the blessed day, warm community atmosphere, aerial perspective"},
    63: {"en": "The Hypocrites", "visual": "A figure with two faces — one golden and welcoming, one shadowed and hidden, a dramatic split-composition showing duality and deception, cinematic contrast"},
    64: {"en": "The Mutual Disillusion", "visual": "Two groups facing each other across a vast plain on Judgment Day, one in golden light one in shadow, the day of taghabun, dramatic cosmic atmosphere"},
    65: {"en": "The Divorce", "visual": "Two paths diverging in a desert landscape at sunset, a shared tent behind, separate journeys ahead, bittersweet golden light, transition and trust in God"},
    66: {"en": "The Prohibition", "visual": "A sealed golden vessel with divine light escaping from its edges, the concept of what is forbidden and permitted, mysterious sacred atmosphere"},
    67: {"en": "The Sovereignty", "visual": "A magnificent crown hovering above the Earth seen from space, golden light radiating outward, seven heavens layered above, cosmic divine dominion"},
    68: {"en": "The Pen", "visual": "A grand cosmic quill writing destiny in golden ink across the tablet of the heavens, stars forming Arabic letters, the first creation, celestial calligraphy"},
    69: {"en": "The Inevitable", "visual": "A colossal wave of golden energy sweeping across the horizon, unstoppable force, the Day that must come, dramatic scale showing human smallness against divine power"},
    70: {"en": "The Ways of Ascent", "visual": "A spiraling staircase of golden light ascending through the clouds into infinite sky, angels ascending and descending, cosmic vertical journey, breathtaking height"},
    71: {"en": "Noah", "visual": "A massive wooden ark on turbulent dark waters under dramatic stormy sky, a break in the clouds showing golden light and a rainbow, hope amid catastrophe"},
    72: {"en": "The Jinn", "visual": "Ethereal translucent figures made of smokeless fire gathered in a dark forest, listening intently, flickering golden and blue flame-like forms, supernatural atmosphere"},
    73: {"en": "The Enshrouded One", "visual": "A figure wrapped in a cloak standing in prayer during deep night, a single lamp illuminating golden, stars visible through a window, nighttime devotion"},
    74: {"en": "The Cloaked One", "visual": "A figure rising wrapped in a grand cloak, standing on a mountaintop at dawn, the moment of receiving the mission, golden light breaking over the horizon"},
    75: {"en": "The Resurrection", "visual": "Human forms rising from the earth toward a brilliant sky of golden light, cosmic scale resurrection scene, dramatic upward movement, awe and accountability"},
    76: {"en": "The Human", "visual": "The stages of human creation — from water drop to full form — shown as a beautiful progression in golden light, the miracle of human existence, artistic anatomy"},
    77: {"en": "Those Sent Forth", "visual": "Powerful winds of different kinds sent across diverse landscapes — gentle breezes and fierce storms — all controlled by divine command, atmospheric drama"},
    78: {"en": "The Great News", "visual": "A cosmic herald trumpet floating in space above Earth, golden light pulsing from it, the announcement that changes everything, dramatic scale"},
    79: {"en": "Those Who Pull Out", "visual": "Angels in the form of golden light extracting souls upward from the earth into cosmic heights, dramatic vertical composition, spiritual transition"},
    80: {"en": "He Frowned", "visual": "A blind man walking with confidence and dignity in golden light while others turn away, the true honor is piety not status, emotional character study"},
    81: {"en": "The Folding Up", "visual": "The sun being folded and dimmed, stars falling like scattered pearls, oceans overflowing, all cosmic signs of the end, dramatic apocalyptic cinematography"},
    82: {"en": "The Breaking Apart", "visual": "The sky literally cracking open like shattered glass with golden light flooding through the cracks, cosmic rupture, breathtaking supernatural event"},
    83: {"en": "The Defrauders", "visual": "A golden balance scale with one side deliberately tampered, set against a dark judicial background, the injustice of cheating in measure, dramatic contrast"},
    84: {"en": "The Splitting", "visual": "The Earth splitting open and yielding what is within, golden light emerging from the cracks, mountains flattened on the horizon, dramatic geological upheaval"},
    85: {"en": "The Great Stars", "visual": "Magnificent constellations of the zodiac burning bright in a deep cosmic sky, each star a brilliant golden point, the celestial vault in its full glory"},
    86: {"en": "The Night Visitor", "visual": "A single piercing star shining through the night sky like a cosmic beacon, its light penetrating through layers of darkness, the morning star, intimate cosmic scale"},
    87: {"en": "The Most High", "visual": "Looking upward from a deep canyon toward infinite golden sky, the perspective showing human smallness and divine vastness, vertical awe composition"},
    88: {"en": "The Overwhelming", "visual": "A dramatic scene showing two contrasting fates side by side — scorching fire on one side, cool paradise gardens on the other, golden dividing line between"},
    89: {"en": "The Dawn", "visual": "A spectacular desert dawn with golden-pink light breaking over ancient ruins (Iram of the Pillars), the beauty and warning of first light, epic wide shot"},
    90: {"en": "The City", "visual": "An ancient city (Mecca) nestled in a valley between rugged mountains, warm golden light, the sacred birthplace, aerial cinematic perspective"},
    91: {"en": "The Sun", "visual": "A glorious golden sun rising over a vast desert landscape, its rays creating long dramatic shadows, the oath by the sun and its brightness, pure radiance"},
    92: {"en": "The Night", "visual": "A deep velvet night sky with a crescent moon and scattered stars over a sleeping desert landscape, peaceful yet profound darkness, nocturnal beauty"},
    93: {"en": "The Morning Brightness", "visual": "The warm golden light of mid-morning (duha time) flooding through clouds after a dark night, promise and hope returning, emotional sunrise composition"},
    94: {"en": "The Expansion", "visual": "A chest opening with golden light radiating outward, a heavy burden being lifted and floating away, the relief after hardship, spiritual liberation"},
    95: {"en": "The Fig", "visual": "A ripe fig tree with lush fruit against a backdrop of Mount Sinai and olive trees, the sacred oaths by creation, Mediterranean botanical beauty, warm light"},
    96: {"en": "The Clinging Clot", "visual": "A cosmic scene of creation — a luminous cell of life forming in golden divine light, the first moment of human existence, microscopic-to-cosmic scale"},
    97: {"en": "The Night of Power", "visual": "A night sky more brilliant than a thousand moons, angels descending as streams of golden light through the atmosphere, the most powerful night, celestial splendor"},
    98: {"en": "The Clear Evidence", "visual": "A luminous golden scroll unrolling with clear divine words, cutting through darkness and confusion like a beam of truth, scholarly sacred atmosphere"},
    99: {"en": "The Earthquake", "visual": "The Earth shaking and splitting with golden light emerging from within, revealing all hidden deeds, dramatic seismic event with supernatural golden undertones"},
    100: {"en": "The War Horses", "visual": "Powerful horses charging at dawn, hooves striking sparks from rocky ground, dust and golden morning light, the raw energy of creation in motion"},
    101: {"en": "The Striking Hour", "visual": "Mountains scattering like carded wool in the wind, dramatic golden-red sky, the catastrophe that strikes, cosmic destruction rendered beautifully"},
    102: {"en": "The Rivalry in Worldly Increase", "visual": "Golden coins and treasures piling endlessly but dissolving into dust, the futility of material competition, dramatic vanitas still-life composition"},
    103: {"en": "The Time", "visual": "A magnificent golden hourglass with sand flowing, set against a cosmic backdrop of spinning galaxies, time passing for all humanity, philosophical scale"},
    104: {"en": "The Slanderer", "visual": "A figure hoarding gold in a dark vault while fire creeps in from all sides, the trap of wealth and slander, dramatic chiaroscuro lighting, cautionary"},
    105: {"en": "The Elephant", "visual": "A massive war elephant in golden battle armor approaching an ancient city, but flocks of birds carrying small stones darken the sky above, epic confrontation"},
    106: {"en": "Quraysh", "visual": "A prosperous trade caravan traveling through desert at golden hour, loaded camels in a long line, ancient commercial routes, warm amber atmosphere"},
    107: {"en": "The Small Kindnesses", "visual": "A pair of hands offering a simple bowl of water to someone in need, golden warm light, the beauty of small acts of charity, intimate close-up composition"},
    108: {"en": "The Abundance", "visual": "An infinite river of golden shimmering water flowing through paradise gardens, abundance beyond measure, al-Kawthar, breathtaking celestial landscape"},
    109: {"en": "The Disbelievers", "visual": "Two distinct paths diverging at a crossroads in dramatic golden light, clear separation of ways, each path leading to a different horizon, decisive moment"},
    110: {"en": "The Victory", "visual": "Massive crowds entering through a grand gate in waves, triumphant golden light overhead, the final victory, aerial perspective showing the magnitude"},
    111: {"en": "The Palm Fiber", "visual": "Dried twisted palm fiber rope against a background of flames, the consequence of opposition to truth, dramatic fire and texture, stark warning"},
    112: {"en": "The Sincerity", "visual": "A single perfect golden sphere of light radiating in all directions against a cosmic void, absolute divine unity (tawhid), pure and undivided, the essence"},
    113: {"en": "The Daybreak", "visual": "First light of dawn breaking over a dark landscape, golden rays piercing through and dissolving shadows and evil, the protective light of the Creator"},
    114: {"en": "Mankind", "visual": "A vast crowd of diverse humanity gathered on an open plain under a cosmic sky, united in their need for divine protection, epic human scale"},
}


def get_surah_visual(surah_number):
    """Get the visual description for a surah cover."""
    return SURAH_VISUALS.get(surah_number, {})


def build_cover_prompt(surah_number, surah_name_en, surah_name_ar=""):
    """Build a prompt for generating a surah cover image."""
    vis = SURAH_VISUALS.get(surah_number, {})
    en_meaning = vis.get("en", surah_name_en)
    visual_desc = vis.get("visual", f"A beautiful cinematic scene representing the theme of {en_meaning}")

    prompt = (
        f"Create a cinematic digital art image representing the theme of Surah {surah_name_en} — \"{en_meaning}\".\n\n"
        f"VISUAL CONCEPT:\n{visual_desc}\n\n"
        f"ART STYLE (CRITICAL):\n"
        f"- High-end cinematic digital art, premium quality like a movie poster backdrop\n"
        f"- Rich warm color palette: golden amber, deep navy, warm earth tones\n"
        f"- Dramatic golden hour / divine light atmosphere\n"
        f"- Photorealistic details with painterly artistic touches\n"
        f"- PORTRAIT aspect ratio (3:4, taller than wide)\n\n"
        f"ISLAMIC GUARDRAILS:\n"
        f"- NEVER depict the face of any Prophet, the Prophet Muhammad, or God/Allah\n"
        f"- Prophets shown as silhouettes, from behind, or face hidden by light\n"
        f"- No idols or shirk imagery. Maintain reverence and dignity.\n\n"
        f"CRITICAL — NO TEXT IN THE IMAGE:\n"
        f"- Do NOT render ANY text, titles, labels, chapter numbers, or words in the image\n"
        f"- The image must be PURELY VISUAL — no typography, no letters, no numbers\n"
        f"- Text will be overlaid separately via CSS — the image is just the background artwork\n"
        f"- If you add ANY text to the image, the result is WRONG\n\n"
        f"OUTPUT: Single portrait image (3:4), high resolution, cinematic. NO TEXT."
    )
    return prompt


def build_verse_thumb_prompt(card_title, verse_ref, category, back_text="", verse_english=""):
    """Build a prompt for generating a verse card thumbnail image.

    Creates a cinematic cover thumbnail consistent with surah cover style,
    based on the card's title, category, and back text content.
    """
    theme_hint = ""
    if back_text:
        theme_hint = back_text[:200].replace("**", "").strip()

    verse_context = ""
    if verse_english:
        verse_context = f"The verse says: \"{verse_english[:150]}...\"\n"

    prompt = (
        f"Create a cinematic digital art image representing a Quranic concept.\n\n"
        f"CONCEPT: \"{card_title}\"\n"
        f"CATEGORY: {category}\n"
        f"{verse_context}"
        f"THEMATIC CONTEXT: {theme_hint}\n\n"
        f"VISUAL DIRECTION:\n"
        f"- Create a symbolic, metaphorical scene that captures the spiritual essence of this concept\n"
        f"- The image should feel like a premium movie poster or book cover for this specific verse's theme\n"
        f"- Use symbolic imagery: if about guidance, show a path with light; "
        f"if about patience, show endurance; if about mercy, show rain on dry earth; etc.\n\n"
        f"ART STYLE (MUST MATCH — same style as other gallery covers):\n"
        f"- High-end cinematic digital art, premium quality\n"
        f"- Rich warm color palette: golden amber, deep navy, warm earth tones\n"
        f"- Dramatic golden hour / divine light atmosphere\n"
        f"- Photorealistic details with painterly artistic touches\n"
        f"- PORTRAIT aspect ratio (3:4, taller than wide)\n\n"
        f"ISLAMIC GUARDRAILS:\n"
        f"- NEVER depict the face of any Prophet or God/Allah\n"
        f"- Use symbolism and metaphor. Maintain reverence and dignity.\n\n"
        f"CRITICAL — NO TEXT IN THE IMAGE:\n"
        f"- Do NOT render ANY text, titles, labels, or words\n"
        f"- PURELY VISUAL — no typography whatsoever\n"
        f"- If you add ANY text, the result is WRONG\n\n"
        f"OUTPUT: Single portrait image (3:4), high resolution, cinematic. NO TEXT."
    )
    return prompt


def get_verse_thumb_url(card_id):
    """Get the URL for a verse card thumbnail if it exists."""
    idx = _load_index()
    key = f"verse_{card_id}"
    if key in idx:
        return idx[key].get("url")
    return None


def save_verse_thumb(card_id, image_data):
    """Save a generated verse thumbnail and update index."""
    filename = f"verse_{card_id}.png"
    filepath = os.path.join(COVERS_DIR, filename)

    if image_data.startswith("data:"):
        b64 = image_data.split(",", 1)[1]
    else:
        b64 = image_data

    with open(filepath, "wb") as f:
        f.write(base64.b64decode(b64))

    url = f"/static/covers/{filename}"
    idx = _load_index()
    idx[f"verse_{card_id}"] = {
        "url": url,
        "filename": filename,
        "generated_at": datetime.now().isoformat(),
    }
    _save_index(idx)
    return url


# Category cover descriptions
CATEGORY_VISUALS = {
    "Tawhid & Worship": "A majestic mosque interior with golden light streaming through geometric windows, lone worshipper in prostration, divine unity concept",
    "Prophecy & Messengers": "Ancient scrolls unrolling with golden prophetic light, a chain of messengers represented as connected stars across a cosmic sky",
    "Moral & Ethical": "A grand golden balance scale perfectly balanced on a mountain peak at sunrise, justice and righteousness, dramatic ethical symbolism",
    "Afterlife & Accountability": "A cosmic courtyard with golden gates opening to reveal brilliant paradise light, while below a dramatic abyss, the two destinies",
    "Faith & Belief": "A glowing heart radiating golden light in a person's chest, visible through translucent form, spiritual faith made visible, warm ethereal",
    "Guidance & Wisdom": "A magnificent golden lantern illuminating a path through darkness, Quran as the ultimate guide, warm scholarly atmosphere with ancient books",
    "Social & Community": "A diverse group of hands interlocked in a circle from above, unity in diversity, warm golden light binding them, community strength",
    "Patience & Perseverance": "A lone tree standing strong on a windswept cliff, roots deep in rock, golden sunset behind, endurance against all odds, inspiring resilience",
    "Repentance & Forgiveness": "Rain falling on parched desert earth that's beginning to bloom with flowers, divine mercy washing away sins, renewal and hope, golden rain",
    "Creation & Nature": "The Milky Way galaxy visible over a pristine natural landscape with mountains and rivers, golden cosmic dust, the signs of creation everywhere",
    "Psychology & Human Nature": "A luminous human silhouette with visible internal light and shadow, the struggle of nafs, self-knowledge, warm golden inner light emerging",
    "Economics & Provision": "Golden wheat fields stretching to the horizon with divine light breaking through clouds, rizq (provision) from Allah, abundance and gratitude",
}


def build_category_cover_prompt(category_name):
    """Build a prompt for generating a category cover image."""
    visual_desc = CATEGORY_VISUALS.get(
        category_name,
        f"A beautiful cinematic scene representing the Islamic concept of {category_name}"
    )

    prompt = (
        f"Create a cinematic digital art image representing the Islamic concept of \"{category_name}\".\n\n"
        f"VISUAL CONCEPT:\n{visual_desc}\n\n"
        f"ART STYLE:\n"
        f"- High-end cinematic digital art, premium quality\n"
        f"- Rich warm color palette: golden amber, deep navy, earth tones\n"
        f"- Dramatic golden hour / divine light atmosphere\n"
        f"- PORTRAIT aspect ratio (3:4, taller than wide)\n\n"
        f"ISLAMIC GUARDRAILS:\n"
        f"- Never depict face of any Prophet or God/Allah\n"
        f"- Use symbolism and metaphor. Maintain reverence.\n\n"
        f"CRITICAL — NO TEXT IN THE IMAGE:\n"
        f"- Do NOT render ANY text, titles, labels, or words in the image\n"
        f"- The image must be PURELY VISUAL — no typography whatsoever\n"
        f"- Text will be overlaid via CSS separately\n"
        f"- If you add ANY text, the result is WRONG\n\n"
        f"OUTPUT: Single portrait image (3:4), high resolution, cinematic. NO TEXT."
    )
    return prompt
