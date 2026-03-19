"""Islamic Design Guardrails for Quran Visual Cards

Encapsulates all Islamic art principles, prohibited imagery rules,
and prompt injection logic for AI image generation compliance.
"""

# ═══════════════════════════════════════════════════════════════
# FORBIDDEN DEPICTIONS — NEVER include in any generated imagery
# ═══════════════════════════════════════════════════════════════

FORBIDDEN_DEPICTIONS = [
    "prophets with detailed facial features or realistic face details",
    "Allah or God depicted as a human figure or any living form",
    "three-dimensional sculptures or statues of living beings",
    "any imagery that could encourage veneration or idolatry",
    "realistic animal faces as primary religious subject",
    "Christian or non-Islamic religious symbols in Quranic content",
    "irreverent or disrespectful treatment of sacred text",
]

# ═══════════════════════════════════════════════════════════════
# APPROVED SUBSTITUTIONS — use these INSTEAD of prohibited imagery
# ═══════════════════════════════════════════════════════════════

PROPHET_SUBSTITUTIONS = [
    "radiant light emanation (noor / نور) — glowing luminous form",
    "silhouette without facial detail, outlined in golden light",
    "ascending luminous figure with light halo/aureole",
    "abstract form surrounded by divine light rays",
    "back-view figure with no facial features visible",
    "calligraphic text naming the prophet instead of figure",
]

DIVINE_SUBSTITUTIONS = [
    "Arabic calligraphy of Allah (الله) in Thuluth or Kufic script",
    "Islamic geometric star patterns representing divine order",
    "golden light rays emanating from above (divine presence)",
    "intricate arabesque patterns symbolizing infinite divine nature",
    "99 Names calligraphy (Al-Rahman, Al-Rahim, etc.)",
    "geometric tessellation representing mathematical perfection of creation",
]

PEOPLE_SUBSTITUTIONS = [
    "regular humans: simple cartoon faces with dot eyes and smile lines — friendly, approachable",
    "back-view figures with no facial detail (for intimate/private moments)",
    "abstract human forms as simple outlines",
    "light/shadow representations without features",
    "hands-only depictions (raised in dua, working, etc.)",
    "footprints or shadows suggesting human presence",
]

# ═══════════════════════════════════════════════════════════════
# ISLAMIC COLOR PALETTE — sacred color symbolism
# ═══════════════════════════════════════════════════════════════

ISLAMIC_COLORS = {
    "green": {
        "hex": "#27A359",
        "meaning": "Paradise (Jannah) — mentioned in Quran as color of paradise garments",
        "usage": "Primary accent for paradise/afterlife themes",
    },
    "gold": {
        "hex": "#FFD700",
        "meaning": "Divine light and wisdom — represents enlightenment and sacred nature",
        "usage": "Sacred text highlighting, divine presence, calligraphy accents",
    },
    "blue": {
        "hex": "#1E3A8A",
        "meaning": "Heavens and transcendence — depth of the universe",
        "usage": "Background elements, secondary accents, spiritual transcendence",
    },
    "white": {
        "hex": "#FFFFFF",
        "meaning": "Purity, cleanliness, sacredness — simplicity and humility",
        "usage": "Clean backgrounds, supporting color, clarity",
    },
    "cream": {
        "hex": "#FDF3E0",
        "meaning": "Parchment — tradition, scholarship, ancient knowledge",
        "usage": "Card backgrounds for warm/Quranic themes",
    },
    "deep_brown": {
        "hex": "#4A2E0A",
        "meaning": "Earth, grounding — natural and organic",
        "usage": "Text color, outlines on warm parchment cards",
    },
}

# ═══════════════════════════════════════════════════════════════
# ISLAMIC VISUAL ELEMENTS — approved symbols and motifs
# ═══════════════════════════════════════════════════════════════

ISLAMIC_VISUAL_ELEMENTS = [
    "Islamic geometric star patterns (6-point, 8-point, 12-point stars)",
    "arabesque designs (flowing intertwined plant and vine motifs)",
    "crescent moon symbol",
    "mosque dome and minaret silhouettes",
    "prayer mat with prayer direction indicator",
    "Quran/book with ornate cover",
    "lanterns (traditional Islamic lamp designs)",
    "Islamic arch (pointed horseshoe arch)",
    "calligraphic bismillah or verse fragments",
    "tessellating geometric tile patterns",
    "mihrab (prayer niche) silhouette",
    "tasbih (prayer beads)",
    "palm trees and desert landscape silhouettes",
    "star and crescent combination",
    "Kaaba silhouette (for Hajj/pilgrimage themes)",
    "water/fountain motifs (purification themes)",
]

# ═══════════════════════════════════════════════════════════════
# CALLIGRAPHY STYLES — when to use each
# ═══════════════════════════════════════════════════════════════

CALLIGRAPHY_STYLES = {
    "naskh": {
        "name": "Naskh (نسخ)",
        "usage": "Body text, Quran transcription, translations — most readable",
        "style": "Clear, rounded, easily legible standard Arabic script",
    },
    "thuluth": {
        "name": "Thuluth (ثلث)",
        "usage": "Titles, headings, important verses — elegant and grand",
        "style": "Large, flowing, ornamental script with generous spacing",
    },
    "kufic": {
        "name": "Kufic (كوفي)",
        "usage": "Decorative headers, borders, geometric emphasis",
        "style": "Angular, geometric, bold — oldest Quranic script style",
    },
    "diwani": {
        "name": "Diwani (ديواني)",
        "usage": "Artistic flourishes, decorative quotes (sparingly)",
        "style": "Highly cursive, flowing, intertwined letters — Ottoman era",
    },
}

# ═══════════════════════════════════════════════════════════════
# GUARDRAIL PROMPT INJECTION — the actual text injected into prompts
# ═══════════════════════════════════════════════════════════════

ISLAMIC_GUARDRAIL_PROMPT = """
ISLAMIC DESIGN COMPLIANCE (MANDATORY — these rules override all other instructions):

HUMAN DEPICTIONS BY TYPE:
- Regular human characters (hero, other people): Faces ARE allowed with simple cartoon features (dot eyes, smile line, etc.) — friendly and approachable
- Prophets (peace be upon them): Show ONLY as radiant luminous noor/light glow emanating from the face area — NO detailed facial features, just radiant silhouette
- Allah/God/Lord/Rabb: ABSOLUTELY FORBIDDEN to depict as ANY human shape, form, face, eyes, hands, silhouette, figure, or body part. Use ONLY Arabic calligraphy (الله) in Thuluth or Kufic script with golden divine light rays, Islamic geometric star patterns, or abstract arabesque designs. The word الله (Allah) in beautiful calligraphy IS the representation.

REQUIRED VISUAL SUBSTITUTIONS:
- Prophets: Luminous noor silhouette with golden halo/aureole, back-view figure with light emanation, or calligraphic text naming the prophet
- Allah/God: Thuluth/Kufic calligraphy, Islamic geometric star patterns, or ascending divine light rays from above
- Sacred moments: Back-view figures without facial detail, hands-only depictions, or abstract outlined forms

ISLAMIC VISUAL ELEMENTS TO INCLUDE:
- Islamic geometric star patterns (interlocking 8-point or 12-point stars) as border or background elements
- Arabesque vine/floral designs as decorative framing
- Mosque dome and minaret silhouettes where contextually appropriate
- Crescent moon motifs as decorative accents
- Islamic calligraphy in Thuluth style for titles, Naskh for body text

COLOR PALETTE:
- Green (#27A359) for paradise/spiritual growth themes
- Gold (#FFD700) for divine light, sacred text, calligraphy accents
- Deep blue (#1E3A8A) for heavenly/transcendent themes
- Cream/white for purity and clean backgrounds
- Rich brown (#4A2E0A) for ink outlines on parchment cards

FRAMING:
- Include Islamic geometric border pattern around the card edges
- Use subtle arabesque corner embellishments
"""

ISLAMIC_GUARDRAIL_PROMPT_CONCISE = """
ISLAMIC COMPLIANCE (MANDATORY):
- Regular human characters: faces ARE allowed (simple cartoon features — dot eyes, smile line, etc.)
- Prophets (peace be upon them) = luminous noor/light glow emanating from face area, NO detailed facial features, radiant silhouette
- Allah/God/Lord/Rabb = ONLY Arabic calligraphy الله in Thuluth script, golden divine light rays from above, or Islamic geometric star patterns. ABSOLUTELY FORBIDDEN: any human shape, form, face, eyes, hands, silhouette, figure, or body part to represent Allah. Not even abstract. Not even glowing. The word الله (Allah) in beautiful calligraphy IS the representation.
- BORDER: Islamic 8-point geometric star pattern as thin border frame around card edges
- CALLIGRAPHY: Any Quranic/Arabic text uses Naskh style (clear, rounded). Titles in Thuluth style (ornamental)
- ACCENTS: Arabesque vine corner flourishes at 2-4 corners
- Use the card's existing color palette (do NOT add new colors for Islamic elements)
"""


def apply_guardrails(prompt, is_islamic_content, islamic_elements=None, concise=False):
    """Inject Islamic design guardrails into an image generation prompt.

    Args:
        prompt: The base image generation prompt
        is_islamic_content: Whether this is Islamic/Quranic content
        islamic_elements: Optional list of specific Islamic elements to emphasize
        concise: Use shorter guardrail text (for prompt length constraints)

    Returns:
        Modified prompt with guardrails injected (or original if not Islamic)
    """
    if not is_islamic_content:
        return prompt

    guardrail = ISLAMIC_GUARDRAIL_PROMPT_CONCISE if concise else ISLAMIC_GUARDRAIL_PROMPT

    # Add specific element emphasis if provided
    if islamic_elements:
        elements_str = ", ".join(islamic_elements)
        guardrail += f"\nSPECIFIC ISLAMIC ELEMENTS FOR THIS CARD: {elements_str}\n"

    # Add border instruction (concise version for concise mode)
    if not concise:
        guardrail += "\n" + get_islamic_border_instruction(concise=False)

    # Inject after the STYLE section (before FRONT CARD) to avoid breaking layout lines
    if "FRONT CARD" in prompt:
        prompt = prompt.replace("FRONT CARD", f"{guardrail}\nFRONT CARD", 1)
    elif "CARD LAYOUT:" in prompt or "LAYOUT GRID:" in prompt:
        marker = "LAYOUT GRID:" if "LAYOUT GRID:" in prompt else "CARD LAYOUT:"
        prompt = prompt.replace(marker, f"{guardrail}\n{marker}", 1)
    else:
        # Append at end if no clear injection point
        prompt = f"{prompt}\n\n{guardrail}"

    return prompt


def get_islamic_border_instruction(concise=False):
    """Get specific Islamic geometric border pattern instruction.

    Returns prompt text describing exactly how to draw Islamic borders
    that Gemini can consistently render.
    """
    if concise:
        return ("Thin Islamic geometric border: interlocking 8-point stars at 3mm equivalent "
                "line weight, single accent color, running along all 4 card edges with "
                "arabesque vine flourishes at corners.")
    return (
        "ISLAMIC GEOMETRIC BORDER (draw precisely):\n"
        "- Pattern: interlocking 8-point stars connected by short straight segments\n"
        "- Line weight: 3mm equivalent, matching card outline weight\n"
        "- Color: SAME accent color as card (golden or teal depending on theme)\n"
        "- Placement: 3% inset from card edge, running continuously on all 4 sides\n"
        "- Corners: arabesque vine/floral flourish filling each corner triangle\n"
        "- The border should be SUBTLE — decorative framing, not the main focus\n"
    )


def get_calligraphy_instruction(text_type="title"):
    """Get calligraphy style instruction for Arabic text.

    Args:
        text_type: 'title' for Thuluth, 'body' for Naskh, 'quote' for Diwani

    Returns:
        Prompt text describing exact calligraphy rendering style
    """
    styles = {
        "title": (
            "Arabic title text in Thuluth (ثلث) calligraphy: large, flowing strokes "
            "with generous letter spacing, ornamental flourishes on ascending strokes, "
            "gold accent color for text body with thin black outline"
        ),
        "body": (
            "Arabic body text in Naskh (نسخ) calligraphy: clear, rounded letterforms, "
            "consistent baseline, highly legible at small sizes, black ink"
        ),
        "quote": (
            "Arabic quote text in Diwani (ديواني) calligraphy: flowing cursive with "
            "intertwined letters, decorative style, accent color ink"
        ),
    }
    return styles.get(text_type, styles["body"])


def get_islamic_color_instruction(theme="warm_parchment"):
    """Build Islamic-specific color instruction for image generation.

    Returns enhanced color palette guidance for Islamic content.
    """
    if theme == "warm_parchment":
        return (
            "Islamic color palette: Gold (#FFD700) for divine light and calligraphy accents, "
            "Green (#27A359) for paradise/spiritual growth themes, "
            "Rich brown (#4A2E0A) ink outlines on warm cream/parchment (#FDF3E0) background. "
            "Use Thuluth calligraphy style for titles. "
            "Subtle geometric pattern texture in background."
        )
    else:
        return (
            "Islamic color palette: Deep blue (#1E3A8A) for heavenly/transcendent themes, "
            "Teal (#4A9B7F) accent, Gold (#FFD700) for sacred highlights, "
            "Clean white/light background with subtle geometric tile texture. "
            "Use Naskh calligraphy for Arabic text. "
            "Cool, contemplative atmosphere."
        )


def detect_islamic_content(title, category, analysis_text):
    """Detect if content is Islamic/Quranic based on keywords.

    Returns (is_islamic, suggested_elements) tuple.
    """
    text = f"{title} {category} {analysis_text}".lower()

    quranic_keywords = [
        "quran", "qur'an", "allah", "prophet", "muhammad", "surah", "sura",
        "verse", "ayah", "ayat", "taqwa", "ibadah", "worship", "islam",
        "islamic", "deen", "ummah", "sunnah", "hadith", "salah", "prayer",
        "jihad", "tawakkul", "dunya", "akhira", "afterlife", "paradise",
        "jannah", "jahannam", "ramadan", "hajj", "zakat", "shahada",
        "ihsan", "iman", "hijra", "khalifah", "shura", "adl",
        "mosque", "masjid", "minaret", "muslim", "believers",
        "sabr", "patience", "rizq", "provision", "tawbah", "repentance",
        "dhikr", "remembrance", "shukr", "gratitude", "hidayah", "guidance",
        "fitrah", "nature", "ruh", "soul", "nafs", "self",
        "halal", "haram", "fiqh", "shariah", "tawhid", "oneness",
    ]

    match_count = sum(1 for kw in quranic_keywords if kw in text)
    is_islamic = match_count >= 2  # Need at least 2 keyword matches

    # Suggest relevant Islamic elements based on content
    elements = []
    if any(w in text for w in ["prayer", "salah", "worship", "ibadah", "sajdah"]):
        elements.append("prayer mat with prostrating silhouette")
    if any(w in text for w in ["quran", "verse", "ayah", "surah", "book"]):
        elements.append("ornate Quran with calligraphy")
    if any(w in text for w in ["mosque", "masjid", "congregation", "jummah"]):
        elements.append("mosque dome and minaret silhouette")
    if any(w in text for w in ["paradise", "jannah", "afterlife", "akhira"]):
        elements.append("garden/paradise imagery with flowing water")
    if any(w in text for w in ["light", "noor", "guidance", "hidayah"]):
        elements.append("divine golden light rays from above")
    if any(w in text for w in ["prophet", "muhammad", "messenger", "rasul"]):
        elements.append("luminous noor silhouette (NO face)")
    if any(w in text for w in ["allah", "god", "divine", "tawhid", "lord"]):
        elements.append("Allah calligraphy in Thuluth script")
    if any(w in text for w in ["patience", "sabr", "tawakkul", "trust"]):
        elements.append("Islamic geometric patience pattern")
    if any(w in text for w in ["community", "ummah", "shura", "together"]):
        elements.append("circle of faceless silhouettes in unity")

    # Always add geometric border for Islamic content
    if is_islamic and not elements:
        elements.append("Islamic geometric border pattern")

    return is_islamic, elements
