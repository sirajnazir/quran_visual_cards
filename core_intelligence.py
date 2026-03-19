"""Core Intelligence Module - LLM-powered analysis engine for Quran Visual Cards.

Enhanced with intelligent mental model matching, expanded visual types,
Islamic content detection, and ReAct multi-phase analysis pipeline.
"""
import json
import os
import re
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MODEL_TYPES, THEMES, VISUAL_TYPES
from intelligent_matching import (
    ModelRepository, get_top_matches, format_models_for_llm_context,
    extract_signals, score_models
)
from islamic_guardrails import detect_islamic_content

# Initialize the mental models repository (loaded once at module level)
_repo = ModelRepository()


def get_client():
    """Get Anthropic client."""
    try:
        from anthropic import Anthropic
        api_key = ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return None
        return Anthropic(api_key=api_key)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# PHASE 1: DEEP UNDERSTANDING PROMPT (no model candidates)
# ═══════════════════════════════════════════════════════════════

PHASE1_DEEP_UNDERSTANDING_PROMPT = """You are a deep content analyst. Your job is to deeply understand the essence of the following content BEFORE any model matching occurs.

INPUT:
- Title: {title}
- Category/Context: {category}
- Content: {analysis_text}

Analyze this content deeply. Think about:
1. What is the CORE message? Not keywords — the actual insight.
2. What cognitive/structural pattern does this content embody?
3. What visual would best convey this to someone seeing it for the first time?
4. Does this content contain MULTIPLE genuinely distinct high-value themes?
5. Does the SURFACE STRUCTURE conflict with the RHETORICAL INTENT?
   Example: "levels of love" = hierarchy structure BUT warning intent → visual should be comparison, NOT pyramid.
   Counter-example: "Maslow's hierarchy" = hierarchy structure AND ranking intent → pyramid IS correct.

MULTI-THEME RULES:
- Most content has ONE theme. Only split if themes are genuinely distinct (not sub-points).
- A secondary theme needs confidence >= 0.7 to be worth proposing.
- Maximum 3 themes. Never force a split.
- Examples of genuine splits: a verse about patience AND divine decree AND charity (3 distinct concepts).
- Examples of NOT splitting: a verse about worship through prayer, fasting, and charity (all sub-points of worship).

COMPETING FRAMINGS RULES:
- Sometimes the same content can be analyzed through genuinely different lenses.
- A "competing framing" is NOT a distinct theme — it is the same content viewed through a different analytical angle.
- Example: "Levels of love" → Framing A: "The Adherence Warning" (Quranic metaphor of love adhering like punishment) vs Framing B: "Sacred Love Spectrum" (categorizing love types)
- Only propose framings when 2 (max 3) significantly different angles exist with distinct key_tension, rhetorical_intent, and visual direction.
- Framings and multi-themes are mutually exclusive. If both apply, prefer framings.
- Do NOT force framings. Most content has one clear angle.

Return your analysis in this EXACT XML format (no markdown, no code blocks):

<analysis>
  <essence>1-2 sentence core message — what this content is REALLY about</essence>
  <cognitive_structure>The thinking pattern: dichotomy, progression, cycle, hierarchy, balance, network, threshold, comparison, or other</cognitive_structure>
  <visual_emphasis>What the eye should be drawn to: contrast, flow, hierarchy, symmetry, tension, convergence, or divergence</visual_emphasis>
  <visual_metaphor>Best real-world visual analogy for this content</visual_metaphor>
  <emotional_tone>The feeling the card should evoke</emotional_tone>
  <key_tension>The central conflict, paradox, or insight</key_tension>
  <rhetorical_intent>The author's PURPOSE: warn, contrast, inspire, rank, caution, explain, reveal-paradox, celebrate, lament, teach-sequence, compare, connect, or other</rhetorical_intent>
  <intent_visual_override>ONLY if rhetorical intent CONFLICTS with cognitive_structure, state the visual type the intent demands (e.g., "comparison" when structure is "hierarchy" but intent is "warn"). Empty if no conflict.</intent_visual_override>
  <suggested_visual_patterns>2-3 visual type names that fit (e.g., comparison, scale_balance, sequential_chain)</suggested_visual_patterns>

  <theme_count>1</theme_count>
  <themes>
    <theme priority="1">
      <title>Short punchy title for this theme</title>
      <focus>What this theme card should center on</focus>
      <essence>1-sentence essence of this specific theme</essence>
      <cognitive_structure>Structure type for this theme</cognitive_structure>
      <visual_emphasis>Visual focus for this theme</visual_emphasis>
      <rhetorical_intent>The author's PURPOSE for this theme</rhetorical_intent>
      <confidence>0.0-1.0</confidence>
    </theme>
  </themes>

  <competing_framings_count>0</competing_framings_count>
  <competing_framings>
    <framing priority="1">
      <title>Short punchy framing title</title>
      <essence>1-sentence essence of this angle</essence>
      <key_tension>The central conflict/paradox from THIS angle</key_tension>
      <rhetorical_intent>Purpose: warn, contrast, inspire, etc.</rhetorical_intent>
      <intent_visual_override>Visual type if intent conflicts with structure (empty if none)</intent_visual_override>
      <visual_direction>Brief description of what the card visual should emphasize</visual_direction>
      <confidence>0.0-1.0</confidence>
    </framing>
  </competing_framings>
</analysis>

If there are 2-3 genuinely distinct themes, set theme_count accordingly and add more <theme> elements.
If there are 2-3 competing framings (same content, different analytical angles), set competing_framings_count and add <framing> elements.
Return ONLY the XML. No other text."""


# ═══════════════════════════════════════════════════════════════
# PHASE 2: MODEL MATCH + SYNTHESIS PROMPT
# ═══════════════════════════════════════════════════════════════

PHASE2_SYNTHESIS_PROMPT = """You are the synthesis stage of a Quranic Mental Model engine.

Phase 1 already performed deep content analysis. Here is that analysis:

{phase1_xml}

{theme_focus_instruction}

Now, using this deep understanding, select the best mental model and produce card data.

INPUT:
- Title: {title}
- Category/Context: {category}
- Analysis Text: {analysis_text}

{models_context}

AVAILABLE VISUAL TYPES (choose the most fitting):
{visual_types_list}

IMPORTANT: Your model selection should be GUIDED by the Phase 1 analysis above.
The cognitive_structure and visual_emphasis from Phase 1 tell you what kind of model fits best.
Do NOT just pick the highest-scored candidate — pick the one that best matches the ESSENCE.
You MUST choose model_id from the candidates listed below. The only exception is model_id='custom' which should be used extremely rarely.

CRITICAL: If intent_visual_override is present, the surface structure is MISLEADING.
Use the intent_visual_override as your primary guide for visual type selection.
Pick the model that best matches RHETORICAL INTENT and ESSENCE, not surface structure.

YOUR TASK:

STEP 0 — MODEL MATCHING (STRICT SELECTION):
You MUST follow this priority order:
1. CONFIRM: If the top-ranked model fits the content essence, use it directly.
2. ADAPT: If a lower-ranked model fits better, choose it and explain the adaptation.
3. COMBINE: If two models together capture the content better, combine them (use one model_id, note the combination in matching_reasoning).
4. CUSTOM (LAST RESORT — <5% of cases): Only use model_id='custom' if EVERY listed model is fundamentally incompatible with the content. You must justify why each top model fails.
Return the model_id of your chosen match.

STEP 1 — VISUAL TYPE SELECTION:
Select the PRIMARY visual type that best represents this content's structure.
Choose from the available visual types list above.
Also suggest a secondary alternative visual type.

STEP 2 — EXTRACT KEY STEPS/CONCEPTS (2-4 elements):
For each step provide:
- label: Short English label (1-3 words)
- arabic: Arabic term if relevant (empty string if not)
- description: One-sentence description

STEP 3 — GENERATE QUOTE:
The quote MUST directly address the <key_tension> from Phase 1.
If key_tension identifies a paradox, crystallize that paradox.
If key_tension identifies a conflict, name both sides.
Do NOT generate a generic inspirational statement — make it SPECIFIC to the tension.
Core insight, 1-2 sentences max, pithy and memorable.

STEP 4 — SELECT THEME:
- "warm_parchment" for Quranic/Islamic themes
- "cool_mint" for general cognitive/psychological concepts

STEP 5 — DETECT ISLAMIC CONTENT:
Is this Quranic or Islamic content? If yes, list specific Islamic visual elements
that should be included (geometric patterns, mosque silhouettes, calligraphy, etc.)

STEP 6 — GENERATE BACK CARD TEXT (3 paragraphs):
- Paragraph 1: State the common fallacy or default thinking
- Paragraph 2: Explain how the mental model corrects this
- Paragraph 3: Synthesize the core takeaway
Use **bold** for key terms. Academic but accessible tone.

STEP 7 — CARD DISPLAY TITLE & CATEGORY:
Generate a concise card title (2-5 words, like "THE TAWAKKUL PARADOX" or "MASLOW'S HAMMER")
and a short category label (1-3 words, like "FAITH & ACTION" or "PROBLEM SOLVING").
These are for the card visual — they must be SHORT and punchy, NOT the full verse text.

STEP 8 — HERO CHARACTER EMOTIONS PER STEP (CRITICAL — determines visual accuracy):
The card features a recurring hero character who appears in each panel/segment.
For EACH step you defined in Step 2, specify the hero's FULL BODY POSTURE and facial expression
that PHYSICALLY EMBODIES that step's spiritual/theological meaning.

CRITICAL: Consider the THEOLOGICAL and MORAL valence of each step:
- Positive concepts (faith, sincerity, worship of Allah alone, virtue, mercy, paradise) →
  warm/happy/inspired/peaceful expressions
- Negative concepts (shirk/polytheism, sin, hypocrisy, corruption, punishment, hellfire) →
  sad/distressed/horrified/guilty expressions
- Cautionary/neutral concepts (materialism, worldly attachment, tests, struggle) →
  restless/uneasy/conflicted/concerned expressions

MANDATORY ISLAMIC SPIRITUAL STATE → PHYSICAL EXPRESSION MAP:
- "Humility"/"Khushu" → head BOWED LOW, eyes DOWN at ground, shoulders INWARD, body SMALL — NOT thinking
- "Worship"/"Ibadah"/"Na'budu" → body BOWED, eyes CLOSED, hands in dua — NOT smiling casually
- "Taqwa" → eyes WIDE and alert, jaw firm, forward lean of vigilance — NOT generic thinking
- "Tawakkul" → eyes closed, palms OPEN upward, shoulders relaxed — active peaceful surrender
- "Submission" → body bowed forward, head lowered, face showing PEACE — willing surrender
- "Recognition" → eyes WIDENING, hand to heart, body STIFFENING — earth-shaking truth realization
- "Elevation"/"Ascent" → eyes UPWARD, body rising, arms lifted — drawn toward the Divine
- "Sovereignty"/"Rabb" → eyes WIDE with awe, body pulled BACK, overwhelmed by divine majesty

IMPORTANT: A step's LABEL may sound positive but its MEANING may be negative.
For example "Love With Allah" sounds positive but means shirk (polytheism) — the hero
should look DISTRESSED, not happy. Always judge by the step's actual theological meaning,
not its surface-level wording.

ANTI-PATTERN: NEVER default to "thinking face", "slight smile", or "neutral gaze" for any Islamic concept. Each spiritual state has a SPECIFIC physical posture.

For each step, provide a vivid 15-30 word description of the hero's FULL BODY POSTURE, head angle,
hand placement, and facial details that an image generator can directly render.
BAD: "thinking expression" or "slight smile" (LAZY — never use these)
GOOD: "Head bowed low with chin toward chest, eyes fully closed in reverence, shoulders curved inward, hands clasped low in submission"

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "model_id": "matched_model_id_from_repository",
  "model_type": "legacy_type_if_applicable",
  "visual_type": "primary_visual_type",
  "visual_type_secondary": "alternative_visual_type",
  "matched_model_name": "Display Name of Matched Model",
  "model_confidence": 0.92,
  "card_title": "THE TAWAKKUL PARADOX",
  "card_category": "FAITH & ACTION",
  "theme": "warm_parchment",
  "is_islamic_content": true,
  "islamic_elements": ["geometric star patterns", "mosque silhouette", "arabesque border"],
  "steps": [
    {{"label": "Worship", "arabic": "اعْبُدُوا اللَّهَ", "description": "Recognize servitude to Allah"}},
    {{"label": "Taqwa", "arabic": "وَاتَّقُوهُ", "description": "Develop consciousness and caution"}},
    {{"label": "Obey", "arabic": "وَأَطِيعُونِ", "description": "Follow the delivered guidance"}}
  ],
  "step_emotions": [
    {{"label": "Worship", "emotion": "devoted reverence — eyes half-closed in peace, serene gentle smile, hands raised in prayer, humble posture"}},
    {{"label": "Taqwa", "emotion": "alert vigilance — wide watchful eyes, slight tension in jaw, cautious but confident stance, shield-like posture"}},
    {{"label": "Obey", "emotion": "determined submission — firm gentle eyes, calm composed mouth, nodding head, hand on heart in acceptance"}}
  ],
  "quote": "It is tempting to follow guidance without recognizing servitude.",
  "back_text": "Paragraph 1...\\n\\nParagraph 2...\\n\\nParagraph 3...",
  "icon_suggestions": ["praying silhouette", "light emanation", "scroll with calligraphy"],
  "matching_reasoning": "Brief explanation of why this model was chosen"
}}"""


# ═══════════════════════════════════════════════════════════════
# LEGACY SINGLE-SHOT ANALYSIS PROMPT (fallback)
# ═══════════════════════════════════════════════════════════════

ANALYSIS_PROMPT = """You are the Core Intelligence Module of a Quranic Mental Model Synthesis Engine.

You have access to a comprehensive repository of 100+ mental models across 15 categories.
Analyze the following input, match it to the best mental model, and produce structured card data.

INPUT:
- Title: {title}
- Category/Context: {category}
- Analysis Text: {analysis_text}

{models_context}

AVAILABLE VISUAL TYPES (choose the most fitting):
{visual_types_list}

You MUST choose model_id from the candidates listed below. The only exception is model_id='custom' which should be used extremely rarely.

YOUR TASK:

STEP 0 — MODEL MATCHING (STRICT SELECTION):
You MUST follow this priority order:
1. CONFIRM: If the top-ranked model fits the content essence, use it directly.
2. ADAPT: If a lower-ranked model fits better, choose it and explain the adaptation.
3. COMBINE: If two models together capture the content better, combine them (use one model_id, note the combination in matching_reasoning).
4. CUSTOM (LAST RESORT — <5% of cases): Only use model_id='custom' if EVERY listed model is fundamentally incompatible with the content. You must justify why each top model fails.
Return the model_id of your chosen match.

STEP 1 — VISUAL TYPE SELECTION:
Select the PRIMARY visual type that best represents this content's structure.
Choose from the available visual types list above.
Also suggest a secondary alternative visual type.

STEP 2 — EXTRACT KEY STEPS/CONCEPTS (2-4 elements):
For each step provide:
- label: Short English label (1-3 words)
- arabic: Arabic term if relevant (empty string if not)
- description: One-sentence description

STEP 3 — GENERATE QUOTE:
Core insight, 1-2 sentences max, pithy and memorable.

STEP 4 — SELECT THEME:
- "warm_parchment" for Quranic/Islamic themes
- "cool_mint" for general cognitive/psychological concepts

STEP 5 — DETECT ISLAMIC CONTENT:
Is this Quranic or Islamic content? If yes, list specific Islamic visual elements
that should be included (geometric patterns, mosque silhouettes, calligraphy, etc.)

STEP 6 — GENERATE BACK CARD TEXT (3 paragraphs):
- Paragraph 1: State the common fallacy or default thinking
- Paragraph 2: Explain how the mental model corrects this
- Paragraph 3: Synthesize the core takeaway
Use **bold** for key terms. Academic but accessible tone.

STEP 7 — CARD DISPLAY TITLE & CATEGORY:
Generate a concise card title (2-5 words, like "THE TAWAKKUL PARADOX" or "MASLOW'S HAMMER")
and a short category label (1-3 words, like "FAITH & ACTION" or "PROBLEM SOLVING").
These are for the card visual — they must be SHORT and punchy, NOT the full verse text.

STEP 8 — HERO EMOTIONS PER STEP (CRITICAL — deep nuanced emotional intelligence required):
For each step, provide a "step_emotions" array with the hero character's facial expression
and body language that PRECISELY matches that step's emotional/theological meaning.

RULES FOR EMOTION DERIVATION:
1. CONTEXT OVER KEYWORDS: "Love With Allah" about shirk = DISTRESSED, not loving. Read the MEANING, not the surface label.
2. GRADUATED INTENSITY: Match the intensity to the gravity — mild concern for minor warnings, deep anguish for hellfire/shirk.
3. BODY LANGUAGE + FACE: Include both facial features AND body posture/gesture in each emotion (e.g., "eyes wide with realization, hand on chest, stepping back" not just "surprised").
4. THEOLOGICAL NUANCE: Taqwa = alert vigilance (not fear), Tawakkul = serene surrender (not passivity), Sabr = dignified endurance (not suffering).
5. DYNAMIC VARIETY: NO two steps in the same card should have the same emotion. Even similar concepts need subtly different expressions.
6. SCENE CONTEXT: If the step describes a scenario (e.g., "person praying"), the emotion should match what someone IN that scenario would feel, not an observer.
7. MICRO-EXPRESSIONS: Include subtle details — "corner of mouth twitching", "one eyebrow slightly raised", "jaw tightening", "nostrils slightly flared", "eyes glistening" — these make expressions REAL.

CRITICAL — ISLAMIC SPIRITUAL STATE → PHYSICAL EXPRESSION MAP (memorize these):
- "Humility" / "Khushu" → head BOWED LOW, eyes cast DOWN at ground, shoulders rounded INWARD making body small, hands clasped low — NOT thinking, NOT looking forward
- "Worship" / "Ibadah" / "Na'budu" → head bowed, eyes CLOSED, hands raised in dua OR body in ruku-like bow, face showing deep submission — NOT smiling, NOT standing casually
- "Taqwa" → eyes WIDE and scanning alertly, jaw firm, body in forward lean of vigilance — the careful walk on a narrow path
- "Tawakkul" → eyes gently closed, face radiating calm, palms OPEN facing up, shoulders completely relaxed — active peaceful surrender
- "Sabr" → jaw SET with resolve, eyes steady and unwavering, chin slightly UP showing strength not defeat, fists gently clenched — nobility under pressure
- "Submission" / "Islam" → body bowed forward, head lowered, face showing PEACE not fear — willing surrender
- "Recognition" / "Realization" → eyes WIDENING with sudden deep understanding, mouth slightly open, hand rising to heart, body STIFFENING — earth-shaking truth
- "Sovereignty" / "Rabb" → eyes WIDE with awe, mouth agape, body pulled back by magnitude, one hand on chest, head tilted back — overwhelmed by divine majesty
- "Nasta'een" (seeking help) → hands raised HIGH in dua, eyes upward with vulnerable dependence, eyebrows drawn with need — no other source of aid
- "Elevation" / "Ascent" → eyes looking UPWARD, body rising, arms slightly lifted, face illuminated — drawn closer to the Divine
- "Shukr" / "Gratitude" → eyes glistening with tears, hands raised palms to sky, head tilted back — overflowing thanks
- "Dhikr" / "Remembrance" → eyes closed, lips moving in silent recitation, face serene, body swaying slightly — absorbed in Allah's remembrance

ANTI-PATTERN — NEVER DO THESE:
- "Humility" panel → thinking face (WRONG! Humility = bowed head + downcast eyes)
- "Worship" panel → smiling face (WRONG! Worship = deep reverence with bowed posture)
- "Recognition" panel → neutral gaze (WRONG! Recognition = widened eyes + hand on heart)
- Any Islamic devotional concept → generic "thoughtful" expression (WRONG! Each concept has SPECIFIC physical posture)
- Defaulting to "thinking" or "slight smile" for any panel (NEVER — these are LAZY defaults)

Each emotion should be 15-30 words describing SPECIFIC facial muscle movements, eye details, mouth shape, eyebrow position, body posture, and hand gestures.
BAD: "happy face" or "sad expression" or "thinking" or "slight smile" (too generic — NEVER use these)
GOOD: "Head bowed low with chin toward chest, eyes fully closed in reverence, shoulders curved inward in humility, hands clasped low in submission"

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "model_id": "matched_model_id_from_repository",
  "model_type": "legacy_type_if_applicable",
  "visual_type": "primary_visual_type",
  "visual_type_secondary": "alternative_visual_type",
  "matched_model_name": "Display Name of Matched Model",
  "model_confidence": 0.92,
  "card_title": "THE TAWAKKUL PARADOX",
  "card_category": "FAITH & ACTION",
  "theme": "warm_parchment",
  "is_islamic_content": true,
  "islamic_elements": ["geometric star patterns", "mosque silhouette", "arabesque border"],
  "steps": [
    {{"label": "Worship", "arabic": "اعْبُدُوا اللَّهَ", "description": "Recognize servitude to Allah"}},
    {{"label": "Taqwa", "arabic": "وَاتَّقُوهُ", "description": "Develop consciousness and caution"}},
    {{"label": "Obey", "arabic": "وَأَطِيعُونِ", "description": "Follow the delivered guidance"}}
  ],
  "step_emotions": [
    {{"label": "Worship", "emotion": "devoted reverence — eyes half-closed, serene gentle smile, hands raised in prayer"}},
    {{"label": "Taqwa", "emotion": "alert vigilance — wide watchful eyes, cautious but confident stance"}},
    {{"label": "Obey", "emotion": "determined submission — firm gentle eyes, nodding head, hand on heart"}}
  ],
  "quote": "It is tempting to follow guidance without recognizing servitude.",
  "back_text": "Paragraph 1...\\n\\nParagraph 2...\\n\\nParagraph 3...",
  "icon_suggestions": ["praying silhouette", "light emanation", "scroll with calligraphy"],
  "matching_reasoning": "Brief explanation of why this model was chosen"
}}"""


def _build_visual_types_list():
    """Build a formatted list of available visual types for the prompt."""
    lines = []
    for vt_id, vt_info in VISUAL_TYPES.items():
        lines.append(f"  - {vt_id}: {vt_info['description']}")
    return "\n".join(lines)


def _parse_phase1_xml(xml_text):
    """Parse Phase 1 XML response into a dict."""
    result = {}

    # Extract simple fields
    simple_fields = [
        "essence", "cognitive_structure", "visual_emphasis",
        "visual_metaphor", "emotional_tone", "key_tension",
        "rhetorical_intent", "intent_visual_override",
        "suggested_visual_patterns", "theme_count",
        "competing_framings_count"
    ]
    for field in simple_fields:
        match = re.search(rf"<{field}>(.*?)</{field}>", xml_text, re.DOTALL)
        result[field] = match.group(1).strip() if match else ""

    # Parse theme_count as int
    try:
        result["theme_count"] = int(result.get("theme_count", "1"))
    except (ValueError, TypeError):
        result["theme_count"] = 1

    # Parse competing_framings_count as int
    try:
        result["competing_framings_count"] = int(result.get("competing_framings_count", "0"))
    except (ValueError, TypeError):
        result["competing_framings_count"] = 0

    # Parse suggested_visual_patterns as list
    patterns_str = result.get("suggested_visual_patterns", "")
    result["suggested_visual_patterns"] = [
        p.strip() for p in re.split(r"[,;]", patterns_str) if p.strip()
    ]

    # Parse themes
    themes = []
    theme_matches = re.findall(
        r'<theme\s+priority="(\d+)">(.*?)</theme>',
        xml_text, re.DOTALL
    )
    for priority, theme_xml in theme_matches:
        theme = {"priority": int(priority)}
        for field in ["title", "focus", "essence", "cognitive_structure",
                      "visual_emphasis", "rhetorical_intent", "confidence"]:
            m = re.search(rf"<{field}>(.*?)</{field}>", theme_xml, re.DOTALL)
            theme[field] = m.group(1).strip() if m else ""
        # Parse confidence as float
        try:
            theme["confidence"] = float(theme.get("confidence", "0.5"))
        except (ValueError, TypeError):
            theme["confidence"] = 0.5
        themes.append(theme)

    result["themes"] = themes

    # Parse competing framings
    framings = []
    framing_matches = re.findall(
        r'<framing\s+priority="(\d+)">(.*?)</framing>',
        xml_text, re.DOTALL
    )
    for priority, framing_xml in framing_matches:
        framing = {"priority": int(priority)}
        for field in ["title", "essence", "key_tension", "rhetorical_intent",
                      "intent_visual_override", "visual_direction", "confidence"]:
            m = re.search(rf"<{field}>(.*?)</{field}>", framing_xml, re.DOTALL)
            framing[field] = m.group(1).strip() if m else ""
        try:
            framing["confidence"] = float(framing.get("confidence", "0.5"))
        except (ValueError, TypeError):
            framing["confidence"] = 0.5
        framings.append(framing)
    result["competing_framings"] = framings

    return result


def _call_phase1(client, title, category, analysis_text):
    """Phase 1: Deep content understanding with extended thinking. No model candidates."""
    prompt = PHASE1_DEEP_UNDERSTANDING_PROMPT.format(
        title=title,
        category=category,
        analysis_text=analysis_text,
    )

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=16000,
            thinking={
                "type": "enabled",
                "budget_tokens": 5000,
            },
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract text from response (may have thinking blocks)
        xml_text = ""
        for block in response.content:
            if block.type == "text":
                xml_text = block.text.strip()
                break

        if not xml_text:
            print("[Phase1] No text in response")
            return None

        # Clean potential markdown wrapping
        if xml_text.startswith("```"):
            xml_text = xml_text.split("\n", 1)[1]
            if xml_text.endswith("```"):
                xml_text = xml_text.rsplit("```", 1)[0]
            xml_text = xml_text.strip()

        result = _parse_phase1_xml(xml_text)
        result["raw_xml"] = xml_text
        print(f"[Phase1] Essence: {result.get('essence', 'N/A')[:80]}...")
        print(f"[Phase1] Structure: {result.get('cognitive_structure', 'N/A')}")
        print(f"[Phase1] Themes: {result.get('theme_count', 1)}")
        return result

    except Exception as e:
        print(f"[Phase1] Error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# RE-RANKING: Boost pre-scored models using Phase 1 insights
# ═══════════════════════════════════════════════════════════════

# Mapping from cognitive structures to visual types that match
_STRUCTURE_VISUAL_MAP = {
    "dichotomy": ["comparison", "scale_balance", "matrix_2x2"],
    "contrast": ["comparison", "scale_balance", "matrix_2x2"],
    "binary": ["comparison", "scale_balance", "matrix_2x2"],
    "comparison": ["comparison", "scale_balance", "matrix_2x2"],
    "progression": ["sequential_chain", "timeline", "funnel"],
    "sequence": ["sequential_chain", "timeline", "funnel"],
    "journey": ["sequential_chain", "timeline"],
    "cycle": ["cycle_loop", "flow_chart"],
    "spiral": ["cycle_loop", "flow_chart"],
    "feedback": ["cycle_loop", "flow_chart"],
    "hierarchy": ["pyramid_hierarchy", "nested_circles", "iceberg"],
    "layers": ["pyramid_hierarchy", "nested_circles", "iceberg"],
    "levels": ["pyramid_hierarchy", "nested_circles", "iceberg"],
    "balance": ["scale_balance", "tripod", "force_diagram"],
    "equilibrium": ["scale_balance", "tripod", "force_diagram"],
    "tension": ["scale_balance", "force_diagram", "comparison"],
    "network": ["network_graph", "venn_diagram"],
    "interconnection": ["network_graph", "venn_diagram"],
    "web": ["network_graph", "venn_diagram"],
    "threshold": ["s_curve", "exponential_curve"],
    "tipping": ["s_curve", "exponential_curve"],
    "transformation": ["s_curve", "exponential_curve", "comparison"],
}

# Mapping from rhetorical intent → natural visual types
_INTENT_VISUAL_MAP = {
    "warn": ["comparison", "funnel", "spectrum", "scale_balance"],
    "caution": ["funnel", "comparison", "spectrum", "s_curve"],
    "contrast": ["comparison", "scale_balance", "matrix_2x2", "spectrum"],
    "rank": ["pyramid_hierarchy", "nested_circles", "funnel"],
    "aspire": ["pyramid_hierarchy", "sequential_chain", "s_curve"],
    "inspire": ["s_curve", "exponential_curve", "sequential_chain"],
    "explain": ["sequential_chain", "flow_chart", "fishbone"],
    "teach-sequence": ["sequential_chain", "timeline", "flow_chart"],
    "reveal-paradox": ["comparison", "scale_balance", "force_diagram"],
    "compare": ["comparison", "scale_balance", "matrix_2x2", "venn_diagram"],
    "reveal-hidden": ["iceberg", "nested_circles", "pyramid_hierarchy"],
    "connect": ["network_graph", "venn_diagram", "cycle_loop"],
    "celebrate": ["tripod", "venn_diagram", "nested_circles"],
    "lament": ["funnel", "comparison", "spectrum"],
    "balance": ["scale_balance", "tripod", "spectrum"],
}


def _rerank_with_phase1(top_matches, phase1_result):
    """Re-rank pre-scored models using Phase 1 cognitive insights.

    4-stage logic:
    1. Detect conflict between surface structure and rhetorical intent
    2. Build visual sets from structure map + intent map
    3. Choose weights based on conflict presence
    4. Score each model with primary boost, penalty, patterns, emphasis, tension
    """
    if not phase1_result or not top_matches:
        return top_matches

    structure = phase1_result.get("cognitive_structure", "").lower()
    visual_emphasis = phase1_result.get("visual_emphasis", "").lower()
    suggested_patterns = [p.lower() for p in phase1_result.get("suggested_visual_patterns", [])]
    rhetorical_intent = phase1_result.get("rhetorical_intent", "").lower().strip()
    intent_override = phase1_result.get("intent_visual_override", "").lower().strip()
    key_tension = phase1_result.get("key_tension", "").lower()

    # ─── Stage 1: Detect conflict ───
    has_conflict = bool(intent_override)

    # ─── Stage 2: Build visual sets ───
    # Structure-based visuals (existing behavior)
    structure_visuals = set()
    for keyword, visuals in _STRUCTURE_VISUAL_MAP.items():
        if keyword in structure:
            structure_visuals.update(visuals)

    # Intent-based visuals (new)
    intent_visuals = set()
    for intent_kw, visuals in _INTENT_VISUAL_MAP.items():
        if intent_kw in rhetorical_intent:
            intent_visuals.update(visuals)

    # If override specifies a specific visual type, include it
    if intent_override:
        intent_visuals.add(intent_override)

    # ─── Stage 3: Choose weights based on conflict ───
    if has_conflict:
        # Intent overrides structure: intent visuals boosted, structure-only penalized
        primary_visuals = intent_visuals
        primary_boost = 0.20
        structure_only = structure_visuals - intent_visuals
        structure_penalty = -0.10
    else:
        # No conflict: both contribute equally (unified set)
        primary_visuals = structure_visuals | intent_visuals
        primary_boost = 0.15
        structure_only = set()
        structure_penalty = 0.0

    # ─── Stage 4: Score each model ───
    reranked = []
    for match in top_matches:
        adjusted_score = match["confidence"]
        model_visual = match.get("visual_type", "").lower()
        model_desc = match.get("description", "").lower()

        # Primary boost: model visual matches intent (or unified set)
        if model_visual in primary_visuals:
            adjusted_score += primary_boost

        # Penalty: model visual matches ONLY structure (conflict case)
        if model_visual in structure_only:
            adjusted_score += structure_penalty

        # Boost if model's visual type is in Phase 1's suggested patterns
        if model_visual in suggested_patterns:
            adjusted_score += 0.10

        # Boost if visual emphasis keywords match model visual type
        emphasis_visual_map = {
            "contrast": ["comparison", "scale_balance"],
            "flow": ["sequential_chain", "flow_chart", "timeline"],
            "hierarchy": ["pyramid_hierarchy", "nested_circles"],
            "symmetry": ["scale_balance", "venn_diagram", "tripod"],
            "tension": ["force_diagram", "scale_balance", "comparison"],
            "convergence": ["funnel", "venn_diagram", "nested_circles"],
            "divergence": ["decision_tree", "network_graph"],
        }
        for emphasis_kw, emphasis_visuals in emphasis_visual_map.items():
            if emphasis_kw in visual_emphasis and model_visual in emphasis_visuals:
                adjusted_score += 0.05

        # Key tension overlap: boost models whose descriptions share tension vocabulary
        if key_tension and model_desc:
            tension_words = set(key_tension.split()) - {"the", "a", "an", "is", "of", "and", "or", "but", "in", "to", "for", "with", "not"}
            desc_words = set(model_desc.split())
            overlap = tension_words & desc_words
            if len(overlap) >= 2:
                adjusted_score += 0.05

        new_match = dict(match)
        new_match["confidence"] = min(max(adjusted_score, 0.0), 1.0)
        new_match["phase1_boosted"] = adjusted_score != match["confidence"]
        if has_conflict:
            new_match["intent_conflict_detected"] = True
        reranked.append(new_match)

    # Re-sort by adjusted score
    reranked.sort(key=lambda m: m["confidence"], reverse=True)
    return reranked


def _call_phase2(client, title, category, analysis_text, phase1_xml,
                 models_context, visual_types_list, theme_focus_instruction=""):
    """Phase 2: Model match + synthesis, informed by Phase 1."""
    prompt = PHASE2_SYNTHESIS_PROMPT.format(
        title=title,
        category=category,
        analysis_text=analysis_text,
        phase1_xml=phase1_xml,
        models_context=models_context,
        visual_types_list=visual_types_list,
        theme_focus_instruction=theme_focus_instruction,
    )

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()

        # Clean potential markdown wrapping
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()

        result = json.loads(text)
        return result

    except Exception as e:
        print(f"[Phase2] Error: {e}")
        return None


def _ensure_backward_compat(result):
    """Ensure model_type and visual_type are present for backward compatibility."""
    if not result:
        return result

    if "model_type" not in result and "visual_type" in result:
        vt = result["visual_type"]
        legacy_map = {
            "sequential_chain": "sequential_chain",
            "tripod": "tripod",
            "cycle_loop": "loop_cycle",
            "comparison": "fail_constraint",
            "venn_diagram": "mutual_gain",
            "force_diagram": "strategic_interlock",
        }
        result["model_type"] = legacy_map.get(vt, "sequential_chain")

    if "visual_type" not in result and "model_type" in result:
        from config import LEGACY_MODEL_TYPES
        result["visual_type"] = LEGACY_MODEL_TYPES.get(result["model_type"], "sequential_chain")

    return result


# ═══════════════════════════════════════════════════════════════
# REACT PIPELINE: 2-call orchestrator
# ═══════════════════════════════════════════════════════════════

def analyze_with_react_pipeline(title, category, analysis_text):
    """ReAct pipeline: Phase 1 (deep understanding) → Phase 2 (model match + synthesis).

    Returns:
      - If single theme: standard card data dict (backward compatible)
      - If multi-theme: {"multi_theme": True, "themes": [...], "phase1_raw": "..."}
    """
    client = get_client()
    if not client:
        return analyze_fallback(title, category, analysis_text)

    # ─── Phase 1: Deep understanding (extended thinking, no models) ───
    print("[Pipeline] Starting Phase 1: Deep Understanding...")
    phase1_result = _call_phase1(client, title, category, analysis_text)

    if not phase1_result:
        print("[Pipeline] Phase 1 failed, falling back to single-shot")
        return _analyze_single_shot(client, title, category, analysis_text)

    # ─── Check for multi-theme ───
    theme_count = phase1_result.get("theme_count", 1)
    themes = phase1_result.get("themes", [])

    # Filter themes by confidence threshold
    qualifying_themes = [t for t in themes if t.get("confidence", 0) >= 0.7]

    if theme_count > 1 and len(qualifying_themes) > 1:
        print(f"[Pipeline] Multi-theme detected: {len(qualifying_themes)} themes")
        return {
            "multi_theme": True,
            "themes": qualifying_themes,
            "phase1_raw": phase1_result.get("raw_xml", ""),
            "phase1_essence": phase1_result.get("essence", ""),
        }

    # ─── Check for competing framings ───
    framings_count = phase1_result.get("competing_framings_count", 0)
    framings = phase1_result.get("competing_framings", [])
    qualifying_framings = [f for f in framings if f.get("confidence", 0) >= 0.7]

    if framings_count >= 2 and len(qualifying_framings) >= 2:
        print(f"[Pipeline] Competing framings detected: {len(qualifying_framings)} framings")
        return {
            "competing_framings": True,
            "framings": qualifying_framings,
            "phase1_raw": phase1_result.get("raw_xml", ""),
            "phase1_essence": phase1_result.get("essence", ""),
        }

    # ─── Single theme: continue to Phase 2 ───
    # Use the first theme's data if available
    active_theme = qualifying_themes[0] if qualifying_themes else None

    # Pre-score models (BETWEEN calls — no premature anchoring)
    print("[Pipeline] Pre-scoring models...")
    top_matches, signals = get_top_matches(title, category, analysis_text, _repo, n=5,
                                           expand_related=True)

    # Re-rank using Phase 1 insights
    reranked = _rerank_with_phase1(top_matches, phase1_result)
    models_context = format_models_for_llm_context(reranked)
    visual_types_list = _build_visual_types_list()

    # Phase 2: Model match + synthesis
    print("[Pipeline] Starting Phase 2: Model Match + Synthesis...")
    phase1_xml = phase1_result.get("raw_xml", "")
    result = _call_phase2(client, title, category, analysis_text,
                          phase1_xml, models_context, visual_types_list)

    if not result:
        print("[Pipeline] Phase 2 failed, falling back to single-shot")
        return _analyze_single_shot(client, title, category, analysis_text)

    # Add Phase 1 metadata
    result["phase1_essence"] = phase1_result.get("essence", "")
    result["phase1_structure"] = phase1_result.get("cognitive_structure", "")
    result["phase1_intent"] = phase1_result.get("rhetorical_intent", "")
    result["phase1_intent_override"] = phase1_result.get("intent_visual_override", "")
    result["phase1_key_tension"] = phase1_result.get("key_tension", "")
    result["pipeline"] = "react_v2"

    _ensure_backward_compat(result)
    return result


def analyze_single_theme(title, category, analysis_text, theme_data, phase1_raw):
    """Analyze a single theme from a multi-theme split.

    Reuses Phase 1 thinking — no extra extended thinking call.
    Called by /api/analyze-theme for each user-approved theme.
    """
    client = get_client()
    if not client:
        return analyze_fallback(title, category, analysis_text)

    # Build focused Phase 1 result from theme_data
    theme_phase1 = {
        "cognitive_structure": theme_data.get("cognitive_structure", ""),
        "visual_emphasis": theme_data.get("visual_emphasis", ""),
        "rhetorical_intent": theme_data.get("rhetorical_intent", ""),
        "suggested_visual_patterns": [],
    }

    # Pre-score models using theme-specific focus
    theme_query = f"{theme_data.get('title', '')} {theme_data.get('focus', '')}"
    top_matches, signals = get_top_matches(
        theme_query, category, theme_data.get("essence", analysis_text), _repo, n=5
    )

    # Re-rank with theme's cognitive insights
    reranked = _rerank_with_phase1(top_matches, theme_phase1)
    models_context = format_models_for_llm_context(reranked)
    visual_types_list = _build_visual_types_list()

    # Theme focus instruction for Phase 2
    theme_focus = (
        f"THEME FOCUS: This card should specifically focus on the theme: "
        f"\"{theme_data.get('title', '')}\"\n"
        f"Theme essence: {theme_data.get('essence', '')}\n"
        f"Theme focus: {theme_data.get('focus', '')}\n"
        f"Center the card data (steps, quote, back text) on THIS specific theme, "
        f"not the overall content."
    )

    result = _call_phase2(client, title, category, analysis_text,
                          phase1_raw, models_context, visual_types_list,
                          theme_focus_instruction=theme_focus)

    if not result:
        return analyze_fallback(title, category, analysis_text)

    result["theme_title"] = theme_data.get("title", "")
    result["pipeline"] = "react_v1_theme"
    _ensure_backward_compat(result)
    return result


def analyze_single_framing(title, category, analysis_text, framing_data, phase1_raw):
    """Analyze content through a user-chosen framing/angle.
    Locks Phase 2 to the chosen framing's key_tension and rhetorical_intent."""
    client = get_client()
    if not client:
        return analyze_fallback(title, category, analysis_text)

    framing_phase1 = {
        "cognitive_structure": "",
        "visual_emphasis": "",
        "rhetorical_intent": framing_data.get("rhetorical_intent", ""),
        "intent_visual_override": framing_data.get("intent_visual_override", ""),
        "key_tension": framing_data.get("key_tension", ""),
        "suggested_visual_patterns": [],
    }

    framing_query = f"{framing_data.get('title', '')} {framing_data.get('essence', '')}"
    top_matches, signals = get_top_matches(framing_query, category, analysis_text, _repo, n=5)
    reranked = _rerank_with_phase1(top_matches, framing_phase1)
    models_context = format_models_for_llm_context(reranked)
    visual_types_list = _build_visual_types_list()

    framing_focus = (
        f"FRAMING LOCK-IN: The user chose this analytical angle:\n"
        f"Framing: \"{framing_data.get('title', '')}\"\n"
        f"Essence: {framing_data.get('essence', '')}\n"
        f"Key tension (USE THIS): {framing_data.get('key_tension', '')}\n"
        f"Rhetorical intent: {framing_data.get('rhetorical_intent', '')}\n"
        f"Visual direction: {framing_data.get('visual_direction', '')}\n"
        f"\nCRITICAL: Lock onto this framing. Do NOT drift to a different angle."
    )

    # Override Phase 1 XML with chosen framing's fields
    modified_phase1 = phase1_raw
    if framing_data.get("key_tension"):
        modified_phase1 = re.sub(
            r"<key_tension>.*?</key_tension>",
            f"<key_tension>{framing_data['key_tension']}</key_tension>",
            modified_phase1, flags=re.DOTALL)
    if framing_data.get("rhetorical_intent"):
        modified_phase1 = re.sub(
            r"<rhetorical_intent>.*?</rhetorical_intent>",
            f"<rhetorical_intent>{framing_data['rhetorical_intent']}</rhetorical_intent>",
            modified_phase1, count=1, flags=re.DOTALL)
    if framing_data.get("intent_visual_override"):
        modified_phase1 = re.sub(
            r"<intent_visual_override>.*?</intent_visual_override>",
            f"<intent_visual_override>{framing_data['intent_visual_override']}</intent_visual_override>",
            modified_phase1, flags=re.DOTALL)

    result = _call_phase2(client, title, category, analysis_text,
                          modified_phase1, models_context, visual_types_list,
                          theme_focus_instruction=framing_focus)
    if not result:
        return analyze_fallback(title, category, analysis_text)

    result["framing_title"] = framing_data.get("title", "")
    result["framing_key_tension"] = framing_data.get("key_tension", "")
    result["pipeline"] = "react_v2_framing"
    _ensure_backward_compat(result)
    return result


def _analyze_single_shot(client, title, category, analysis_text):
    """Legacy single-shot analysis (renamed from original analyze_with_llm body)."""
    top_matches, signals = get_top_matches(title, category, analysis_text, _repo, n=5)
    models_context = format_models_for_llm_context(top_matches)
    visual_types_list = _build_visual_types_list()

    prompt = ANALYSIS_PROMPT.format(
        title=title,
        category=category,
        analysis_text=analysis_text,
        models_context=models_context,
        visual_types_list=visual_types_list,
    )

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()

        result = json.loads(text)
        result["pipeline"] = "single_shot"
        _ensure_backward_compat(result)
        return result

    except Exception as e:
        print(f"[SingleShot] Error: {e}")
        return None


def analyze_with_llm(title, category, analysis_text):
    """Use Claude to analyze text and produce card data.

    Uses ReAct pipeline as primary path, with single-shot and
    rule-based fallbacks.

    Fallback chain:
      analyze_with_react_pipeline()
        → _analyze_single_shot()
          → analyze_fallback()
    """
    # Primary: ReAct 2-call pipeline
    try:
        result = analyze_with_react_pipeline(title, category, analysis_text)
        if result:
            return result
    except Exception as e:
        print(f"[Pipeline] Exception: {e}")

    # Fallback 1: Single-shot
    client = get_client()
    if client:
        try:
            result = _analyze_single_shot(client, title, category, analysis_text)
            if result:
                return result
        except Exception as e:
            print(f"[SingleShot] Exception: {e}")

    # Fallback 2: Rule-based
    return analyze_fallback(title, category, analysis_text)


def analyze_fallback(title, category, analysis_text):
    """Enhanced rule-based fallback using mental models repository.

    Scores against the full repo instead of just 6 hardcoded types.
    """
    # Try intelligent matching first
    if _repo.is_loaded:
        top_matches, signals = get_top_matches(title, category, analysis_text, _repo, n=3)
        if top_matches and top_matches[0]["confidence"] > 0.1:
            best = top_matches[0]
            model_id = best["id"]
            visual_type = best["visual_type"]
            matched_name = best["name"]
            confidence = best["confidence"]
        else:
            model_id = "custom"
            visual_type = "sequential_chain"
            matched_name = "Custom Analysis"
            confidence = 0.0
    else:
        model_id = "custom"
        visual_type = "sequential_chain"
        matched_name = "Custom Analysis"
        confidence = 0.0

    text_lower = analysis_text.lower()

    # Legacy pattern detection (kept for backward compatibility)
    if any(w in text_lower for w in ["then", "leads to", "step", "first", "second", "third", "chain", "sequence"]):
        model_type = "sequential_chain"
    elif any(w in text_lower for w in ["three pillars", "tripod", "balance", "foundation", "pillar"]):
        model_type = "tripod"
    elif any(w in text_lower for w in ["cycle", "loop", "repeat", "circular", "feedback"]):
        model_type = "loop_cycle"
    elif any(w in text_lower for w in ["fail", "hammer", "wrong tool", "misappl", "constraint", "mistake"]):
        model_type = "fail_constraint"
    elif any(w in text_lower for w in ["lock", "key", "fit", "interlock", "precise"]):
        model_type = "strategic_interlock"
    elif any(w in text_lower for w in ["win-win", "mutual", "venn", "overlap", "both", "zero sum"]):
        model_type = "mutual_gain"
    else:
        model_type = "sequential_chain"

    # Islamic content detection
    is_islamic, islamic_elements = detect_islamic_content(title, category, analysis_text)
    theme = "warm_parchment" if is_islamic else "cool_mint"

    # Extract simple steps from text
    sentences = [s.strip() for s in analysis_text.split(".") if len(s.strip()) > 10]
    steps = []
    for i, sent in enumerate(sentences[:4]):
        words = sent.split()
        label = " ".join(words[:3]) if len(words) >= 3 else sent[:20]
        steps.append({
            "label": label,
            "arabic": "",
            "description": sent[:100]
        })

    if not steps:
        steps = [{"label": "Core Concept", "arabic": "", "description": analysis_text[:100]}]

    quote = sentences[0] if sentences else title

    back_text = (
        f"The default understanding often simplifies the relationship between these concepts. "
        f"We tend to see them as separate or optional.\n\n"
        f"However, **{title}** reveals a deeper structure. {analysis_text[:200]}\n\n"
        f"The key takeaway is that these elements form an interconnected system, "
        f"not isolated components. Understanding their relationship transforms our approach."
    )

    return {
        "model_id": model_id,
        "model_type": model_type,
        "visual_type": visual_type,
        "visual_type_secondary": None,
        "matched_model_name": matched_name,
        "model_confidence": confidence,
        "theme": theme,
        "is_islamic_content": is_islamic,
        "islamic_elements": islamic_elements,
        "steps": steps,
        "quote": quote[:150],
        "back_text": back_text,
        "icon_suggestions": ["concept", "arrow", "framework"],
    }


def generate_back_text_with_llm(title, category, model_type, steps, analysis_text):
    """Generate refined back card text using LLM."""
    client = get_client()
    if not client:
        return None

    steps_desc = "\n".join([f"- {s['label']}: {s['description']}" for s in steps])
    prompt = f"""Write the back-card text for a mental model card about "{title}" (Category: {category}).

Mental model type: {model_type}
Key concepts:
{steps_desc}

Original analysis: {analysis_text[:500]}

Write exactly 3 paragraphs:
1. State the common fallacy or default way of thinking (start with a hook)
2. Explain how this mental model corrects the thinking
3. Synthesize the core takeaway with an actionable insight

Use **bold** for 2-3 key philosophical terms. Keep it concise (150 words max total).
Academic but accessible tone. Return ONLY the text, no JSON wrapping."""

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception:
        return None


def get_model_repository():
    """Expose the model repository for use by other modules."""
    return _repo
