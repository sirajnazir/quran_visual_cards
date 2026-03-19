"""Icon Library for Quran Visual Cards

Maps visual types and concept keywords to specific, drawable icon descriptions.
These replace generic 'icon for X' with concrete visual suggestions
that Gemini can consistently render in hand-drawn style.
"""

# Master icon vocabulary — reusable across visual types
ICON_VOCAB = {
    # Spiritual / Islamic
    "worship": "figure in prostration (sajdah) silhouette",
    "prayer": "raised hands in dua (supplication)",
    "taqwa": "shield with crescent moon inside",
    "guidance": "open Quran with light rays emanating upward",
    "patience": "anchor with roots growing downward",
    "trust": "open palm releasing a bird upward",
    "repentance": "door opening with light streaming through",
    "sin": "chain link with crack/break",
    "paradise": "garden gate with flowing water beneath",
    "divine_light": "radiating sun/star with golden rays",
    "allah": "Arabic calligraphy الله (Allah) in ornate Thuluth script with golden light rays — ABSOLUTELY NO human shape, form, eyes, hands, or silhouette",
    "god": "Arabic calligraphy الله (Allah) in ornate Thuluth script with golden light rays — ABSOLUTELY NO human shape, form, eyes, hands, or silhouette",
    "lord": "Arabic calligraphy الله (Allah) in ornate Thuluth script with golden light rays — ABSOLUTELY NO human shape, form, eyes, hands, or silhouette",
    "rabb": "Arabic calligraphy الله (Allah) in ornate Thuluth script with golden light rays — ABSOLUTELY NO human shape, form, eyes, hands, or silhouette",
    "divine": "Arabic calligraphy الله (Allah) in ornate Thuluth script with golden light rays — ABSOLUTELY NO human shape, form, eyes, hands, or silhouette",
    "soul": "flame inside a lantern",
    "heart": "anatomical heart with light inside",
    "mercy": "two hands cupped together with stars above",
    "justice": "balanced scales with sword upright",
    "obedience": "figure following an upward arrow",
    "rebellion": "arrow pointing down and away",

    # Cognitive / Decision
    "awareness": "open eye with radiating lines",
    "choice": "fork in a path / Y-shaped road",
    "bias": "tilted scale or bent ruler",
    "thinking": "figure with open Quran, light emanating upward from pages — contemplation/tafakkur",
    "insight": "ornate Islamic lantern with light streaming through geometric cutouts — illumination/basira",
    "confusion": "question mark in a cloud",
    "clarity": "magnifying glass over text",
    "memory": "filing cabinet drawer pulling open",
    "denial": "X mark or eye with line through it",
    "realization": "person with head-smacking gesture",

    # Action / Process
    "growth": "small seedling sprouting from soil",
    "decline": "wilting plant or downward arrow",
    "barrier": "brick wall with cracks",
    "breakthrough": "arrow punching through a wall",
    "connection": "two interlocking rings",
    "separation": "scissors cutting a thread",
    "accumulation": "stack of coins growing taller",
    "loss": "coins falling/scattering from hand",
    "victory": "crescent flag planted on summit with light rays — triumph/nasr",
    "defeat": "broken sword or snapped chain",
    "strength": "thick braided rope (habl) with Islamic geometric knot pattern — inner strength",
    "weakness": "thin cracked thread",
    "progress": "figure climbing upward stairs",
    "stagnation": "figure stuck in circular pattern",

    # Balance / Comparison
    "balance": "traditional two-pan scale",
    "imbalance": "tilted scale with one side heavy",
    "moderation": "slider/dial at center position",
    "extreme": "arrow hitting far edge of spectrum",
    "trade_off": "seesaw with objects on each end",
    "equilibrium": "stable platform with equal weight sides",

    # Time / Change
    "beginning": "sunrise over horizon line",
    "ending": "sunset with fading light",
    "transformation": "caterpillar → butterfly arrow",
    "cycle": "circular arrow (recycling symbol style)",
    "milestone": "flag planted on a point",
    "deadline": "ornate Islamic hourglass with crescent finial, sand trickling — time awareness",
    "eternity": "infinity symbol with radiating light",
    "temporary": "fading footprints in sand",

    # System / Structure
    "foundation": "stone/brick base block",
    "pillar": "classical column with capital",
    "hierarchy": "stacked blocks pyramid-style",
    "network": "interconnected dots/nodes",
    "filter": "funnel shape with dots passing through",
    "boundary": "fence or dotted line border",
    "unity": "circle of figures around Kaaba silhouette (bird's eye) — ummah unity",
    "fragmentation": "crumbling blocks separating apart",

    # Emotion / State
    "desire": "flame/fire burning upward",
    "fear": "eye with wide pupil in shadow",
    "contentment": "serene face silhouette under crescent moon — inner peace/sakinah",
    "anger": "lightning bolt or jagged line",
    "gratitude": "hands raised in dua (palms up) with blessings raining down as small stars — shukr",
    "humility": "small figure next to large mountain",
    "shame": "face with downward gaze and shadow",
    "honor": "crown or laurel wreath with light",
}

# Islamic-specific style instructions for all icons
ISLAMIC_ICON_STYLE = (
    "ICON STYLE (ALL icons on this card MUST follow these rules):\n"
    "- Every icon is a HAND-DRAWN ink sketch — wobbly natural lines, NOT clean digital vector\n"
    "- Use cross-hatching (45° parallel lines, 2mm spacing) for shading inside icons, NEVER solid fills\n"
    "- Accent color wash (single flat tone) allowed for one layer of fill — NO gradients\n"
    "- Islamic motif integration: incorporate subtle arabesque flourishes, crescent accents, or geometric star elements into icon borders when contextually appropriate\n"
    "- Icon borders: thin hand-drawn frame with slight corner embellishments (tiny vine curl or geometric notch)\n"
    "- Size: each icon ~35-45px equivalent, consistent across all icons on the card\n"
    "- Style reference: imagine a skilled Muslim calligrapher/artist drew these with a Sakura Micron pen\n"
    "- FORBIDDEN icon styles: flat corporate/business icons, emoji-style, 3D rendered, photorealistic, clipart\n"
    "- For spiritual concepts: use Islamic visual language (crescent, star patterns, calligraphy snippets, mosque silhouettes, lanterns, prayer beads) rather than generic western symbols\n"
    "- For process/action concepts: show the action being performed BY the hero character or with Islamic context items (Quran, prayer mat, tasbih) rather than abstract shapes\n"
)

# Per-visual-type default icon sets (what icons work best structurally)
VISUAL_TYPE_ICONS = {
    "sequential_chain": {
        "connector": "thick hand-drawn arrow →",
        "node_shape": "rounded rectangle with thick border",
        "style_note": "Each step gets a unique icon ABOVE its label. Icons should be 40px equivalent, line-drawn.",
    },
    "cycle_loop": {
        "connector": "curved arrow following the circle",
        "node_shape": "circle with icon inside",
        "style_note": "Icons sit inside each circle node. Arrows curve between nodes clockwise.",
    },
    "tripod": {
        "connector": "horizontal beam on top connecting all three",
        "node_shape": "rectangular pillar with cross-hatching",
        "style_note": "Icon at top of each pillar, inside a small circle. Platform on top labeled with title.",
    },
    "pyramid_hierarchy": {
        "connector": "horizontal divider lines between levels",
        "node_shape": "trapezoidal layer",
        "style_note": "Each level gets a small icon on the LEFT side, with text label on the RIGHT.",
    },
    "scale_balance": {
        "connector": "beam and chains hanging pans",
        "node_shape": "circular pans hanging from chains",
        "style_note": "Icons go INSIDE each pan. Fulcrum gets a decorative triangle. Tilt shows imbalance.",
    },
    "iceberg": {
        "connector": "wavy waterline dividing above/below",
        "node_shape": "labeled zones within iceberg shape",
        "style_note": "Tip icon above water. Multiple icons stacked below water, getting larger deeper down.",
    },
    "venn_diagram": {
        "connector": "overlap zone highlighted",
        "node_shape": "large circle with icon in center",
        "style_note": "Each circle gets ONE icon in its non-overlapping area. Overlap gets a special combined icon.",
    },
    "comparison": {
        "connector": "bold vertical divider line",
        "node_shape": "side-by-side panels",
        "style_note": "Left panel: X mark + concept icon. Right panel: checkmark + concept icon. Mirror layout.",
    },
    "force_diagram": {
        "connector": "thick directional arrows (varying thickness = force strength)",
        "node_shape": "central shield/rectangle",
        "style_note": "Center element is solid and anchored. Arrows push in from edges with icons at arrow tips.",
    },
    "funnel": {
        "connector": "narrowing walls with dots/items dropping through",
        "node_shape": "horizontal band within funnel",
        "style_note": "Icons at each stage level, getting smaller as funnel narrows. Items shown being filtered.",
    },
    "decision_tree": {
        "connector": "branching lines with Yes/No labels",
        "node_shape": "diamonds for decisions, rectangles for outcomes",
        "style_note": "Decision diamonds get question-mark icons. Outcome boxes get result icons.",
    },
    "matrix_2x2": {
        "connector": "thick axis lines forming cross",
        "node_shape": "four quadrant areas",
        "style_note": "One icon per quadrant, centered. Axis labels bold at edges.",
    },
    "fishbone": {
        "connector": "angled bones branching from central spine",
        "node_shape": "text labels at bone endpoints",
        "style_note": "Small icon at the tip of each major bone. Fish head on right as the main effect.",
    },
    "network_graph": {
        "connector": "lines of varying thickness between nodes",
        "node_shape": "circles of varying sizes",
        "style_note": "Larger nodes = more important. Icons inside nodes. Line thickness = connection strength.",
    },
    "timeline": {
        "connector": "horizontal line with milestone dots",
        "node_shape": "flag/marker above timeline",
        "style_note": "Icons sit above the timeline at each milestone. Dates/labels below the line.",
    },
    "s_curve": {
        "connector": "smooth S-shaped curve line",
        "node_shape": "labeled zones along the curve",
        "style_note": "One icon at each phase transition point. Tipping point gets a star/burst icon.",
    },
    "exponential_curve": {
        "connector": "hockey-stick curve with dotted linear comparison",
        "node_shape": "labeled zones",
        "style_note": "Icon at the knee/inflection point (exclamation). Small icon at start, large at end.",
    },
    "flow_chart": {
        "connector": "arrows between shapes (some branching)",
        "node_shape": "rounded rectangles + diamonds",
        "style_note": "Process boxes get action icons. Decision diamonds get question icons.",
    },
    "spectrum": {
        "connector": "horizontal bar with gradient hatching",
        "node_shape": "marker arrows pointing to positions on bar",
        "style_note": "Icons at each extreme end. Ideal zone highlighted with accent color.",
    },
    "nested_circles": {
        "connector": "concentric circle borders",
        "node_shape": "ring zones between circles",
        "style_note": "Icon at CENTER (innermost, most important). Labels in each ring zone.",
    },
}


def get_icon_for_concept(concept_text):
    """Find the best matching icon description for a concept.

    Scans ICON_VOCAB for keyword matches and returns the most specific icon.
    Falls back to a generic derived icon if no match found.

    Args:
        concept_text: String describing a concept or step label

    Returns:
        String with specific icon description suitable for image generation prompts
    """
    concept_lower = concept_text.lower().strip()

    # Direct match
    if concept_lower in ICON_VOCAB:
        return ICON_VOCAB[concept_lower]

    # Partial match - check if any vocab key is IN the concept
    best_match = None
    best_len = 0
    for key, icon_desc in ICON_VOCAB.items():
        if key in concept_lower and len(key) > best_len:
            best_match = icon_desc
            best_len = len(key)

    if best_match:
        return best_match

    # Reverse match - check if concept words are in any vocab key
    concept_words = set(concept_lower.split())
    for key, icon_desc in ICON_VOCAB.items():
        key_words = set(key.split("_"))
        if concept_words & key_words:
            return icon_desc

    # Fallback: generate a simple derived icon
    return f"simple outline icon representing {concept_lower}"


def get_icons_for_steps(steps, visual_type=None):
    """Map a list of step dicts to specific icon descriptions.

    Args:
        steps: List of dicts with 'label', 'description' keys
        visual_type: Optional visual type for structural context

    Returns:
        List of dicts with original step data + 'icon_desc' key added
    """
    result = []
    for step in steps:
        label = step.get("label", "")
        description = step.get("description", "")

        # Try description first (more specific), then label
        icon = get_icon_for_concept(description) if description else get_icon_for_concept(label)

        enriched = dict(step)
        enriched["icon_desc"] = icon
        result.append(enriched)

    return result


def get_structural_guidance(visual_type):
    """Get structural icon placement guidance for a visual type.

    Args:
        visual_type: String identifier for the visualization type

    Returns:
        Dict with 'connector', 'node_shape', and 'style_note' keys describing
        how to position icons within this visual structure
    """
    return VISUAL_TYPE_ICONS.get(visual_type, {
        "connector": "hand-drawn arrows",
        "node_shape": "simple bordered shapes",
        "style_note": "Each concept gets a small, distinct line-drawn icon beside its label.",
    })


def build_icon_enriched_steps(steps, visual_type=None):
    """Build step descriptions enriched with specific icon suggestions.

    Returns a formatted string ready for injection into illustration prompts.
    This string includes step labels, descriptions, icon directions, and
    structural guidance for consistent visual rendering.

    Args:
        steps: List of step dicts with 'label', 'description', optional 'arabic'
        visual_type: Optional visual type for structural context

    Returns:
        Formatted string with enriched step information and icon placement rules
    """
    if not steps:
        return ""

    enriched = get_icons_for_steps(steps, visual_type)
    guidance = get_structural_guidance(visual_type)

    lines = []
    for i, s in enumerate(enriched):
        label = s.get("label", f"Step {i+1}")
        desc = s.get("description", "")
        arabic = s.get("arabic", "")
        icon = s.get("icon_desc", "simple icon")

        line = f'  {i+1}. "{label.upper()}"'
        if desc:
            line += f" — {desc}"
        line += f" [ICON: {icon}]"
        if arabic:
            line += f' (Arabic: "{arabic}")'
        lines.append(line)

    result = "\n".join(lines)
    result += f"\n\nICON RULES: {guidance.get('style_note', '')}"
    result += f"\n\n{ISLAMIC_ICON_STYLE}"

    return result


def get_all_icon_types():
    """Return list of all available visual types.

    Returns:
        List of visual type identifiers
    """
    return sorted(VISUAL_TYPE_ICONS.keys())


def get_all_concepts():
    """Return list of all available concept keywords in the vocabulary.

    Returns:
        List of concept keywords that have icon mappings
    """
    return sorted(ICON_VOCAB.keys())


def enforce_divine_icon_guardrails(steps, step_label=None):
    """Enforce strict Allah/God/Lord icon guardrails — NO human forms allowed.

    If a step's label or description mentions Allah/God/Lord/divine/Rabb,
    override any icon that could be interpreted as human-like with the
    strict Allah calligraphy icon.

    Args:
        steps: List of step dicts with 'label', 'description', 'icon_desc' keys
        step_label: Optional specific step label to check (for single-step enforcement)

    Returns:
        List of steps with divine icons guaranteed to be safe
    """
    divine_keywords = {"allah", "god", "lord", "rabb", "divine"}
    strict_divine_icon = "Arabic calligraphy الله (Allah) in ornate Thuluth script with golden light rays — ABSOLUTELY NO human shape, form, eyes, hands, or silhouette"

    result = []
    for step in steps:
        step_copy = dict(step)
        label = (step.get("label") or "").lower()
        desc = (step.get("description") or "").lower()
        combined = f"{label} {desc}"

        # Check if this step mentions divine concepts
        has_divine = any(kw in combined for kw in divine_keywords)

        if has_divine:
            # Override icon to strict divine version
            step_copy["icon_desc"] = strict_divine_icon

        result.append(step_copy)

    return result


def list_concepts_by_category():
    """Return icon vocabulary grouped by semantic category.

    Returns:
        Dict mapping category names to lists of (concept, icon_desc) tuples
    """
    categories = {
        "spiritual_islamic": [
            ("worship", ICON_VOCAB["worship"]),
            ("prayer", ICON_VOCAB["prayer"]),
            ("taqwa", ICON_VOCAB["taqwa"]),
            ("guidance", ICON_VOCAB["guidance"]),
            ("patience", ICON_VOCAB["patience"]),
            ("trust", ICON_VOCAB["trust"]),
            ("repentance", ICON_VOCAB["repentance"]),
            ("sin", ICON_VOCAB["sin"]),
            ("paradise", ICON_VOCAB["paradise"]),
            ("divine_light", ICON_VOCAB["divine_light"]),
            ("soul", ICON_VOCAB["soul"]),
            ("heart", ICON_VOCAB["heart"]),
            ("mercy", ICON_VOCAB["mercy"]),
            ("justice", ICON_VOCAB["justice"]),
            ("obedience", ICON_VOCAB["obedience"]),
            ("rebellion", ICON_VOCAB["rebellion"]),
        ],
        "cognitive_decision": [
            ("awareness", ICON_VOCAB["awareness"]),
            ("choice", ICON_VOCAB["choice"]),
            ("bias", ICON_VOCAB["bias"]),
            ("thinking", ICON_VOCAB["thinking"]),
            ("insight", ICON_VOCAB["insight"]),
            ("confusion", ICON_VOCAB["confusion"]),
            ("clarity", ICON_VOCAB["clarity"]),
            ("memory", ICON_VOCAB["memory"]),
            ("denial", ICON_VOCAB["denial"]),
            ("realization", ICON_VOCAB["realization"]),
        ],
        "action_process": [
            ("growth", ICON_VOCAB["growth"]),
            ("decline", ICON_VOCAB["decline"]),
            ("barrier", ICON_VOCAB["barrier"]),
            ("breakthrough", ICON_VOCAB["breakthrough"]),
            ("connection", ICON_VOCAB["connection"]),
            ("separation", ICON_VOCAB["separation"]),
            ("accumulation", ICON_VOCAB["accumulation"]),
            ("loss", ICON_VOCAB["loss"]),
            ("victory", ICON_VOCAB["victory"]),
            ("defeat", ICON_VOCAB["defeat"]),
            ("strength", ICON_VOCAB["strength"]),
            ("weakness", ICON_VOCAB["weakness"]),
            ("progress", ICON_VOCAB["progress"]),
            ("stagnation", ICON_VOCAB["stagnation"]),
        ],
        "balance_comparison": [
            ("balance", ICON_VOCAB["balance"]),
            ("imbalance", ICON_VOCAB["imbalance"]),
            ("moderation", ICON_VOCAB["moderation"]),
            ("extreme", ICON_VOCAB["extreme"]),
            ("trade_off", ICON_VOCAB["trade_off"]),
            ("equilibrium", ICON_VOCAB["equilibrium"]),
        ],
        "time_change": [
            ("beginning", ICON_VOCAB["beginning"]),
            ("ending", ICON_VOCAB["ending"]),
            ("transformation", ICON_VOCAB["transformation"]),
            ("cycle", ICON_VOCAB["cycle"]),
            ("milestone", ICON_VOCAB["milestone"]),
            ("deadline", ICON_VOCAB["deadline"]),
            ("eternity", ICON_VOCAB["eternity"]),
            ("temporary", ICON_VOCAB["temporary"]),
        ],
        "system_structure": [
            ("foundation", ICON_VOCAB["foundation"]),
            ("pillar", ICON_VOCAB["pillar"]),
            ("hierarchy", ICON_VOCAB["hierarchy"]),
            ("network", ICON_VOCAB["network"]),
            ("filter", ICON_VOCAB["filter"]),
            ("boundary", ICON_VOCAB["boundary"]),
            ("unity", ICON_VOCAB["unity"]),
            ("fragmentation", ICON_VOCAB["fragmentation"]),
        ],
        "emotion_state": [
            ("desire", ICON_VOCAB["desire"]),
            ("fear", ICON_VOCAB["fear"]),
            ("contentment", ICON_VOCAB["contentment"]),
            ("anger", ICON_VOCAB["anger"]),
            ("gratitude", ICON_VOCAB["gratitude"]),
            ("humility", ICON_VOCAB["humility"]),
            ("shame", ICON_VOCAB["shame"]),
            ("honor", ICON_VOCAB["honor"]),
        ],
    }
    return categories
