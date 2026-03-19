"""
Image Generation Module — Nano Banana 2 (Google Gemini Image Gen)
Generates hand-drawn doodle-style illustrations for mental model cards.
Phase 6 Enhancement: Integrated intelligent matching and Islamic guardrails.
"""
import os
import io
import base64
import json
import re
from pathlib import Path
from PIL import Image

from islamic_guardrails import apply_guardrails, get_islamic_color_instruction, detect_islamic_content
from intelligent_matching import get_illustration_prompt_for_visual_type
from config import LEGACY_MODEL_TYPES
from icon_library import build_icon_enriched_steps, get_structural_guidance, get_icon_for_concept, enforce_divine_icon_guardrails, get_icons_for_steps
from hero_character import build_hero_injection, suggest_pose_for_visual_type

# ---------- Configuration ----------
GOOGLE_API_KEY = os.environ.get("GOOGLE_AI_API_KEY", "")
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "static", "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

# Gemini model for image generation
IMAGE_MODEL = "gemini-3-pro-image-preview"  # best quality, matches MCP server


def get_gemini_client():
    """Get Google GenAI client."""
    api_key = GOOGLE_API_KEY or os.environ.get("GOOGLE_AI_API_KEY", "")
    if not api_key:
        return None
    try:
        from google import genai

        # Try to create client with custom http options to handle proxy issues
        try:
            import httpx
            # Attempt direct connection first (bypassing proxy if possible)
            http_client = httpx.Client(proxy=None, timeout=120)
            client = genai.Client(api_key=api_key, http_options={"client": http_client})
        except Exception:
            # Fall back to default client (uses system proxy)
            client = genai.Client(api_key=api_key)

        return client
    except Exception as e:
        print(f"[image_gen] Failed to init Gemini client: {e}")
        return None


# ---------- Data Sanitization ----------

def _sanitize_title(card_data):
    """Get a concise card title for the image prompt (2-5 words max).

    Prefers card_title (LLM-generated concise title), falls back to
    matched_model_name, then truncates raw title.
    """
    # Prefer concise card_title from LLM analysis
    card_title = card_data.get("card_title", "").strip()
    if card_title and len(card_title) <= 60:
        return card_title

    # Fallback: matched model name (usually concise)
    model_name = card_data.get("matched_model_name", "").strip()
    if model_name and model_name != "Custom Analysis" and len(model_name) <= 60:
        return model_name

    # Last resort: truncate raw title to first ~6 words
    raw = card_data.get("title", "Concept")
    words = raw.split()
    if len(words) <= 6:
        return raw
    return " ".join(words[:6])


def _sanitize_category(card_data):
    """Get a concise category for the image prompt (1-3 words max).

    Prefers card_category (LLM-generated), falls back to truncated raw category.
    """
    # Prefer concise card_category from LLM analysis
    card_cat = card_data.get("card_category", "").strip()
    if card_cat and len(card_cat) <= 40:
        return card_cat

    # Fallback: truncate raw category
    raw = card_data.get("category", "")
    words = raw.split()
    if len(words) <= 4:
        return raw
    return " ".join(words[:4])


def _truncate_at_sentence(text, max_len=600):
    """Truncate text at the nearest sentence boundary, never mid-word."""
    if len(text) <= max_len:
        return text
    # Find last sentence-ending punctuation before max_len
    truncated = text[:max_len]
    for end_char in ['. ', '.\n', '."', ".'", '.']:
        last_period = truncated.rfind(end_char)
        if last_period > max_len * 0.5:  # At least half the content
            return truncated[:last_period + 1]
    # Fallback: cut at last space
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return truncated[:last_space] + '...'
    return truncated


def _build_verse_ref_line(surah_name, verse_number):
    """Build verse reference string for card top band. Returns empty string if no data."""
    parts = []
    if surah_name:
        parts.append(f"Surah {surah_name}" if not surah_name.lower().startswith("surah") else surah_name)
    if verse_number:
        parts.append(verse_number)
    if parts:
        ref = " · ".join(parts)
        return f"\n  - VERSE REFERENCE: Small italic text \"{ref}\" centered below the title, in accent color — this is the Quranic source"
    return ""


def _build_verse_ref_display(surah_name, verse_number):
    """Build short verse reference display (e.g., '2:165') for footer ornament."""
    if surah_name and verse_number:
        # verse_number should be in format "Surah:Verse" or just "Surah:Verse"
        if ":" in str(verse_number):
            return verse_number
        # Try to extract from surah_name and verse_number separately
        parts = []
        # verse_number might already be the full reference
        if verse_number:
            parts.append(str(verse_number))
        if parts:
            return "·".join(parts)
    elif verse_number:
        return str(verse_number)
    return ""


def _build_verse_text_block(verse_arabic, verse_english):
    """Build prompt instructions for rendering Quran verse text on the back card.

    Based on standard Islamic verse card design principles:
    - Arabic text is LARGE, centered, in Naskh calligraphy with proper RTL rendering
    - English translation sits below in smaller italic serif
    - Both are enclosed in an ornate arabesque frame with geometric corner motifs
    - A decorative divider separates the verse section from the explanation
    """
    if not verse_arabic and not verse_english:
        return ""

    block = "\n\n  QURANIC VERSE SECTION (TOP 25-30% of the back card — this is the MOST PROMINENT element):\n"
    block += "  Draw a hand-drawn ornate rectangular frame with arabesque vine corner flourishes and Islamic geometric star accents at each corner.\n"
    block += "  Inside this frame, centered:\n"

    if verse_arabic:
        block += (
            f'  LINE 1 (ARABIC — LARGE): "{verse_arabic}"\n'
            f"  — Render in Naskh calligraphy style, RIGHT-TO-LEFT direction, centered horizontally\n"
            f"  — This is the LARGEST text on the back card (approx 14pt equivalent), black ink\n"
            f"  — Copy EVERY Arabic letter and diacritical mark EXACTLY — do not approximate or summarize\n"
        )
    if verse_english:
        block += (
            f'  LINE 2 (ENGLISH — smaller): "{verse_english}"\n'
            f"  — Italic serif hand-lettered style, centered below the Arabic, approx 9pt equivalent\n"
            f"  — Enclosed in quotation marks, accent color ink\n"
            f"  — Copy EVERY English word EXACTLY as written above — do not paraphrase or change spelling\n"
        )

    block += (
        "  Below the verse frame: thin hand-drawn decorative divider line with small arabesque ornament in center\n"
        "  Then the explanation paragraphs follow below the divider.\n"
    )

    return block


# ---------- Prompt Engineering ----------

CARD_FRONT_PROMPT_TEMPLATE = """Create a single hand-drawn sketchnote-style mental model card illustration with an aged parchment aesthetic.

CARD SURFACE & BORDER (CRITICAL — the card must look like a treasured Islamic artifact):
- Card surface: aged warm parchment with subtle paper grain texture — NOT flat white
- Edges: slightly darkened/vignette edges as if the parchment is naturally aged and worn
- BORDER: ornate Islamic geometric border frame around ALL 4 edges of the card (2-3% width) — interlocking star-and-polygon tessellation pattern in thin ink lines with accent color wash fill
- CORNERS: elaborate arabesque vine/floral corner flourishes extending inward ~8% from each corner — flowing organic curves with small leaf motifs
- Between border and content: thin ruled line creating an inner margin frame

DRAWING TOOL (CRITICAL — replicate exactly):
- Simulate a 0.5 mm Sakura Micron fineliner on aged parchment cardstock
- Outlines: 1.5–2 pt BLACK ink strokes with slight hand-wobble (NOT digitally perfect)
- Shading: parallel hatching lines (45° angle, 2 mm apart) or stipple dots — NEVER smooth gradients
- Fill accents: single flat wash of ONE accent color — no blending, no gradients
- Text: hand-lettered with natural baseline drift (letters slightly uneven in size)
- BANNED: anti-aliasing glow, airbrush, Gaussian blur, drop shadows, 3D bevels, photorealistic textures

COLOR RULE (STRICT — only 2 colors allowed):
- {color_instruction}
- Everything else is BLACK ink or PARCHMENT surface — no extra colors

LAYOUT GRID (follow these zones precisely, INSIDE the ornate border):
- TOP BAND (top 20%): Title "{title}" hand-lettered BOLD UPPERCASE left-aligned | Category "{category}" smaller text right-aligned{verse_ref_line} | thin ruled divider line below
- CENTER ZONE (middle 55%): Main illustration filling this zone edge-to-edge with 10% internal margins
- BOTTOM BAND (bottom 15%): Italic hand-written quote: "{quote}"
- FOOTER (bottom 5%): Verse reference "{verse_ref_display}" inside a small hand-drawn ornate circle with Islamic geometric border, bottom-right — if no verse reference, show card number "{card_number}" inside a crescent-decorated circle
- MARGINS: 5% padding inside the border — white space is sacred, do NOT crowd

MAIN ILLUSTRATION (center zone):
{illustration_description}

ICON QUALITY ENFORCEMENT:
- Every labeled concept MUST have a SPECIFIC, RECOGNIZABLE icon drawn beside it (not an abstract blob)
- Icons should be simple line-drawings, 30-40px equivalent size, consistent weight
- Use cross-hatching or stipple dots for shading inside icons — never solid fill except accent color wash
- Each icon must be DIFFERENT from every other icon on the card

OUTPUT: Single card image, portrait orientation, approximately 380×540 pixel ratio."""


CARD_BACK_PROMPT_TEMPLATE = """Create the BACK side of a hand-drawn mental model card with aged parchment aesthetic matching the front.

CRITICAL RULE: This is a TEXT-ONLY card. Absolutely NO illustrations, NO diagrams, NO icons, NO flowcharts, NO images. Only hand-lettered text and decorative border framing.

CARD SURFACE & BORDER (must match front card):
- Card surface: aged warm parchment with subtle paper grain — NOT flat white
- Edges: slightly darkened/vignette as if naturally aged
- BORDER: ornate Islamic geometric border frame around ALL 4 edges — interlocking star-and-polygon tessellation in thin ink with accent color wash
- CORNERS: arabesque vine/floral corner flourishes at all 4 corners
- Crescent moon small decorative motif integrated into top border center

DRAWING TOOL (match front card exactly):
- 0.5 mm Micron fineliner on aged parchment cardstock
- 1.5–2 pt black ink strokes with hand-wobble
- {color_instruction}

LAYOUT (inside the ornate border):
- TOP: Decorative header rule (hand-drawn line with arabesque flourish)
{verse_text_block}
EXPLANATION SECTION:
Three paragraphs of explanation text in warm hand-lettered serif style.

TEXT FIDELITY (CRITICAL — MOST COMMON MISTAKE):
Copy the text below WORD FOR WORD. Every word must be spelled correctly and match EXACTLY.
Do NOT invent, paraphrase, summarize, or approximate the text. NEVER write garbled or made-up words.

EXACT TEXT TO RENDER:
{back_text}

Key terms to render in BOLD with slight underline: {bold_terms}

FOOTER (CRITICAL — MUST BE PRESENT on back card, matching front card):
- Bottom-right corner: Draw a small hand-drawn ornate circle (25-30px diameter) with Islamic geometric border pattern
- INSIDE the circle: Write "{verse_ref_display}" — if empty, write "{card_number}"
- This verse reference circle MUST appear on the back card in the same position as the front card
- The circle should have a crescent moon small motif above or beside it
- This is the SAME footer element as the front card — readers need to match front and back

MARGINS: 8% padding inside the border

OUTPUT: Single card back image, same dimensions as front (380×540 ratio, portrait). TEXT ONLY — no diagrams."""


CARD_SPREAD_PROMPT_TEMPLATE = """Create a premium double-card mental model spread — two cards lying on a clean {bg_texture} desk surface, photographed from above.

CARD SURFACE & BORDER (BOTH cards must have this aged parchment look):
- Card surfaces: aged warm parchment with subtle paper grain texture — NOT flat white
- Edges: slightly darkened/vignette as if parchment is naturally aged and worn
- BORDER on BOTH cards: ornate Islamic geometric border frame around ALL 4 edges (2-3% width) — interlocking star-and-polygon tessellation pattern in thin ink with accent color wash fill
- CORNERS on BOTH cards: elaborate arabesque vine/floral corner flourishes extending ~8% from each corner — flowing organic curves with small leaf motifs
- Inner ruled line between border and content area on both cards

DRAWING TOOL (CRITICAL — replicate exactly):
- Simulate 0.5 mm Sakura Micron fineliner on aged parchment {card_bg} cardstock
- Outlines: 1.5–2 pt BLACK ink with slight hand-wobble (never digitally perfect)
- Shading: parallel hatching (45°, 2 mm spacing) or stipple dots — NEVER smooth gradients
- Fill: ONE flat accent color wash only — no blending
- Text: hand-lettered with natural baseline drift
- BANNED: anti-aliasing, airbrush, blur, drop shadows, 3D bevels, photorealism

COLOR RULE (STRICT — only 2 colors allowed):
- {color_instruction}
- Everything else: BLACK ink or PARCHMENT card surface — no extra colors

FRONT CARD (left, perfectly straight — no tilt):
  LAYOUT GRID (inside ornate border):
  - TOP BAND (20%): Title "{title}" — bold uppercase hand-lettered left | Category "{category}" — {category_placement}{verse_ref_line}
  - CENTER (55%): Main illustration filling zone with 10% internal margins
  - BOTTOM (15%): Italic hand-written quote{quote_extra}: "{quote}"
  - FOOTER (5%): Verse reference "{verse_ref_display}" in small {accent_shape} ornate circle with crescent motif bottom-right — if no verse reference, show card number "{card_number}" in crescent-decorated circle

  ILLUSTRATION:
  {illustration_description}

  ICON ENFORCEMENT:
  - Every labeled concept has a SPECIFIC recognizable icon (not blobs)
  - Icons: simple line-drawings, ~35px, consistent stroke weight
  - Hatching/stipple shading inside icons — no solid fills except accent wash

BACK CARD (right, perfectly straight — no tilt):
  THIS IS A TEXT-ONLY CARD — absolutely NO illustrations, NO diagrams, NO icons, NO flowcharts, NO images on the back card. Only hand-lettered text and decorative framing.
  Crescent moon small decorative motif integrated into the top border center.
  {verse_text_block}
  EXPLANATION SECTION (below the verse section, or from the top if no verse):
  Three paragraphs of explanation text in warm hand-lettered serif style.
  TEXT FIDELITY (CRITICAL — MOST COMMON MISTAKE):
  Copy the text below WORD FOR WORD. Every word must be spelled correctly and match EXACTLY.
  Do NOT invent, paraphrase, summarize, or approximate the text. If you cannot fit it all, truncate cleanly at a sentence boundary — but NEVER write garbled or made-up words.

  EXACT TEXT TO RENDER{back_text_content}

  Key terms to render in BOLD with slight underline: {bold_terms}

  FOOTER (CRITICAL — MUST match front card's footer):
  - Bottom-right corner: ornate circle with "{verse_ref_display}" inside — if empty, show "{card_number}"
  - This verse reference circle MUST appear on BOTH front and back cards in matching position
  - Crescent moon motif beside the circle
  MARGINS: 8% padding inside border

SPREAD DETAILS:
- Cards have soft rounded corners, subtle paper edge shadow on desk surface
- Both cards must have matching aged parchment appearance and ornate Islamic borders
- NO "Front" or "Back" labels — do NOT draw any labels or arrows outside the cards
- ~15px gap between cards
- Minimal desk surface visible around edges (keep it tight to the cards)

OUTPUT: Single landscape image containing both cards as a spread."""


# ---------- Illustration Descriptions by Model Type ----------

# Legacy prompts for backward compatibility (6 original visual types)
LEGACY_ILLUSTRATION_PROMPTS = {
    "sequential_chain": """A SEQUENTIAL CHAIN showing {num_steps} steps connected by hand-drawn arrows:
{steps_description}
Each step shown as a simple cartoon figure/icon with a label underneath.
Arrows (hand-drawn, textured) connect each step left-to-right.
Arabic text labels beneath each figure: {arabic_labels}""",

    "tripod": """A TRIPOD / THREE PILLARS structure:
{steps_description}
Three equal pillars/columns supporting a platform/beam on top.
Each pillar labeled with its concept. The platform represents the unified concept.
Hand-drawn architectural sketch style.""",

    "loop_cycle": """A CIRCULAR LOOP / CYCLE diagram with {num_steps} nodes:
{steps_description}
Nodes arranged in a circle, connected by curved hand-drawn arrows showing the cycle.
Each node is a simple icon with label. The cycle should feel continuous and self-reinforcing.
Perhaps show the loop getting tighter/stronger with each revolution.""",

    "fail_constraint": """A FAIL / CONSTRAINT METAPHOR illustration:
A hammer trying to drive a screw into wood — clearly the WRONG TOOL for the job.
The hammer is drawn with a red/yellow handle, the screw is being bent/damaged.
An "X" mark or red cross showing failure.
The concept: using a familiar tool inappropriately instead of the right one.""",

    "strategic_interlock": """A LOCK AND KEY / STRATEGIC FIT illustration:
A large lock on the left with a matching key approaching from the right.
Hand-drawn, simple sketch style. The key perfectly fits the lock.
Shows that precision matching is required — not brute force.
Perhaps show a wrong key (crossed out) and the right key.""",

    "mutual_gain": """A VENN DIAGRAM showing overlapping interests:
Two large circles overlapping in the center.
Left circle: "WHAT YOU WANT" — golden/yellow fill
Right circle: "WHAT THEY WANT" — golden/yellow fill
Overlap area: "WIN/WIN" — highlighted in warm accent color
An arrow pointing to the overlap area emphasizing the mutual gain zone.
Hand-drawn circles with rough, sketch-style edges.""",
}


def build_illustration_description(visual_type=None, model_type=None, steps=None, title="",
                                   arabic_terms=None, step_emotions=None):
    """Build the illustration description for the prompt.

    Enhanced with icon_library integration for specific, drawable icon descriptions.
    Delegates to get_illustration_prompt_for_visual_type() for all 20 visual types,
    then enriches with icon guidance from icon_library.

    Args:
        visual_type: Primary visual type identifier (one of 20 types from intelligent_matching)
        model_type: Legacy model type (optional, used if visual_type not provided)
        steps: List of step dicts with 'label', 'description', 'arabic' keys
        title: Card title for context
        arabic_terms: List of Arabic terms (for legacy support)
        step_emotions: List of dicts with 'label' and 'emotion' keys from LLM Phase 2
                       (passed through to illustration prompt for per-panel hero emotions)

    Returns:
        Detailed illustration description string with icon enrichment
    """
    card_data = {
        "steps": steps or [],
        "title": title,
        "arabic_terms": arabic_terms or [],
        "step_emotions": step_emotions or [],
    }

    # Determine which visual_type to use
    effective_visual_type = visual_type
    if not effective_visual_type and model_type:
        effective_visual_type = LEGACY_MODEL_TYPES.get(model_type, "sequential_chain")
    if not effective_visual_type:
        effective_visual_type = "sequential_chain"

    # Get base illustration prompt from intelligent_matching
    try:
        base_prompt = get_illustration_prompt_for_visual_type(effective_visual_type, card_data)
    except Exception:
        if model_type and model_type in LEGACY_ILLUSTRATION_PROMPTS:
            template = LEGACY_ILLUSTRATION_PROMPTS[model_type]
            steps_desc = "\n".join([
                f"  Step {i+1}: {s['label']} — {s.get('description', '')}"
                for i, s in enumerate(steps or [])
            ])
            arabic_labels = ", ".join([
                s.get('arabic', '') for s in (steps or []) if s.get('arabic')
            ]) or "None"
            base_prompt = template.format(
                num_steps=len(steps or []),
                steps_description=steps_desc,
                arabic_labels=arabic_labels
            )
        else:
            base_prompt = "A simple conceptual hand-drawn diagram illustrating the mental model with labeled elements."

    # Enrich with icon_library guidance
    if steps:
        # First, get icons for each step
        icon_steps = get_icons_for_steps(steps, effective_visual_type)
        # Then enforce divine icon guardrails (override any potentially human icons for Allah/God)
        icon_steps = enforce_divine_icon_guardrails(icon_steps)
        # Now build the enriched text with the guarded icons
        icon_enriched = build_icon_enriched_steps(icon_steps, effective_visual_type)
        if icon_enriched:
            base_prompt += f"\n\nSPECIFIC ICONS FOR EACH ELEMENT:\n{icon_enriched}"

    # Add structural guidance from icon_library
    guidance = get_structural_guidance(effective_visual_type)
    if guidance:
        structural_note = (
            f"\n\nSTRUCTURAL DRAWING GUIDE: "
            f"Connectors: {guidance.get('connector', 'arrows')}. "
            f"Node shapes: {guidance.get('node_shape', 'bordered shapes')}. "
            f"{guidance.get('style_note', '')}"
        )
        base_prompt += structural_note

    return base_prompt


def _build_hero_block(visual_type="sequential_chain", card_data=None):
    """Build the hero character prompt block as a standalone section.

    Kept separate from illustration description so prompt budget trimming
    can preserve the hero while trimming icon/structural details.
    COLOR RULE: Hero is drawn using ONLY the card's existing 2-color palette
    (black ink + accent color). No extra skin tones, no extra hoodie colors.

    The hero is styled as a YOUNG, SHARP, 3D cartoon character (Pixar/Disney style
    adapted to sketchnote ink rendering) — NOT a generic adult or older man.
    Face expressions match the card's emotional content.

    For MULTI-PANEL visual types (comparison, matrix_2x2, sequential_chain, etc.),
    the hero appears in EACH panel with a DIFFERENT emotion matching that panel's message.
    """
    pose = suggest_pose_for_visual_type(visual_type)

    # Determine emotional expression based on card content (used as default/overall)
    emotion = _get_hero_emotion(visual_type, card_data)

    # Check if this is a multi-panel type that needs per-step emotions
    steps = card_data.get("steps", []) if card_data else []
    multi_panel_types = {
        "comparison", "matrix_2x2", "sequential_chain", "cycle_loop",
        "pyramid_hierarchy", "funnel", "timeline", "force_diagram"
    }
    is_multi_panel = visual_type in multi_panel_types and len(steps) >= 2

    # Build per-step emotion block for multi-panel cards
    per_step_block = ""
    if is_multi_panel:
        per_step_block = _build_per_step_emotion_block(steps, card_data)

    base_block = (
        f"\n\nHERO CHARACTER (SAME youthful character on EVERY card — card's 2 colors ONLY):\n"
        f"CHARACTER IDENTITY LOCK — draw this EXACT SAME person every time. These 5 IMMUTABLE features MUST appear on every rendering:\n"
        f"  1. LEFT-parted dark swooping hair swept RIGHT across forehead\n"
        f"  2. LEFT eyebrow arched HIGHER than right (facial asymmetry signature)\n"
        f"  3. Light SHORT beard (neatly trimmed, visible jawline outline) — NOT clean-shaven, NOT full bushy beard\n"
        f"  4. Charcoal hoodie with golden Islamic star/arabesque patterns\n"
        f"  5. Slim build, slightly large head in 3D cartoon proportions\n\n"
        f"DETAILED FACE SPEC (reproduce EXACTLY — these features define THIS character):\n"
        f"- Age: Young Muslim man, EARLY 20s — youthful energy, NOT middle-aged\n"
        f"- Hair: Parted LEFT, swept RIGHT over forehead, dark brown almost-black, voluminous wavy with visible individual strands, slightly tousled\n"
        f"- Face shape: Slightly oval with DEFINED cheekbones, softly pointed chin, strong jawline visible through the beard\n"
        f"- Eyes: Large almond-shaped, dark brown iris, thick upper lashes, small white sparkle highlight in each eye, slightly downturned outer corners giving a kind/warm look\n"
        f"- Eyebrows: Thick well-groomed arched brows — LEFT eyebrow positioned HIGHER than right (this asymmetry is his SIGNATURE LOOK)\n"
        f"- Nose: Small straight nose, drawn as a simple angular ink line with minimal shading\n"
        f"- Beard/facial hair: Light SHORT trimmed beard — thin ink stipple dots along jawline, chin, and upper lip forming a neat connected beard outline. "
        f"NOT heavy or bushy — you can see the jawline shape THROUGH the beard. Think '3-day stubble grown to short trim'. "
        f"The beard should be the SAME density and pattern in every rendering.\n"
        f"- Mouth: Small, expressive — changes with emotion but always proportionate to face\n"
        f"- Ears: Partially visible behind hair, simple curved line\n"
        f"- 3D cartoon proportions adapted to ink sketch: slightly large head (~1.2x normal), big expressive eyes, sharp defined jawline\n"
    )

    if is_multi_panel:
        # For multi-panel: hero appears in EACH panel with different expression
        base_block += (
            f"The hero appears in EACH panel/segment of this card with a COMPLETELY DIFFERENT body posture AND facial expression "
            f"matching that panel's theological/spiritual meaning — NOT just subtle face tweaks. "
            f"Each panel requires a FULL BODY POSE CHANGE: different head angle, different shoulder position, different hand placement, different body lean. "
            f"For Islamic spiritual concepts: Humility = body SMALL and bowed. Worship = body in prayer posture. Awe = body pulled back. Recognition = body stiffened with hand on heart. "
        )
    else:
        # For single-panel: one overall expression
        base_block += (
            f"FACE EXPRESSION: {emotion} — the face MUST convey this emotion clearly through "
            f"eye shape, eyebrow angle, and mouth curve. "
        )

    base_block += (
        f"\nCLOTHING (consistent across all cards):\n"
        f"- Hoodie: Charcoal/dark gray base with golden (#C8902E) 8-point Islamic star patterns and arabesque tessellations printed on it. "
        f"Drawstrings visible, hood DOWN always. The pattern coverage is medium — stars/arabesques are scattered, not covering every inch.\n"
        f"- Pants: Slim-fit dark jeans tapered at ankles\n"
        f"- Shoes: White low-top sneakers with accent color laces\n\n"
        f"SKIN RENDERING (CRITICAL — MOST COMMON MISTAKE TO AVOID):\n"
        f"The hero's skin (face, hands, neck, any visible body) is rendered as BLANK WHITE PAPER "
        f"with BLACK INK outlines ONLY — exactly like a manga or Tintin character. "
        f"The face is the SAME white/parchment as the card background surface, with black ink lines defining features. "
        f"DO NOT add ANY skin color — no beige, no tan, no peach, no warm tones, no shading on skin areas. "
        f"Hair is solid BLACK ink fill. Beard stipple dots are BLACK ink on white skin. "
        f"Hoodie patterns use the card's accent color wash only.\n\n"
        f"CHARACTER CONSISTENCY CHECK — before finalizing, verify these are ALL present:\n"
        f"  [x] Left-parted hair swept right  [x] Left eyebrow higher than right\n"
        f"  [x] Light short trimmed beard      [x] Charcoal hoodie with gold Islamic patterns\n"
        f"  [x] White skin (no color fill)     [x] Almond eyes with sparkle highlights\n\n"
        f"POSE: {pose} — naturally interacting with the diagram, not just standing beside it."
    )

    # Append per-step emotions AFTER the base hero block
    if per_step_block:
        base_block += per_step_block

    return base_block


def _get_hero_emotion(visual_type="sequential_chain", card_data=None):
    """Determine the hero's facial expression based on card content and visual type.

    For single-panel cards (non-multi-panel types or cards with <2 steps).
    Uses LLM-provided step_emotions if available, else falls back to
    visual type + title keyword heuristics.
    """
    # Try LLM-provided emotions first (most intelligent)
    if card_data:
        llm_emotions = _get_llm_step_emotions(card_data)
        if llm_emotions:
            # For single-panel rendering, use the first step's emotion as overall tone
            return llm_emotions[0][1]

    # Fallback: visual type → emotion mapping
    type_emotions = {
        "sequential_chain": "curious and engaged — eyes wide with interest, slight smile with mouth slightly open, leaning forward with energy",
        "cycle_loop": "thoughtful realization — eyebrows raised with dawning understanding, mouth slightly open in 'oh!', head tilting slightly",
        "tripod": "confident and steady — relaxed genuine smile, eyes calm and warm, chin slightly raised with quiet strength",
        "pyramid_hierarchy": "looking upward with aspiration — wide eyes gazing upward with hope, eyebrows lifted, slight hopeful smile",
        "scale_balance": "concerned and weighing — eyebrows furrowed together, lips pressed firmly together, head tilted as if calculating",
        "iceberg": "shocked discovery — eyes wide with surprise, eyebrows raised high, mouth open in genuine shock, leaning back",
        "venn_diagram": "contemplative — eyes narrowed slightly in thought, head tilted to one side, one hand raised to chin in reflection",
        "comparison": "analytical focus — one eyebrow raised higher than the other in evaluation, eyes sharp and focused, slight knowing smirk",
        "force_diagram": "tense determination — jaw clenched with focused intensity, eyes narrowed and burning, eyebrows drawn down together firmly",
        "funnel": "patient focus — eyes calm and steady, eyebrows relaxed and level, gentle nod of understanding, shoulders settled",
        "decision_tree": "puzzled but processing — one eyebrow raised in question, slight frown of thought, finger touching temple in concentration",
        "matrix_2x2": "organized clarity — satisfied smile showing understanding, eyes relaxed and clear, head giving slight nod of comprehension",
        "fishbone": "detective mode — eyes narrowed in investigation, eyebrows drawn slightly together, slight lean forward, examining gaze",
        "network_graph": "excited connection — eyes bright and shining, wide enthusiastic smile, eyebrows raised with excitement, animated energy",
        "timeline": "reflective wisdom — eyes gentle and soft, slight nostalgic smile, gaze looking slightly into distance with reflection",
        "s_curve": "patient anticipation — knowing confident smile, eyes focused ahead on the path, eyebrows level with calm assurance",
        "exponential_curve": "amazed by growth — eyes wide with astonishment, jaw slightly dropped, eyebrows raised high in amazement",
        "flow_chart": "methodical focus — gaze steady and concentrated, mouth in neutral line, eyebrows level, entire face composed and focused",
        "spectrum": "carefully measuring — squinting slightly with one eye, head tilted in evaluation, eyes sharp with discernment",
        "nested_circles": "deep inner peace — eyes gently closed or nearly closed, soft serene smile, face completely relaxed and centered",
    }

    emotion = type_emotions.get(visual_type, "curious and engaged — eyes wide, slight smile")

    # Override with card-specific emotional context if available
    if card_data:
        title = (card_data.get("card_title") or card_data.get("title", "")).lower()
        # Detect emotional tone from title/content
        if any(w in title for w in ["struggle", "trap", "fail", "sin", "temptation", "danger"]):
            emotion = "worried concern — furrowed brows, worried eyes, lips pressed tight"
        elif any(w in title for w in ["love", "mercy", "blessing", "paradise", "hope"]):
            emotion = "warm gratitude — soft eyes, gentle genuine smile, peaceful expression"
        elif any(w in title for w in ["power", "strength", "victory", "conquer"]):
            emotion = "determined confidence — firm jaw, focused eyes, slight upward chin"
        elif any(w in title for w in ["wisdom", "knowledge", "insight", "truth"]):
            emotion = "enlightened wonder — bright wide eyes with sparkle, amazed half-smile"
        elif any(w in title for w in ["warning", "punishment", "consequence", "destruction"]):
            emotion = "sobered awareness — serious eyes, tight mouth, slightly pulled-back posture"

    return emotion


# ---------- Per-Segment Emotion Keywords ----------
# Keyword → emotion mapping used to derive facial expressions for EACH step/panel

_POSITIVE_KEYWORDS = {
    "faith": "warm gratitude and inner peace — eyes softened with closed upper lids, corners of mouth lifted in genuine smile, shoulders relaxed downward, hand over heart in serene expression",
    "true": "warm gratitude and inner peace — eyes softened with closed upper lids, corners of mouth lifted in genuine smile, shoulders relaxed downward, hand over heart in serene expression",
    "worship": "devoted worship (ibadah) — head bowed LOW with chin nearly touching chest, eyes CLOSED in deep spiritual submission, hands raised in dua palms-up near face, shoulders curved INWARD, entire body oriented DOWNWARD in servitude — NOT smiling, NOT looking at viewer, posture communicates total surrender to Allah",
    "ibadah": "devoted worship (ibadah) — head bowed LOW with chin nearly touching chest, eyes CLOSED in deep spiritual submission, hands raised in dua palms-up near face, shoulders curved INWARD, entire body oriented DOWNWARD in servitude — NOT smiling, NOT looking at viewer, posture communicates total surrender to Allah",
    "na'budu": "worshipful devotion — body bent forward in ruku-like posture, eyes closed with deep reverence, hands on knees or raised in supplication, face showing profound awe and submission, mouth slightly open in silent dhikr — this is ACTIVE WORSHIP not passive observation",
    "sincere": "deep sincerity — warm open eyes with visible earnestness, eyebrows drawn slightly inward, heartfelt smile showing bottom teeth, hand placed firmly on chest over heart",
    "paradise": "joyful hope — eyes wide and bright with visible sparkle highlights, eyebrows raised high, beaming smile with cheeks lifted, gaze lifted slightly upward",
    "blessing": "grateful joy — eyes slightly glistening with moisture, corner of mouth pulled up in warm smile, both hands slightly raised with palms facing upward in gratitude gesture",
    "mercy": "tender compassion — eyes soft and warm, eyebrows slightly lowered with empathy, gentle smile with slight downward curve at mouth corners, head tilted slightly toward subject",
    "love": "warm overflowing love — eyes sparkling brightly with visible highlights, eyebrows raised and relaxed, wide heartfelt smile with teeth showing, arms open in welcoming gesture",
    "hope": "bright optimism — eyes wide and shining with visible sparkle, eyebrows raised with hope, slight hopeful smile, gaze directed slightly upward toward horizon",
    "knowledge": "enlightened wonder — bright wide eyes with visible sparkle dots, eyebrows raised in amazement, half-smile with slight opening of mouth in wonder, head tilted back slightly",
    "wisdom": "deep contemplation — eyes warm and knowing, eyebrows softly arched, thoughtful gentle smile, one hand near chin in contemplative pose, gaze forward with quiet confidence",
    "guidance": "confident clarity — eyes focused and bright, eyebrows steady and confident, calm assured smile with mouth firmly closed, shoulders back and chest open",
    "victory": "triumphant determination — jaw set firmly with quiet strength, eyes bright with confident fire, fist raised with energy but controlled, chin raised with pride",
    "success": "proud accomplishment — beaming wide smile with cheeks lifted, confident eyes with visible sparkle, chin slightly raised with pride, chest slightly puffed out",
    "peace": "serene tranquility — eyes closed gently, eyebrows relaxed and smooth, soft gentle smile, face completely slack and relaxed, shoulders dropped and comfortable",
    "trust": "calm confidence — eyes steady and warm with direct gaze, eyebrows level and composed, assured gentle smile, posture upright and grounded",
    "gratitude": "overflowing thankfulness — eyes slightly glistening with tears of joy, eyebrows softly raised, wide genuine smile, both hands raised with palms open in thanksgiving",
    "patience": "calm endurance — eyes steady and focused, eyebrows level and composed, slight smile showing dignified strength, jaw relaxed but firm, posture solid and grounded",
    "repent": "hopeful relief — eyes teary with catharsis but smiling softly, eyebrows raised with hope, weight visibly lifted from shoulders, head starting to turn toward light",
    "forgive": "compassionate release — eyes soft and warm with understanding, eyebrows slightly lowered with empathy, gentle forgiving smile, hand extended in peace gesture",
    # --- Islamic Spiritual States (precise physical expressions) ---
    "humility": "deep humility (khushu) — head BOWED LOW with chin toward chest, eyes cast FULLY DOWNWARD looking at ground, shoulders rounded INWARD making body small, hands clasped together LOW near waist or resting on thighs, entire posture SHRUNK and LOWERED — expressing total self-effacement before Allah, NOT thinking, NOT looking forward",
    "humble": "deep humility (khushu) — head BOWED LOW with chin toward chest, eyes cast FULLY DOWNWARD looking at ground, shoulders rounded INWARD making body small, hands clasped together LOW near waist or resting on thighs, entire posture SHRUNK and LOWERED — expressing total self-effacement before Allah, NOT thinking, NOT looking forward",
    "khushu": "deep spiritual concentration — eyes CLOSED with visible calm, eyebrows relaxed NOT furrowed, face peaceful and still, body motionless in prayer-like stillness, hands placed on chest or on knees, shoulders gently sloped — the stillness of one completely absorbed in connection with Allah",
    "tawakkul": "serene surrender and trust in Allah — eyes gently closed with relaxed eyelids, face radiating calm acceptance, slight peaceful smile, shoulders completely relaxed and dropped, palms open and facing upward at sides in gesture of releasing control — NOT passive, but actively PEACEFUL",
    "taqwa": "alert spiritual vigilance — eyes WIDE and watchful scanning surroundings, eyebrows slightly raised in heightened awareness, jaw firm with readiness, body in slight forward lean of alertness, one hand near heart — protective consciousness of Allah watching, the careful walk of one on a narrow path",
    "sabr": "dignified patient endurance — jaw set firmly with quiet resolve, eyes steady and UNWAVERING looking straight ahead, slight upward tilt of chin showing strength not defeat, shoulders bearing weight but standing TALL, fists gently clenched at sides — nobility under pressure, NOT passive suffering",
    "shukr": "overflowing gratitude to Allah — eyes glistening with tears of thankfulness, eyebrows raised with wonder, wide genuine smile, both hands raised with palms OPEN facing sky in traditional Islamic gratitude gesture, head tilted slightly back looking upward",
    "tawbah": "repentant return to Allah — eyes filled with tears but facing UPWARD toward light with hope, eyebrows drawn together with remorse, mouth slightly trembling, one hand on heart and other reaching upward, body transitioning from hunched to rising — the turning motion of return",
    "dhikr": "absorbed remembrance of Allah — eyes closed in meditative focus, lips slightly moving in silent recitation, face serene and glowing with inner light, prayer beads in one hand, body swaying very slightly with rhythmic remembrance, completely oblivious to surroundings",
    "yaqeen": "unshakeable certainty — eyes BRIGHT and clear with absolutely steady gaze, no wavering, chin slightly raised with grounded confidence, chest open and expanded, feet firmly planted wide, both hands relaxed at sides — rock-solid inner conviction radiating outward",
    "ikhlas": "pure sincerity — eyes clear and guileless looking directly forward, face completely open with no artifice, gentle earnest expression, hand firmly on chest over heart, posture upright and unguarded — transparent devotion without any self-consciousness",
    "tafakkur": "deep Islamic contemplation — eyes gazing UPWARD at sky or into distance with wonder, eyebrows slightly raised in intellectual awe, mouth slightly parted, one hand touching chin lightly, body still but mind visibly active — contemplating Allah's signs in creation, NOT just generic thinking",
    "submission": "complete submission to Allah — body bowed forward at waist, head lowered, eyes directed downward, arms relaxed and hanging or hands on knees in ruku-like posture, face showing PEACE not fear — the willing surrender of one who knows their Lord",
    "devotion": "intense devotion — eyes half-closed with spiritual focus, face turned slightly upward, eyebrows softly raised, lips moving in silent prayer, both hands raised at chest level with palms up in dua position, body leaning slightly forward toward qibla",
    "elevation": "spiritual ascent — eyes looking UPWARD with hope and wonder, body positioned HIGHER or rising, arms slightly lifted, face radiating growing illumination, chin raised, chest expanded — the physical sensation of being drawn closer to the Divine",
    "recognition": "profound realization and acknowledgment — eyes WIDENING with sudden deep understanding, eyebrows raised HIGH, mouth slightly open with the weight of recognition, one hand rising to heart, body STIFFENING with the gravity of truth — NOT casual awareness but earth-shaking recognition of divine truth",
    "nasta'een": "seeking help from Allah alone — hands raised HIGH in earnest supplication with palms open toward sky, eyes looking upward with vulnerable dependence, eyebrows drawn together with need, face showing both vulnerability AND hope — the posture of one who has no other source of aid",
    "sovereignty": "awestruck reverence at divine majesty — eyes WIDE with wonder, mouth slightly agape, body pulled slightly backward by the magnitude, one hand on chest, head tilted back to look up at something infinitely vast — overwhelmed by divine greatness",
    "revelation": "receiving divine truth — eyes wide and illuminated with understanding, face bathed in upward light, body perfectly still in receptive posture, hands open at sides palm-up, expression of profound awe mixed with gratitude — the moment truth enters the heart",
}

_NEGATIVE_KEYWORDS = {
    "sin": "guilt and sorrow — eyes downcast with heavy lids, eyebrows drawn down and together, mouth corners pulled down in frown, face weighted with heaviness and remorse",
    "sinner": "guilt and sorrow — eyes downcast with heavy lids, eyebrows drawn down and together, mouth corners pulled down in frown, face weighted with heaviness and remorse",
    "corruption": "disgusted sadness — eyes narrowed in disgust, nostrils flared slightly, mouth tight in recoil, body turned slightly away with shoulders hunched",
    "shirk": "deep distress — eyes wide with alarm and hurt, eyebrows raised toward center of brow in anguish, mouth slightly agape in shock, body pulling backward defensively",
    "hypocrisy": "uncomfortable unease — eyes darting nervously side-to-side, eyebrows twitching slightly, forced awkward half-smile that doesn't reach eyes, jaw clenched tight",
    "hypocrit": "uncomfortable unease — eyes darting nervously side-to-side, eyebrows twitching slightly, forced awkward half-smile that doesn't reach eyes, jaw clenched tight",
    "punishment": "sobered fear — eyes widened with fear, eyebrows raised and pulled inward, lips pressed thin and pale, body shrinking and shoulders hunched protectively",
    "hellfire": "terrified alarm — eyes wide with visible whites showing terror, eyebrows raised maximally, mouth agape in shock, hands raised defensively in front of face",
    "destruction": "devastated shock — eyes wide and hollow with emptiness, eyebrows raised, jaw dropped open slackly, arms limp and hanging without energy",
    "danger": "alarmed vigilance — eyes sharp and alert with intensity, eyebrows raised and focused, jaw tensed and clenched, body leaning back in defensive posture",
    "warning": "worried concern — eyebrows furrowed down and together tightly, eyes narrowed with worry, lips pressed firmly together, forehead creased with anxiety lines",
    "trap": "anxious awareness — eyes darting in multiple directions nervously, eyebrows raised with tension, lower lip being subtly bitten, shoulders held up tensely",
    "temptation": "inner struggle — eyes conflicted and uncertain, eyebrows furrowed with internal conflict, one hand reaching forward while other pulls back, jaw clenched slightly",
    "fail": "disappointed frustration — eyes drooping downward with disappointment, eyebrows lowered sadly, mouth turned down in slight frown, shoulders slumped forward",
    "loss": "profound grief — eyes downcast and glistening with tears, eyebrows drawn inward with sorrow, lower lip trembling slightly, hand clutching at chest",
    "greed": "restless craving — eyes wide and hungry with intensity, eyebrows raised with eagerness, nostrils flared in desire, hands grasping and leaning forward tensely",
    "arrogance": "foolish pride — chin held too high with false confidence, eyes looking down with disdain, mouth in smug dangerous smirk, nostrils slightly flared",
    "ignorance": "confused darkness — eyes squinting in confusion and lost, eyebrows raised questioningly, mouth open in confused expression, hand scratching head in bewilderment",
    "despair": "crushing hopelessness — eyes hollow and empty without light, eyebrows completely relaxed with surrender, mouth slack and expressionless, entire posture collapsed inward",
    "injustice": "righteous anger — eyes burning with fierce intensity, eyebrows drawn down sharply in anger, jaw clenched tightly with tension, fists balled up firmly",
    "oppression": "burdened suffering — eyes crushed downward with weight, eyebrows heavy and drawn together, mouth slightly frowning, shoulders caved inward under burden",
}

_NEUTRAL_KEYWORDS = {
    "materialism": "restless dissatisfaction — eyes darting unsettled in multiple directions, mouth tight and uneasy, shoulders fidgeting slightly, one foot tapping impatiently",
    "worldly": "distracted wandering — eyes unfocused and pulled in different directions, eyebrows slightly raised, mouth slightly downturned, gaze never settling on one point",
    "wealth": "cautious weighing — one eyebrow raised higher than the other, eyes narrowing in calculation, lips pursed thoughtfully, head tilted slightly to one side",
    "test": "determined resolve — eyes focused intently on the challenge, eyebrows set firmly level, jaw set with quiet determination, posture upright and alert",
    "struggle": "effortful strain — teeth slightly gritted with effort, eyes squinting with focused intensity, shoulders tensed, body leaning forward in pushing motion",
    "journey": "curious anticipation — eyes wide and exploring with interest, eyebrows raised with excitement, slight excited smile, body leaning forward with eagerness",
    "change": "uncertain openness — eyebrows raised with openness and uncertainty, lips slightly parted as if about to speak, eyes searching for understanding, head tilted slightly",
    "choice": "deliberate weighing — one eyebrow raised up while other stays neutral, one finger touching chin in contemplation, slight thoughtful frown, eyes looking to one side",
    "balance": "careful equilibrium — eyes level and steady with direct gaze, eyebrows perfectly level and composed, mouth in neutral straight line, posture perfectly centered",
    "question": "puzzled inquiry — head tilted to one side with curiosity, one eyebrow raised in question, slight frown of confusion, mouth slightly open as if wondering",
    # --- Islamic transitional / mixed states ---
    "straight path": "focused determination on sirat al-mustaqeem — eyes locked STRAIGHT AHEAD on a single point with laser focus, jaw firm, body walking forward with purposeful stride, arms at sides with fists gently clenched — walking a narrow bridge with total concentration",
    "sirat": "careful traversal — eyes focused intensely on path ahead, arms slightly out for balance, body in careful measured stride, face showing concentration mixed with hope — walking the narrow path between extremes",
    "fitrah": "innocent natural state — eyes wide and clear like a child, face open and unguarded, slight wonder at surroundings, body relaxed and natural — the original pure state before corruption",
    "nafs": "inner struggle with self — eyebrows drawn together in internal conflict, one hand pushing away while other pulls toward, face showing tension between desire and discipline, jaw clenched — the battle within",
    "dunya": "torn attachment — eyes glancing sideways at worldly attraction while body leans away, face showing conflicted desire, hand reaching but pulling back — the pull of temporary pleasures vs eternal truth",
    "akhirah": "eyes-on-eternity — gaze directed FAR into the distance beyond visible horizon, eyes slightly narrowed with longing, face showing bittersweet yearning, body oriented toward the unseen — contemplating the eternal life to come",
}


def _keyword_in_text(keyword, text):
    """Check if keyword appears as a whole word in text.

    Prevents false matches like 'sin' inside 'sincere' or 'fail' inside 'faithful'.
    Uses regex word boundaries on BOTH sides for exact whole-word matching.
    """
    import re
    pattern = r'\b' + re.escape(keyword) + r'\b'
    return bool(re.search(pattern, text))


def _get_per_step_emotions(steps, card_data=None):
    """Generate a specific emotion/expression for EACH step in a multi-panel card.

    This is the key function for per-segment hero emotions. Instead of one emotion
    for the whole card, each panel/step gets its own expression based on that
    step's label and description content.

    Args:
        steps: List of step dicts with 'label', 'description' keys
        card_data: Optional card data for additional context

    Returns:
        List of (step_label, emotion_description) tuples, one per step
    """
    if not steps:
        return []

    results = []
    all_keywords = {}
    all_keywords.update(_POSITIVE_KEYWORDS)
    all_keywords.update(_NEGATIVE_KEYWORDS)
    all_keywords.update(_NEUTRAL_KEYWORDS)

    for step in steps:
        label = (step.get("label") or "").lower()
        desc = (step.get("description") or "").lower()

        # PRIORITY LOGIC:
        # 1. Check label for negative keywords first (catches "Shirk", "Sin" etc.)
        # 2. Check label for neutral keywords
        # 3. Check label for positive keywords — BUT cross-check against description
        #    for negative override (catches "Love With Allah" whose desc says "shirk/polytheism")
        # 4. Fall back to full combined text

        best_match = None
        best_match_len = 0
        label_matched_positive = False  # Track if we matched positive from label

        # 1) Check label against negative keywords FIRST (highest priority)
        for keyword, emotion in _NEGATIVE_KEYWORDS.items():
            if _keyword_in_text(keyword, label) and len(keyword) > best_match_len:
                best_match = emotion
                best_match_len = len(keyword)

        # 2) If no negative match in label, check label against neutral keywords
        if not best_match:
            for keyword, emotion in _NEUTRAL_KEYWORDS.items():
                if _keyword_in_text(keyword, label) and len(keyword) > best_match_len:
                    best_match = emotion
                    best_match_len = len(keyword)

        # 3) If no negative/neutral match in label, check label against positive keywords
        if not best_match:
            for keyword, emotion in _POSITIVE_KEYWORDS.items():
                if _keyword_in_text(keyword, label) and len(keyword) > best_match_len:
                    best_match = emotion
                    best_match_len = len(keyword)
                    label_matched_positive = True

        # 3b) CROSS-CHECK: If label matched positive, check if description contains
        #     STRONG negative signals that contradict the label's positivity.
        #     Example: "Love With Allah" label → positive "love" match, but description
        #     says "shirk", "polytheism", "rivals" → override to negative.
        if label_matched_positive and desc:
            desc_neg_match = None
            desc_neg_len = 0
            for keyword, emotion in _NEGATIVE_KEYWORDS.items():
                if _keyword_in_text(keyword, desc) and len(keyword) > desc_neg_len:
                    desc_neg_match = emotion
                    desc_neg_len = len(keyword)
            # Also check for strong negative tone words in description
            if not desc_neg_match:
                for keyword, emotion in _NEUTRAL_KEYWORDS.items():
                    if _keyword_in_text(keyword, desc) and len(keyword) > desc_neg_len:
                        desc_neg_match = emotion
                        desc_neg_len = len(keyword)
            if desc_neg_match:
                # Description contradicts label's positivity — override
                best_match = desc_neg_match
                best_match_len = desc_neg_len

        # 4) If no label match at all, check full combined text (label + description)
        if not best_match:
            combined = f"{label} {desc}"
            for keyword, emotion in all_keywords.items():
                if _keyword_in_text(keyword, combined) and len(keyword) > best_match_len:
                    best_match = emotion
                    best_match_len = len(keyword)

        if best_match:
            results.append((step.get("label", ""), best_match))
        else:
            # Fallback: infer from general tone
            # Check if step seems positive, negative, or neutral
            positive_signals = ["good", "right", "correct", "best", "ideal", "pure", "strong",
                                "grow", "rise", "light", "reward", "achieve", "noble"]
            negative_signals = ["bad", "wrong", "evil", "weak", "dark", "fall", "decline",
                                "reject", "deny", "hate", "harm", "fear", "pain", "broken"]

            pos_count = sum(1 for w in positive_signals if w in combined)
            neg_count = sum(1 for w in negative_signals if w in combined)

            if pos_count > neg_count:
                results.append((step.get("label", ""),
                                "positive engagement — bright eyes, warm smile, open posture"))
            elif neg_count > pos_count:
                results.append((step.get("label", ""),
                                "troubled concern — furrowed brows, worried eyes, tense mouth"))
            else:
                results.append((step.get("label", ""),
                                "thoughtful contemplation — focused eyes, neutral composed expression"))

    return results


def _get_llm_step_emotions(card_data):
    """Extract LLM-generated step emotions from card_data if available.

    The Phase 2 LLM analysis now outputs a step_emotions array alongside steps.
    This is the PRIMARY source — much more intelligent than keyword matching because
    the LLM understands theological context, surface-vs-actual meaning, and nuance.

    Returns:
        List of (label, emotion) tuples if LLM emotions available, else None
    """
    step_emotions = card_data.get("step_emotions") if card_data else None
    if not step_emotions or not isinstance(step_emotions, list):
        return None

    results = []
    for entry in step_emotions:
        if isinstance(entry, dict):
            label = entry.get("label", "")
            emotion = entry.get("emotion", "")
            if label and emotion:
                results.append((label, emotion))

    # Only use if we got emotions for at least 2 steps
    return results if len(results) >= 2 else None


def _build_per_step_emotion_block(steps, card_data=None):
    """Build the per-segment hero emotion directive to inject into prompts.

    Uses a 2-tier strategy:
      1. PRIMARY: LLM-generated step_emotions from Phase 2 analysis
         (deeply understands theological context, surface-vs-actual meaning)
      2. FALLBACK: Keyword-based emotion detection
         (for backward compatibility, legacy single-shot, or when LLM field is missing)

    Returns a string block that instructs the image generator to show different
    hero emotions in different panels/segments of multi-panel cards.
    """
    # Tier 1: Try LLM-generated emotions (primary — intelligent, context-aware)
    emotions = _get_llm_step_emotions(card_data)
    source = "llm"

    # Tier 2: Fall back to keyword-based detection
    if not emotions:
        emotions = _get_per_step_emotions(steps, card_data)
        source = "keyword"

    if not emotions or len(emotions) < 2:
        return ""

    lines = [
        "\n\nHERO EXPRESSION PER PANEL (CRITICAL — THE MOST IMPORTANT VISUAL ELEMENT IN EACH PANEL):",
        "The hero character's ENTIRE BODY POSTURE and FACE must change dramatically between panels.",
        "Each panel tells a different part of the spiritual story — the hero PHYSICALLY EMBODIES that state.\n",
    ]
    for i, (label, emotion) in enumerate(emotions):
        lines.append(f'  Panel {i+1} ("{label}"): Hero MUST show: {emotion}')

    lines.append(
        "\nEXPRESSION QUALITY RULES (MANDATORY — violation makes the card WRONG):\n"
        "- The hero's face MUST be drawn LARGE enough in each panel for the expression to be clearly readable\n"
        "- FULL BODY changes between panels: head angle, shoulder position, hand placement, body lean, posture height — NOT just facial tweaks\n"
        "- Eyes, eyebrows, mouth, head tilt, shoulder angle, and hand position must ALL change between panels\n"
        "- THEOLOGICAL PRECISION: If a panel says 'Humility' the hero MUST show physical humility (head bowed, eyes down, body small) — NOT a thinking face\n"
        "- If a panel says 'Worship' the hero MUST be in a worship posture (bowed, hands in dua, eyes closed) — NOT smiling or standing casually\n"
        "- BANNED DEFAULT EXPRESSIONS: Do NOT use 'thinking face', 'slight smile', or 'neutral gaze' for ANY Islamic spiritual concept. These are LAZY and WRONG.\n"
        "- BODY POSTURE communicates more than face alone. Humility = SMALL body. Worship = BOWED body. Awe = body PULLED BACK. Devotion = body LEANED FORWARD.\n"
        "- Use the FULL spiritual vocabulary: reverence, awe, submission, surrender, devotion, vigilance, yearning, trembling, weeping, supplication, absorption"
    )

    # Log which source was used for debugging
    print(f"[hero_emotions] Using {source}-based emotions for {len(emotions)} panels")

    return "\n".join(lines)


def build_color_instruction(theme, is_islamic_content=False):
    """Build strict 2-color instruction based on theme.

    RULE: Only BLACK ink + ONE accent color. No exceptions.
    Islamic content uses same palette (proven to produce better results).
    """
    if theme == "warm_parchment":
        return ("ONLY 2 colors allowed — black ink lines + golden amber (#C8902E) flat wash. "
                "Card surface: aged warm parchment (#F5E6C8 to #FDF3E0) with subtle paper grain texture "
                "and slightly darkened edges (vignette effect as if naturally aged). "
                "Text: dark brown (#4A2E0A) or black. "
                "NO other colors. NO teal. NO blue. NO red. Just black + gold on parchment.")
    else:
        return ("ONLY 2 colors allowed — black ink lines + soft teal (#4A9B7F) flat wash. "
                "Card surface: light cream parchment (#F8F6F0) with very subtle paper grain. "
                "Text: dark navy (#1A2530) or black. "
                "NO other colors. NO gold. NO red. NO orange. Just black + teal on cream.")


# ---------- Image Generation ----------

def _enforce_prompt_budget(prompt, max_chars=4500, mode="spread"):
    """Enforce prompt length limits to keep Gemini focused.

    Trims verbose sections (icon details, structural guides) while
    PRESERVING critical sections:
    - Hero character block (appended after budget enforcement)
    - Per-panel hero emotions (HERO IN THIS PANEL lines)
    - Style directives, layout grid, color rules
    - Drawing tool instructions

    Budget accounts for Islamic guardrails appended AFTER budget enforcement.

    Args:
        prompt: Full prompt string
        max_chars: Maximum character count (default 3500 for spread, 2200 for front)
        mode: 'spread', 'front', or 'back'

    Returns:
        Trimmed prompt string within budget
    """
    if mode == "front":
        max_chars = 2500
    elif mode == "back":
        max_chars = 2000

    if len(prompt) <= max_chars:
        return prompt

    # Strategy: trim EXPENDABLE sections first, preserve HERO CHARACTER and style
    # Priority: trim icon details > structural guide > back text verbosity
    # NEVER trim: hero character block, drawing tool, color rule, layout grid
    # NEVER trim illustration section when it contains per-panel hero emotions
    #   (HERO IN THIS PANEL lines must stay associated with their PANEL definitions)

    has_inline_hero_emotions = "HERO IN THIS PANEL:" in prompt

    trimming_targets = [
        ("SPECIFIC ICONS FOR EACH ELEMENT:", "STRUCTURAL DRAWING GUIDE:"),
        ("SPECIFIC ICONS FOR EACH ELEMENT:", "HERO CHARACTER"),
        ("STRUCTURAL DRAWING GUIDE:", "HERO CHARACTER"),
        ("ICON RULES:", "STRUCTURAL DRAWING GUIDE:"),
        ("MAIN ILLUSTRATION", "ICON QUALITY"),
    ]

    # Only trim illustration section if it does NOT contain inline hero emotions
    if not has_inline_hero_emotions:
        trimming_targets.append(("ILLUSTRATION:", "ICON ENFORCEMENT"))

    trimmed = prompt
    for start_marker, end_marker in trimming_targets:
        if len(trimmed) <= max_chars:
            break
        start_idx = trimmed.find(start_marker)
        end_idx = trimmed.find(end_marker)
        if start_idx > 0 and end_idx > start_idx:
            section = trimmed[start_idx:end_idx]
            if len(section) > 200:
                # Keep first 150 chars of this section
                truncated_section = section[:150] + "...\n\n"
                trimmed = trimmed[:start_idx] + truncated_section + trimmed[end_idx:]

    # If still over budget, trim FRONT CARD icon/structural sections more aggressively
    # NEVER trim the BACK CARD — it contains critical verse text and exact content
    if len(trimmed) > max_chars:
        # Trim icon enforcement section on front card
        icon_start = trimmed.find("ICON ENFORCEMENT:")
        back_start = trimmed.find("BACK CARD")
        if icon_start > 0 and back_start > icon_start:
            icon_section = trimmed[icon_start:back_start]
            if len(icon_section) > 100:
                trimmed = trimmed[:icon_start] + "\n\n" + trimmed[back_start:]

    # Final hard truncation — but try to keep hero block
    if len(trimmed) > max_chars:
        hero_idx = trimmed.find("HERO CHARACTER")
        if hero_idx > 0:
            # Keep everything up to hero block start, then hero block to end
            pre_hero = trimmed[:hero_idx]
            hero_onward = trimmed[hero_idx:]
            # Trim pre-hero section
            budget_for_pre = max_chars - len(hero_onward) - 50
            if budget_for_pre > 500:
                trimmed = pre_hero[:budget_for_pre] + "\n\n" + hero_onward
            else:
                trimmed = trimmed[:max_chars - 50] + "\n\n[Generate the card as described above.]"
        else:
            trimmed = trimmed[:max_chars - 50] + "\n\n[Generate the card as described above.]"

    return trimmed


def generate_card_spread(card_data):
    """Generate a complete front+back card spread image.

    Enhanced Phase 6:
    - Reads visual_type and model_type (with fallback)
    - Reads is_islamic_content and islamic_elements flags
    - Applies Islamic guardrails to prompts when needed
    """
    client = get_gemini_client()
    if not client:
        return {"error": "No Google API key configured. Set GOOGLE_AI_API_KEY environment variable."}

    # Use card_title/card_category (concise LLM-generated) if available, else sanitize raw input
    title = _sanitize_title(card_data)
    category = _sanitize_category(card_data)
    visual_type = card_data.get("visual_type")
    model_type = card_data.get("model_type", "sequential_chain")
    theme = card_data.get("theme", "warm_parchment")
    steps = card_data.get("steps", [])
    quote = card_data.get("quote", "")
    back_text = card_data.get("back_text", "")
    card_number = card_data.get("card_number") or 1
    arabic_terms = card_data.get("arabic_terms", [])
    is_islamic_content = card_data.get("is_islamic_content", False)
    islamic_elements = card_data.get("islamic_elements", [])
    surah_name = card_data.get("surah_name", "").strip()
    verse_number = card_data.get("verse_number", "").strip()

    # Build prompt components — use same palette for all content (matches original prompts)
    color_instruction = build_color_instruction(theme, is_islamic_content)
    illustration_description = build_illustration_description(
        visual_type=visual_type,
        model_type=model_type,
        steps=steps,
        title=title,
        arabic_terms=arabic_terms,
        step_emotions=card_data.get("step_emotions"),
    )

    # Extract bold terms from back text
    bold_terms = re.findall(r'\*\*(.*?)\*\*', back_text)
    bold_terms_str = ", ".join(f'"{t}"' for t in bold_terms) if bold_terms else "key concepts"

    # Build back text content — include actual text like original prompts
    back_text_clean = back_text.replace("**", "")
    if back_text_clean:
        back_text_content = ":\n" + _truncate_at_sentence(back_text_clean, 600)
    else:
        back_text_content = " about the concept"

    # Theme-specific template vars matching original prompts exactly
    if theme == "warm_parchment":
        bg_texture = "light-cream"
        card_bg = "Cream/parchment"
        accent_shape = "golden"
        category_placement = "top-right, smaller text with divider line"
    else:
        bg_texture = "light-grey"
        card_bg = "White"
        accent_shape = "teal"
        category_placement = "rotated vertically on the right edge with a divider line"

    # Build verse reference line for the top band (below title, small italic text)
    verse_ref_line = _build_verse_ref_line(surah_name, verse_number)

    # Build verse reference display for footer (e.g., "2:165")
    verse_ref_display = _build_verse_ref_display(surah_name, verse_number)

    # Build verse text block for back card
    verse_arabic = card_data.get("verse_arabic", "").strip()
    verse_english = card_data.get("verse_english", "").strip()
    verse_text_block = _build_verse_text_block(verse_arabic, verse_english)

    prompt = CARD_SPREAD_PROMPT_TEMPLATE.format(
        title=title.upper(),
        category=category.upper(),
        color_instruction=color_instruction,
        illustration_description=illustration_description,
        quote=quote,
        back_text_content=back_text_content,
        bold_terms=bold_terms_str,
        card_number=card_number,
        bg_texture=bg_texture,
        card_bg=card_bg,
        accent_shape=accent_shape,
        category_placement=category_placement,
        quote_extra=", slightly rotated" if theme == "cool_mint" else "",
        verse_ref_line=verse_ref_line,
        verse_ref_display=verse_ref_display,
        verse_text_block=verse_text_block,
    )

    prompt = _enforce_prompt_budget(prompt, mode="spread")

    # Inject hero character AFTER budget trimming (so it's never cut)
    if steps:
        prompt += _build_hero_block(visual_type or model_type or "sequential_chain", card_data)

    # Apply Islamic guardrails — use CONCISE version to avoid overwhelming the style
    prompt = apply_guardrails(prompt, is_islamic_content, islamic_elements, concise=True)

    return _call_gemini_image(client, prompt, f"spread_{card_data.get('id', 'new')}")


def generate_card_front(card_data):
    """Generate just the front card image.

    Enhanced Phase 6:
    - Reads visual_type with model_type fallback
    - Reads is_islamic_content and islamic_elements
    - Applies Islamic guardrails
    """
    client = get_gemini_client()
    if not client:
        return {"error": "No Google API key configured."}

    title = _sanitize_title(card_data)
    category = _sanitize_category(card_data)
    visual_type = card_data.get("visual_type")
    model_type = card_data.get("model_type", "sequential_chain")
    theme = card_data.get("theme", "warm_parchment")
    steps = card_data.get("steps", [])
    quote = card_data.get("quote", "")
    card_number = card_data.get("card_number") or 1
    is_islamic_content = card_data.get("is_islamic_content", False)
    islamic_elements = card_data.get("islamic_elements", [])

    surah_name = card_data.get("surah_name", "")
    verse_number = card_data.get("verse_number", "")
    verse_ref_line = _build_verse_ref_line(surah_name, verse_number)
    verse_ref_display = _build_verse_ref_display(surah_name, verse_number)

    color_instruction = build_color_instruction(theme, is_islamic_content)
    illustration_description = build_illustration_description(
        visual_type=visual_type,
        model_type=model_type,
        steps=steps,
        title=title,
        step_emotions=card_data.get("step_emotions"),
    )

    prompt = CARD_FRONT_PROMPT_TEMPLATE.format(
        title=title.upper(),
        category=category.upper(),
        color_instruction=color_instruction,
        illustration_description=illustration_description,
        quote=quote,
        card_number=card_number,
        verse_ref_line=verse_ref_line,
        verse_ref_display=verse_ref_display,
    )

    prompt = _enforce_prompt_budget(prompt, mode="front")

    # Inject hero character AFTER budget trimming (so it's never cut)
    if steps:
        prompt += _build_hero_block(visual_type or model_type or "sequential_chain", card_data)

    # Apply Islamic guardrails — concise to avoid overwhelming style
    prompt = apply_guardrails(prompt, is_islamic_content, islamic_elements, concise=True)

    return _call_gemini_image(client, prompt, f"front_{card_data.get('id', 'new')}")


def generate_card_back(card_data):
    """Generate just the back card image.

    Enhanced Phase 6:
    - Reads is_islamic_content and islamic_elements
    - Applies Islamic guardrails
    """
    client = get_gemini_client()
    if not client:
        return {"error": "No Google API key configured."}

    theme = card_data.get("theme", "warm_parchment")
    back_text = card_data.get("back_text", "")
    card_number = card_data.get("card_number") or 1
    is_islamic_content = card_data.get("is_islamic_content", False)
    islamic_elements = card_data.get("islamic_elements", [])
    surah_name = card_data.get("surah_name", "")
    verse_number = card_data.get("verse_number", "")
    verse_arabic = card_data.get("verse_arabic", "").strip()
    verse_english = card_data.get("verse_english", "").strip()

    color_instruction = build_color_instruction(theme, is_islamic_content)
    bold_terms = re.findall(r'\*\*(.*?)\*\*', back_text)
    bold_terms_str = ", ".join(f'"{t}"' for t in bold_terms) if bold_terms else "key concepts"

    verse_ref_display = _build_verse_ref_display(surah_name, verse_number)
    verse_text_block = _build_verse_text_block(verse_arabic, verse_english)

    prompt = CARD_BACK_PROMPT_TEMPLATE.format(
        color_instruction=color_instruction,
        bold_terms=bold_terms_str,
        back_text=back_text.replace("**", ""),
        card_number=card_number,
        verse_ref_display=verse_ref_display,
        verse_text_block=verse_text_block,
    )

    prompt = _enforce_prompt_budget(prompt, mode="back")

    # Apply Islamic guardrails — concise
    prompt = apply_guardrails(prompt, is_islamic_content, islamic_elements, concise=True)

    return _call_gemini_image(client, prompt, f"back_{card_data.get('id', 'new')}")


def _post_generation_quality_check(filepath):
    """Run basic quality checks on a generated image.

    Validates dimensions, file size, and aspect ratio to catch
    obvious generation failures before returning to user.

    Args:
        filepath: Path to the generated image file

    Returns:
        Dict with 'passed' bool and 'warnings' list
    """
    warnings = []
    try:
        img = Image.open(filepath)
        w, h = img.size

        # Check minimum dimensions
        if w < 200 or h < 200:
            warnings.append(f"Image too small: {w}x{h}px (minimum 200x200)")

        # Check for extremely distorted aspect ratios
        ratio = w / h if h > 0 else 0
        if ratio > 4.0 or ratio < 0.25:
            warnings.append(f"Extreme aspect ratio: {ratio:.2f} (expected 0.5-2.0)")

        # Check file size (too small = likely blank/failed)
        file_size = os.path.getsize(filepath)
        if file_size < 5000:  # Less than 5KB is suspicious
            warnings.append(f"File suspiciously small: {file_size} bytes")

        # Check for mostly single-color images (potential blank generation)
        if img.mode in ('RGB', 'RGBA'):
            # Sample center pixel vs corner pixels
            center = img.getpixel((w // 2, h // 2))
            corners = [
                img.getpixel((10, 10)),
                img.getpixel((w - 10, 10)),
                img.getpixel((10, h - 10)),
                img.getpixel((w - 10, h - 10)),
            ]
            # Check if all sampled pixels are very similar (mostly blank)
            if all(_pixel_similar(center, c, threshold=20) for c in corners):
                warnings.append("Image appears mostly uniform (possible blank generation)")

    except Exception as e:
        warnings.append(f"Quality check error: {str(e)}")

    return {
        "passed": len(warnings) == 0,
        "warnings": warnings,
    }


def _pixel_similar(p1, p2, threshold=20):
    """Check if two RGB/RGBA pixels are similar within threshold."""
    try:
        # Handle both RGB and RGBA
        r1, g1, b1 = p1[:3]
        r2, g2, b2 = p2[:3]
        return (abs(r1 - r2) < threshold and
                abs(g1 - g2) < threshold and
                abs(b1 - b2) < threshold)
    except (TypeError, IndexError):
        return False


def _call_gemini_image(client, prompt, file_prefix, reference_image_b64=None):
    """Call Gemini API to generate an image.

    Args:
        client: Gemini client
        prompt: Text prompt string
        file_prefix: Prefix for saved files
        reference_image_b64: Optional base64 image string (with or without data:image prefix)
                            to send as visual reference for image-to-image editing
    """
    # Log prompt for debugging (saved to file so we can review what Gemini received)
    try:
        log_dir = os.path.join(os.path.dirname(__file__), "static", "prompt_logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"{file_prefix}_{_timestamp()}.txt")
        with open(log_path, "w") as f:
            f.write(f"=== PROMPT FOR {file_prefix} ===\n")
            f.write(f"Length: {len(prompt)} chars\n")
            f.write(f"Has reference image: {reference_image_b64 is not None}\n\n")
            f.write(prompt)
        print(f"[image_gen] Prompt logged to {log_path} ({len(prompt)} chars, ref_img={reference_image_b64 is not None})")
    except Exception as e:
        print(f"[image_gen] Prompt log failed: {e}")

    try:
        from google.genai import types

        # Build contents — either text-only or multimodal (image + text) for refinement
        if reference_image_b64:
            # Strip data URI prefix if present
            raw_b64 = reference_image_b64
            if raw_b64.startswith("data:"):
                raw_b64 = raw_b64.split(",", 1)[1]

            img_bytes = base64.b64decode(raw_b64)

            # Multimodal: send reference image FIRST, then the text prompt
            contents = [
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                prompt
            ]
            print(f"[image_gen] Sending multimodal request (image + text) for refinement")
        else:
            contents = prompt

        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            )
        )

        # Extract image from response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                # Save image
                img_data = part.inline_data.data
                mime = part.inline_data.mime_type or "image/png"
                ext = "png" if "png" in mime else "jpg"

                filename = f"{file_prefix}_{_timestamp()}.{ext}"
                filepath = os.path.join(IMAGE_DIR, filename)

                # Decode and save
                img = Image.open(io.BytesIO(img_data))
                img.save(filepath, quality=95)

                # Run quality checks
                qc = _post_generation_quality_check(filepath)

                # Also create base64 for web display
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                b64 = base64.b64encode(buffered.getvalue()).decode()

                return {
                    "success": True,
                    "filename": filename,
                    "filepath": filepath,
                    "url": f"/static/images/{filename}",
                    "base64": f"data:image/png;base64,{b64}",
                    "width": img.width,
                    "height": img.height,
                    "quality_check": qc,
                    "quality_warnings": qc.get("warnings", []),
                }

        # If no image in response, check for text
        text_parts = [p.text for p in response.candidates[0].content.parts if p.text]
        return {"error": f"No image generated. Model response: {' '.join(text_parts)[:200]}"}

    except Exception as e:
        return {"error": f"Image generation failed: {str(e)}"}


def generate_prompt_only(card_data, mode="spread"):
    """Return the prompt without calling the API (for manual use).

    Enhanced Phase 6:
    - Supports visual_type with model_type fallback
    - Applies Islamic guardrails to returned prompt
    """
    title = _sanitize_title(card_data)
    category = _sanitize_category(card_data)
    visual_type = card_data.get("visual_type")
    model_type = card_data.get("model_type", "sequential_chain")
    theme = card_data.get("theme", "warm_parchment")
    steps = card_data.get("steps", [])
    quote = card_data.get("quote", "")
    back_text = card_data.get("back_text", "")
    card_number = card_data.get("card_number") or 1
    is_islamic_content = card_data.get("is_islamic_content", False)
    islamic_elements = card_data.get("islamic_elements", [])
    surah_name = card_data.get("surah_name", "")
    verse_number = card_data.get("verse_number", "")
    verse_arabic = card_data.get("verse_arabic", "").strip()
    verse_english = card_data.get("verse_english", "").strip()
    verse_ref_line = _build_verse_ref_line(surah_name, verse_number)
    verse_ref_display = _build_verse_ref_display(surah_name, verse_number)
    verse_text_block = _build_verse_text_block(verse_arabic, verse_english)

    color_instruction = build_color_instruction(theme, is_islamic_content)
    illustration_description = build_illustration_description(
        visual_type=visual_type,
        model_type=model_type,
        steps=steps,
        title=title,
        step_emotions=card_data.get("step_emotions"),
    )
    bold_terms = re.findall(r'\*\*(.*?)\*\*', back_text)
    bold_terms_str = ", ".join(bold_terms) if bold_terms else "key concepts"
    back_text_short = back_text[:300].replace("**", "")

    if mode == "spread":
        # Build back text content like original prompts
        back_text_clean = back_text.replace("**", "")
        back_text_content = (":\n" + _truncate_at_sentence(back_text_clean, 600)) if back_text_clean else " about the concept"

        # Theme-specific vars matching original prompts
        if theme == "warm_parchment":
            bg_texture, card_bg, accent_shape = "light-cream", "Cream/parchment", "golden"
            category_placement = "top-right, smaller text with divider line"
        else:
            bg_texture, card_bg, accent_shape = "light-grey", "White", "teal"
            category_placement = "rotated vertically on the right edge with a divider line"

        prompt = CARD_SPREAD_PROMPT_TEMPLATE.format(
            title=title.upper(), category=category.upper(),
            color_instruction=color_instruction,
            illustration_description=illustration_description,
            quote=quote, back_text_content=back_text_content,
            bold_terms=bold_terms_str, card_number=card_number,
            bg_texture=bg_texture, card_bg=card_bg,
            accent_shape=accent_shape, category_placement=category_placement,
            quote_extra=", slightly rotated" if theme == "cool_mint" else "",
            verse_ref_line=verse_ref_line,
            verse_ref_display=verse_ref_display,
            verse_text_block=verse_text_block,
        )
    elif mode == "front":
        prompt = CARD_FRONT_PROMPT_TEMPLATE.format(
            title=title, category=category,
            color_instruction=color_instruction,
            illustration_description=illustration_description,
            quote=quote, card_number=card_number,
            verse_ref_line=verse_ref_line,
            verse_ref_display=verse_ref_display,
        )
    else:
        prompt = CARD_BACK_PROMPT_TEMPLATE.format(
            color_instruction=color_instruction,
            bold_terms=bold_terms_str,
            back_text=back_text.replace("**", ""),
            card_number=card_number,
            verse_ref_display=verse_ref_display,
            verse_text_block=verse_text_block,
        )

    prompt = _enforce_prompt_budget(prompt, mode=mode)

    # Inject hero character AFTER budget trimming (so it's never cut)
    if steps and mode in ("spread", "front"):
        prompt += _build_hero_block(visual_type or model_type or "sequential_chain", card_data)

    # Apply Islamic guardrails — use CONCISE version to avoid overwhelming the style
    prompt = apply_guardrails(prompt, is_islamic_content, islamic_elements, concise=True)

    return prompt


def generate_from_custom_prompt(prompt):
    """Generate an image from a raw custom prompt — no prompt building or guardrails."""
    client = get_gemini_client()
    if not client:
        return {"error": "No Google API key configured. Set GOOGLE_AI_API_KEY environment variable."}
    return _call_gemini_image(client, prompt, "custom")


# ---------- Image Refinement System ----------

def build_refinement_prompt(original_prompt, refinement_instructions, has_reference_image=False):
    """Build a refinement prompt that preserves the original card baseline and ADDITIVELY
    applies human-specified tweaks.

    The key principle: the original image/prompt is the baseline. The refinement only
    changes what the human explicitly requests — everything else stays exactly the same.

    When has_reference_image=True, the prompt references the attached image directly,
    which gives Gemini a strong visual anchor to preserve the original.

    Args:
        original_prompt: The full prompt that generated the baseline image
        refinement_instructions: Human-written description of what to change
        has_reference_image: Whether the original image is being sent alongside this prompt

    Returns:
        The refined prompt string ready to send to Gemini
    """
    # When we have the reference image, use image-to-image editing style prompt
    if has_reference_image:
        refinement_prompt = (
            "EDIT THIS IMAGE. The attached image is a hand-drawn mental model card spread "
            "(front card + back card). Make ONLY the specific changes listed below. "
            "Keep EVERYTHING else EXACTLY as it is in the image — same layout, same style, "
            "same drawing technique, same colors, same text, same positions, same card structure.\n"
            "\n"
            "CHANGES TO MAKE (apply ONLY these — nothing else changes):\n"
            f"{refinement_instructions}\n"
            "\n"
            "PRESERVATION RULES (CRITICAL):\n"
            "- The BACK CARD (right side) text must be EXACTLY the same words — copy every "
            "sentence precisely, do not paraphrase or invent new text\n"
            "- The FRONT CARD title, panel labels, sub-text, and quote stay exactly the same "
            "unless the changes above explicitly modify them\n"
            "- Same hand-drawn Sakura Micron fineliner style — hatching, stipple, hand-wobble\n"
            "- Same 2-color palette (black ink + golden amber accent)\n"
            "- Same hero character design (young Muslim man, early 20s, thick wavy hair, hoodie "
            "with geometric patterns)\n"
            "- Same card dimensions, same tilt angles, same desk surface\n"
            "- Same Islamic border patterns, same corner flourishes\n"
            "- Same panel dividers, same icon positions, same zone proportions\n"
            "\n"
            "Think of this as a SURGICAL EDIT — change only what was requested, preserve everything else.\n"
            "\n"
            "OUTPUT: Single landscape image containing both cards as a refined spread."
        )
    else:
        # Fallback: text-only refinement (no reference image)
        refinement_prompt = (
            "TASK: Re-generate an existing card image with small targeted changes.\n"
            "\n"
            "STEP 1 — Read the ORIGINAL PROMPT below. This defines the baseline card.\n"
            "STEP 2 — Read the CHANGES section. Apply ONLY those specific changes.\n"
            "STEP 3 — Generate the card following the original prompt exactly, with the changes applied.\n"
            "\n"
            "CRITICAL — BACK CARD TEXT PRESERVATION:\n"
            "The back card text must be reproduced WORD-FOR-WORD from the original prompt. "
            "Do NOT paraphrase, summarize, or invent new text. Copy it exactly.\n"
            "\n"
            f"═══ ORIGINAL CARD PROMPT (baseline — follow this exactly) ═══\n"
            f"{original_prompt}\n"
            f"\n"
            f"═══ CHANGES (apply ONLY these on top of the baseline) ═══\n"
            f"{refinement_instructions}\n"
            f"\n"
            f"PRESERVATION CHECKLIST:\n"
            f"- Same layout, panels, dividers, zones\n"
            f"- Same hero character design throughout\n"
            f"- Same color palette (2 colors only)\n"
            f"- Same drawing style (Sakura Micron fineliner)\n"
            f"- Same text content word-for-word unless explicitly changed\n"
            f"- Same icons and positions unless explicitly changed\n"
            f"\n"
            f"OUTPUT: Single landscape image containing both cards as a refined spread."
        )

    return refinement_prompt


def refine_card_image(card_data, refinement_instructions, original_prompt=None, original_image_b64=None):
    """Generate a refined version of a card image based on human feedback.

    This is the main entry point for the human-in-the-loop refinement flow.
    When original_image_b64 is provided, uses image-to-image editing (much better
    at preserving the original) rather than text-only regeneration.

    Args:
        card_data: The card data dict (same as used for original generation)
        refinement_instructions: Human-written tweaks to apply
        original_prompt: The prompt used for the original image (if not provided, regenerates it)
        original_image_b64: Base64 of the current card image (for visual reference)

    Returns:
        Dict with image result (same format as generate_card_spread)
    """
    client = get_gemini_client()
    if not client:
        return {"error": "No Google API key configured. Set GOOGLE_AI_API_KEY environment variable."}

    # Get or rebuild the original prompt
    if not original_prompt:
        original_prompt = generate_prompt_only(card_data, mode="spread")

    # Build the refinement prompt — use image-anchored version when we have the image
    has_ref_image = bool(original_image_b64)
    refined_prompt = build_refinement_prompt(
        original_prompt, refinement_instructions, has_reference_image=has_ref_image
    )

    # Log the refinement prompt
    try:
        log_dir = os.path.join(os.path.dirname(__file__), "static", "prompt_logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"refine_{_timestamp()}.txt")
        with open(log_path, "w") as f:
            f.write(f"=== REFINEMENT PROMPT ===\n")
            f.write(f"Has reference image: {has_ref_image}\n")
            f.write(f"Original prompt length: {len(original_prompt)} chars\n")
            f.write(f"Refinement instructions: {refinement_instructions}\n")
            f.write(f"Total refined prompt length: {len(refined_prompt)} chars\n\n")
            f.write(refined_prompt)
        print(f"[refine] Prompt logged to {log_path} (ref_img={has_ref_image})")
    except Exception as e:
        print(f"[refine] Log failed: {e}")

    return _call_gemini_image(
        client, refined_prompt, f"refine_{card_data.get('id', 'new')}",
        reference_image_b64=original_image_b64 if has_ref_image else None
    )


def split_spread_into_cards(image_source):
    """Split a spread image (front+back side by side) into individual card images
    with transparent backgrounds. Uses only PIL (no numpy dependency).

    Args:
        image_source: One of:
            - Base64 string (with or without data: prefix)
            - File path string (e.g. "static/images/spread.jpg")

    Returns:
        Dict with front_b64, back_b64 (transparent PNG base64), and metadata
    """
    # Decode image — handle base64 data, file paths, and URL paths
    src = image_source

    if os.path.exists(src):
        # Direct file path
        img = Image.open(src).convert("RGBA")
    elif src.startswith("data:"):
        raw_b64 = src.split(",", 1)[1]
        img_bytes = base64.b64decode(raw_b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    elif src.startswith("/static/") or src.startswith("static/"):
        filepath = src.lstrip("/")
        img = Image.open(filepath).convert("RGBA")
    else:
        # Try as raw base64
        img_bytes = base64.b64decode(src)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    w, h = img.size

    # Split at midpoint
    mid_x = w // 2
    left_half = img.crop((0, 0, mid_x, h))
    right_half = img.crop((mid_x, 0, w, h))

    results = {}
    for label, half in [("front", left_half), ("back", right_half)]:
        card_img = _extract_card_from_half(half)
        buf = io.BytesIO()
        card_img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        results[f"{label}_b64"] = f"data:image/png;base64,{b64}"
        results[f"{label}_width"] = card_img.width
        results[f"{label}_height"] = card_img.height

    return results


def _extract_card_from_half(half_img):
    """Extract the card from a half of the spread by detecting its dark border frame.
    Pure PIL implementation — no numpy required.

    The card has an ornate dark Islamic border pattern. We detect the outermost
    border lines by scanning for columns/rows with high dark-pixel density,
    then crop slightly outside those borders to include the card's rounded edges.
    """
    rgba = half_img.convert("RGBA")
    gray = half_img.convert("L")
    w, h = gray.size

    if w < 10 or h < 10:
        return rgba

    gpx = list(gray.getdata())
    dark_thresh = 130  # pixels below this are "dark" (border ink)
    min_density = 0.12  # a border col/row has >12% dark pixels

    # ─── Step 1: Find outer border lines ───
    # Scan from each edge inward to find the FIRST column/row with
    # significant dark pixel density (the card's ornate border frame)

    # Left border: scan columns left → right
    border_left = 0
    for x in range(w // 2):
        dark_count = sum(1 for y in range(h) if gpx[y * w + x] < dark_thresh)
        if dark_count / h > min_density:
            border_left = x
            break

    # Right border: scan columns right → left
    border_right = w - 1
    for x in range(w - 1, w // 2, -1):
        dark_count = sum(1 for y in range(h) if gpx[y * w + x] < dark_thresh)
        if dark_count / h > min_density:
            border_right = x
            break

    # Top border: scan rows top → bottom
    border_top = 0
    for y in range(h // 2):
        dark_count = sum(1 for x in range(w) if gpx[y * w + x] < dark_thresh)
        if dark_count / w > min_density:
            border_top = y
            break

    # Bottom border: scan rows bottom → top
    border_bottom = h - 1
    for y in range(h - 1, h // 2, -1):
        dark_count = sum(1 for x in range(w) if gpx[y * w + x] < dark_thresh)
        if dark_count / w > min_density:
            border_bottom = y
            break

    # ─── Step 2: Expand slightly to include the border + rounded edge ───
    # The border itself should be included, plus a small margin for
    # the card's rounded corners and any soft edge outside the border
    margin = max(3, min(w, h) // 80)  # ~8-10px on typical images
    crop_left = max(0, border_left - margin)
    crop_top = max(0, border_top - margin)
    crop_right = min(w, border_right + margin + 1)
    crop_bottom = min(h, border_bottom + margin + 1)

    card = rgba.crop((crop_left, crop_top, crop_right, crop_bottom))

    # ─── Step 3: Sample the card's outer edge color and fill corners ───
    # The rounded corners may expose desk-color pixels. Replace them
    # with the card's actual edge color (the cream/parchment just outside the border).
    cw, ch = card.size
    card_px = list(card.getdata())

    # Sample the card's edge color from just inside the border on each side
    # (a few pixels inside from the middle of each edge)
    edge_samples = []
    mid_y, mid_x = ch // 2, cw // 2
    sample_range = range(2, min(15, min(cw, ch) // 4))

    for d in sample_range:
        for pos in [
            mid_y * cw + d,            # left edge, middle
            mid_y * cw + (cw - 1 - d), # right edge, middle
            d * cw + mid_x,            # top edge, middle
            (ch - 1 - d) * cw + mid_x, # bottom edge, middle
        ]:
            if 0 <= pos < len(card_px):
                px = card_px[pos]
                # Only sample non-dark pixels (we want the card color, not border ink)
                brightness = (px[0] + px[1] + px[2]) // 3
                if brightness > 150:
                    edge_samples.append(px[:3])

    if edge_samples:
        ne = len(edge_samples)
        fill_r = sorted(p[0] for p in edge_samples)[ne // 2]
        fill_g = sorted(p[1] for p in edge_samples)[ne // 2]
        fill_b = sorted(p[2] for p in edge_samples)[ne // 2]
        fill_color = (fill_r, fill_g, fill_b)

        # Replace corner pixels that look like desk background
        # (similar to desk color, which is different from card color)
        # Detect desk color from the original image corners
        orig_px = list(rgba.getdata())
        desk_samples = []
        cs = max(2, min(w, h) // 30)
        for cy in range(cs):
            for cx in range(cs):
                desk_samples.append(orig_px[cy * w + cx][:3])
        dn = len(desk_samples)
        desk_r = sorted(p[0] for p in desk_samples)[dn // 2]
        desk_g = sorted(p[1] for p in desk_samples)[dn // 2]
        desk_b = sorted(p[2] for p in desk_samples)[dn // 2]

        # Replace pixels matching desk color with card edge color
        # Only in the corner regions (outer 15% of card)
        corner_depth_x = max(5, cw // 7)
        corner_depth_y = max(5, ch // 7)
        desk_thresh_sq = 30 * 30

        final_pixels = list(card_px)
        for i, px in enumerate(card_px):
            x = i % cw
            y = i // cw
            # Only process corner regions
            in_corner = ((x < corner_depth_x or x >= cw - corner_depth_x) and
                         (y < corner_depth_y or y >= ch - corner_depth_y))
            if in_corner:
                r, g, b = px[0], px[1], px[2]
                dist_sq = (r - desk_r)**2 + (g - desk_g)**2 + (b - desk_b)**2
                if dist_sq < desk_thresh_sq:
                    final_pixels[i] = (fill_r, fill_g, fill_b, 255)

        card.putdata(final_pixels)

    # ─── Step 4: Apply rounded corners ───
    card = _apply_rounded_corners(card, radius=max(12, min(card.size) // 20))

    return card


def _apply_rounded_corners(img, radius=20):
    """Apply rounded corner mask to an image using PIL."""
    from PIL import ImageDraw

    w, h = img.size
    # Create a rounded rectangle mask
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=radius, fill=255)

    # Apply mask to alpha channel
    result = img.convert("RGBA")
    r, g, b, a = result.split()
    # Combine existing alpha with rounded mask
    from PIL import ImageChops
    a = ImageChops.multiply(a, mask.convert("L"))
    result.putalpha(a)
    return result


def _timestamp():
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")
