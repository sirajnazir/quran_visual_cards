"""Card Style Presets for Quran Visual Cards

Three curated presets that bundle drawing style, color palette, layout rules,
and font instructions into cohesive, named visual identities.

Usage:
    from style_presets import get_preset, apply_preset_to_prompt, PRESET_NAMES
    preset = get_preset("classic_sketch")
    prompt = apply_preset_to_prompt(base_prompt, preset)
"""

# ═══════════════════════════════════════════════════════════════
# PRESET DEFINITIONS
# ═══════════════════════════════════════════════════════════════

PRESETS = {
    "classic_sketch": {
        "name": "Classic Sketch",
        "description": "Clean Micron-pen sketchnote on white cardstock — the default production style",
        "drawing_tool": (
            "0.5 mm Sakura Micron fineliner on smooth white cardstock. "
            "1.5–2 pt BLACK ink strokes with slight hand-wobble. "
            "Shading: parallel hatching (45°, 2 mm apart) or stipple dots. "
            "NEVER smooth gradients, airbrush, blur, or 3D effects."
        ),
        "color_rules": {
            "warm_parchment": {
                "instruction": (
                    "ONLY 2 colors: black ink + golden amber (#C8902E) flat wash. "
                    "Card surface: warm cream (#FDF3E0). Text: dark brown (#4A2E0A)."
                ),
                "accent_hex": "#C8902E",
                "bg_hex": "#FDF3E0",
                "text_hex": "#4A2E0A",
            },
            "cool_mint": {
                "instruction": (
                    "ONLY 2 colors: black ink + soft teal (#4A9B7F) flat wash. "
                    "Card surface: clean white (#FFFFFF). Text: dark navy (#1A2530)."
                ),
                "accent_hex": "#4A9B7F",
                "bg_hex": "#FFFFFF",
                "text_hex": "#1A2530",
            },
        },
        "layout": {
            "title_zone": "top 20%",
            "illustration_zone": "middle 55%",
            "quote_zone": "bottom 15%",
            "footer_zone": "bottom 5%",
            "margins": "5% all sides",
        },
        "font_style": "hand-lettered with natural baseline drift, slightly uneven letter sizes",
        "border": "thin single-line rounded rectangle with 3px corners",
        "banned_effects": [
            "anti-aliasing glow", "airbrush", "Gaussian blur",
            "drop shadows", "3D bevels", "photorealistic textures",
            "smooth gradients", "lens flare",
        ],
    },

    "islamic_ornate": {
        "name": "Islamic Ornate",
        "description": "Rich Islamic art style with geometric borders, calligraphy, and sacred geometry",
        "drawing_tool": (
            "Fine-point calligraphy nib (1.0 mm) on aged cream parchment. "
            "1.5–2 pt ink strokes with intentional calligraphic thick-thin variation. "
            "Shading: geometric tessellation fills and arabesque vine patterns. "
            "Gold leaf accents on key elements. "
            "NEVER photorealistic, no 3D, no digital gradients."
        ),
        "color_rules": {
            "warm_parchment": {
                "instruction": (
                    "ONLY 3 colors: black ink + deep gold (#DAA520) + forest green (#27A359). "
                    "Card surface: aged cream parchment (#F5E6C8). Text: dark brown (#4A2E0A). "
                    "Gold for borders and calligraphy accents. Green for Islamic motifs."
                ),
                "accent_hex": "#DAA520",
                "accent2_hex": "#27A359",
                "bg_hex": "#F5E6C8",
                "text_hex": "#4A2E0A",
            },
            "cool_mint": {
                "instruction": (
                    "ONLY 3 colors: black ink + royal blue (#1E3A8A) + gold (#FFD700). "
                    "Card surface: soft ivory (#FAFAF0). Text: deep navy (#0F1B3D). "
                    "Gold for calligraphy and sacred geometry. Blue for background patterns."
                ),
                "accent_hex": "#1E3A8A",
                "accent2_hex": "#FFD700",
                "bg_hex": "#FAFAF0",
                "text_hex": "#0F1B3D",
            },
        },
        "layout": {
            "title_zone": "top 18% — Thuluth calligraphy style",
            "illustration_zone": "middle 52% — framed by geometric border inset",
            "quote_zone": "bottom 18% — Naskh calligraphy, centered",
            "footer_zone": "bottom 7% — card number in geometric star frame",
            "margins": "8% all sides to accommodate ornate border",
        },
        "font_style": "Arabic calligraphy: Thuluth for titles, Naskh for body, Diwani for quotes",
        "border": (
            "Islamic geometric border: interlocking 8-point stars connected by straight segments, "
            "3% inset from edge, accent color line, arabesque vine flourishes at all 4 corners"
        ),
        "banned_effects": [
            "anti-aliasing glow", "airbrush", "Gaussian blur",
            "3D bevels", "photorealistic textures", "lens flare",
            "human faces", "figurative depictions of prophets",
        ],
        "islamic_extras": {
            "border_pattern": "8-point geometric star interlocking tessellation",
            "corner_ornament": "arabesque vine/floral flourish",
            "calligraphy_title": "Thuluth (ثلث) — ornamental, flowing",
            "calligraphy_body": "Naskh (نسخ) — clear, rounded, legible",
            "sacred_geometry": "subtle tessellation in background at 10% opacity",
        },
    },

    "analytical_clean": {
        "name": "Analytical Clean",
        "description": "Minimalist infographic style — crisp lines, data-viz clarity, no decorative noise",
        "drawing_tool": (
            "0.35 mm technical pen (Rotring Rapidograph style) on smooth bright white paper. "
            "1.0–1.5 pt precise BLACK ink strokes with minimal wobble (near-mechanical precision). "
            "Shading: light parallel hatching (60°, 3 mm spacing) or flat 20% grey tone. "
            "NEVER hand-lettered — use clean sans-serif geometric letterforms. "
            "NEVER decorative, no flourishes, no textures."
        ),
        "color_rules": {
            "warm_parchment": {
                "instruction": (
                    "ONLY 2 colors: black ink + warm orange (#E07B3C) for accent/highlight. "
                    "Card surface: pure white (#FFFFFF). Text: dark charcoal (#333333). "
                    "NO decorative elements. Clean data-viz style."
                ),
                "accent_hex": "#E07B3C",
                "bg_hex": "#FFFFFF",
                "text_hex": "#333333",
            },
            "cool_mint": {
                "instruction": (
                    "ONLY 2 colors: black ink + steel blue (#4682B4) for accent/highlight. "
                    "Card surface: pure white (#FFFFFF). Text: dark charcoal (#333333). "
                    "NO decorative elements. Clean data-viz style."
                ),
                "accent_hex": "#4682B4",
                "bg_hex": "#FFFFFF",
                "text_hex": "#333333",
            },
        },
        "layout": {
            "title_zone": "top 15% — clean sans-serif, left-aligned",
            "illustration_zone": "middle 60% — maximum clarity, generous whitespace",
            "quote_zone": "bottom 15% — small italic text, left-aligned",
            "footer_zone": "bottom 5% — minimal",
            "margins": "6% all sides — breathing room is essential",
        },
        "font_style": "clean sans-serif geometric letterforms (Futura/Helvetica style), consistent baseline",
        "border": "hairline 0.5pt rule line, 2% inset, no rounded corners (sharp 90° angles)",
        "banned_effects": [
            "anti-aliasing glow", "airbrush", "Gaussian blur",
            "drop shadows", "3D bevels", "photorealistic textures",
            "decorative flourishes", "arabesque patterns", "textured backgrounds",
            "hand-wobble", "sketch imperfections",
        ],
    },
}

PRESET_NAMES = list(PRESETS.keys())


# ═══════════════════════════════════════════════════════════════
# PRESET ACCESS FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_preset(preset_name):
    """Get a style preset by name.

    Args:
        preset_name: One of 'classic_sketch', 'islamic_ornate', 'analytical_clean'

    Returns:
        Dict with all preset configuration, or classic_sketch as default
    """
    return PRESETS.get(preset_name, PRESETS["classic_sketch"])


def get_preset_color_instruction(preset_name, theme="warm_parchment"):
    """Get color instruction string from a preset for a given theme.

    Args:
        preset_name: Preset identifier
        theme: 'warm_parchment' or 'cool_mint'

    Returns:
        Color instruction string for prompt injection
    """
    preset = get_preset(preset_name)
    theme_colors = preset["color_rules"].get(theme, preset["color_rules"]["warm_parchment"])
    return theme_colors["instruction"]


def get_preset_drawing_tool(preset_name):
    """Get drawing tool specification from a preset.

    Args:
        preset_name: Preset identifier

    Returns:
        Drawing tool specification string
    """
    preset = get_preset(preset_name)
    return preset["drawing_tool"]


def get_preset_banned_list(preset_name):
    """Get banned effects list from a preset.

    Args:
        preset_name: Preset identifier

    Returns:
        Comma-separated string of banned effects
    """
    preset = get_preset(preset_name)
    return ", ".join(preset.get("banned_effects", []))


def apply_preset_to_prompt(prompt, preset_name, theme="warm_parchment"):
    """Apply a style preset to an existing prompt by replacing key sections.

    This function looks for standard markers in the prompt and replaces
    the drawing tool, color, and border sections with preset values.

    Args:
        prompt: Base prompt string with standard section markers
        preset_name: Preset identifier
        theme: 'warm_parchment' or 'cool_mint'

    Returns:
        Modified prompt with preset values injected
    """
    preset = get_preset(preset_name)

    # Replace drawing tool section if marker found
    if "DRAWING TOOL" in prompt:
        # Find the drawing tool section and replace its content
        lines = prompt.split("\n")
        new_lines = []
        in_tool_section = False
        tool_replaced = False

        for line in lines:
            if "DRAWING TOOL" in line and not tool_replaced:
                new_lines.append(line)  # Keep the header
                new_lines.append(f"- {preset['drawing_tool']}")
                banned = get_preset_banned_list(preset_name)
                new_lines.append(f"- BANNED: {banned}")
                in_tool_section = True
                tool_replaced = True
                continue

            if in_tool_section:
                # Skip old drawing tool lines until we hit a new section
                if line.strip().startswith(("-", "•")) or line.strip() == "":
                    if line.strip().isupper() and ":" in line:
                        in_tool_section = False
                        new_lines.append(line)
                    continue
                else:
                    in_tool_section = False
                    new_lines.append(line)
            else:
                new_lines.append(line)

        prompt = "\n".join(new_lines)

    return prompt


def get_preset_summary(preset_name):
    """Get a human-readable summary of a preset.

    Returns:
        Dict with name, description, and key characteristics
    """
    preset = get_preset(preset_name)
    return {
        "name": preset["name"],
        "description": preset["description"],
        "font": preset["font_style"],
        "border": preset["border"],
        "layout": preset["layout"],
        "banned_count": len(preset.get("banned_effects", [])),
    }


def list_all_presets():
    """List all available presets with summaries.

    Returns:
        List of preset summary dicts
    """
    return [get_preset_summary(name) for name in PRESET_NAMES]
