"""Hero Character System for Quran Visual Cards

Defines a consistent hero character — a young adult Muslim — who appears
across all cards as the central figure experiencing the mental model.

This creates visual continuity across the entire card deck, like a
recurring character in a graphic novel or educational series.

IMPORTANT GUARDRAIL NOTE:
- The hero character IS a regular human — faces ARE allowed and encouraged
- Prophets (peace be upon them) = noor/light silhouette, NO facial features
- Allah = Arabic calligraphy ONLY, never depicted as a figure
- The hero is NOT a prophet — he is the "everyman" learner/reader
"""

from typing import Dict, Optional


# ═══════════════════════════════════════════════════════════════
# HERO CHARACTER PRESETS
# ═══════════════════════════════════════════════════════════════

HERO_PRESETS = {
    "traditional": {
        "name": "Traditional Muslim Youth",
        "description": "Young adult Muslim man with traditional Islamic attire — timeless, scholarly look",
        "character_prompt": (
            "A young adult Muslim man (early 20s) with a short neat beard, "
            "wearing a white/cream kufi (prayer cap) and a clean thobe/jubbah robe. "
            "Warm brown skin, kind expressive eyes, gentle smile. "
            "Build: average, approachable, relatable. "
            "Drawn in sketchnote style with consistent 1.5pt ink outlines."
        ),
        "face_details": (
            "Simple but expressive face: two dot-eyes with eyebrow arcs, "
            "small nose line, gentle curved smile line. "
            "Short beard rendered as light stipple/hatching on jawline. "
            "NOT photorealistic — simplified cartoon/sketchnote features."
        ),
        "clothing": {
            "headwear": "white/cream kufi (prayer cap) with subtle geometric stitching pattern",
            "top": "ankle-length thobe/jubbah in white or cream, with simple collar",
            "accessories": "optional: prayer beads (misbaha) around wrist, small Quran in hand",
            "footwear": "simple sandals or bare feet",
        },
        "islamic_design_elements": [
            "Geometric star pattern embroidered on kufi cap edge",
            "Subtle arabesque trim along thobe collar and cuffs",
            "Prayer beads with crescent moon charm",
        ],
        "poses": {
            "thinking": "hand on chin, head slightly tilted, thoughtful expression",
            "learning": "sitting cross-legged with open Quran or book, leaning forward attentively",
            "realizing": "wide eyes, one hand raised palm-up in 'aha' moment",
            "struggling": "shoulders slightly hunched, hand on forehead, concerned look",
            "praying": "hands raised in dua (palms facing up toward sky, elbows at sides) — Islamic supplication, NOT namaste",
            "walking": "walking forward with purpose, slight lean into stride",
            "presenting": "one hand open-palm gesturing toward diagram/concept, other hand at side",
            "reflecting": "sitting cross-legged, one hand on chest over heart, eyes gently closed in tafakkur",
            "comparing": "hands out to both sides palm-up as if weighing options, looking between them",
            "celebrating": "right hand raised with index finger pointing up (tawhid gesture), grateful expression",
            "reading": "holding open Quran with both hands, head slightly bowed",
            "listening": "standing attentively, head tilted, one hand near ear",
        },
    },

    "urban": {
        "name": "Urban Muslim Youth",
        "description": "Young adult Muslim with trendy urban hoodie featuring golden Islamic geometric patterns — sharp 3D cartoon style adapted to ink sketch",
        "character_prompt": (
            "HERO 'ADAM' — SAME character on EVERY card.\n"
            "FACE: Young man early 20s, oval face, pointed chin, sharp jawline. "
            "Hair: jet-black solid ink, parted LEFT swept RIGHT, thick wavy tousled. "
            "Eyes: large almond, dark brown, thick upper lashes, white sparkle dot per eye. "
            "Eyebrows: thick arched, LEFT brow HIGHER than right (signature asymmetry). "
            "Nose: small straight angular line. "
            "Beard: short neat stipple dots on jawline+chin+upper lip, jawline visible through.\n"
            "HOODIE: Dark charcoal gray. CHEST: one LARGE golden (#C8902E) 8-pointed Islamic star (~5cm). "
            "SHOULDERS: small golden arabesque scrolls. Hood DOWN, drawstrings visible, kangaroo pocket.\n"
            "PANTS: dark indigo slim jeans tapered. SHOES: white canvas sneakers, golden laces.\n"
            "SKIN: PURE WHITE paper + BLACK INK outlines only — manga/Tintin style. "
            "NO beige, NO tan, NO skin color. Hair = solid black fill. "
            "Consistent 1.5pt ink outlines."
        ),
        "face_details": (
            "ADAM'S FIXED FACE — identical every card:\n"
            "Hair: jet-black, parted LEFT, swept RIGHT, wavy tousled strands\n"
            "Face: oval, pointed chin, defined cheekbones, sharp jawline\n"
            "Eyes: large almond, dark brown, thick lashes, white sparkle highlights\n"
            "Eyebrows: thick arched, LEFT higher than RIGHT (signature)\n"
            "Nose: small straight angular line\n"
            "Beard: short stipple dots on jawline+chin+lip, jawline visible\n"
            "Skin: WHITE paper + BLACK ink only. NO color fills.\n"
            "Expression changes per card, but face structure NEVER changes."
        ),
        "clothing": {
            "headwear": "no headwear — thick dark wavy hair swept to one side is the signature look",
            "top": "hoodie covered in Islamic geometric patterns (8-point stars, arabesque tessellations, floral motifs) — drawn using the card's accent color for pattern fills, black ink for outlines",
            "accessories": "optional: backpack (only when contextually relevant, NOT on every card), hoodie drawstrings visible",
            "footwear": "casual sneakers or contextually appropriate",
        },
        "islamic_design_elements": [
            "8-point star tessellation covering the hoodie fabric",
            "Arabesque floral vine motifs interlocking between geometric stars on hoodie",
            "Islamic interlocking tessellation as the hoodie's signature design",
            "Accent color wash on pattern fills, black ink for all outlines",
            "Subtle crescent moon detail on hoodie zipper pull (when visible)",
        ],
        "poses": {
            "thinking": "hand on chin, head slightly tilted, thoughtful expression — standing or leaning casually",
            "learning": "sitting cross-legged on floor with open Quran or book, leaning forward attentively",
            "realizing": "stepping back slightly, one hand raised palm-up in 'aha' moment, wide eyes",
            "struggling": "hands in hoodie pockets, shoulders slightly hunched, looking down in contemplation",
            "praying": "hands raised in dua (palms facing up toward sky, elbows at sides) — the Islamic supplication pose, NOT a namaste/prayer-hands pose",
            "walking": "confident stride forward, one hand holding a book, looking ahead with purpose",
            "presenting": "one hand open-palm gesturing toward diagram/concept, other hand relaxed at side",
            "reflecting": "sitting quietly, one hand on chest over heart, eyes slightly downcast in tafakkur (contemplation)",
            "comparing": "standing with weight shifted to one side, head turning between two options, hands open at sides",
            "celebrating": "right hand raised with index finger pointing up (tawhid gesture), subtle smile",
            "reading": "holding open Quran or book with both hands, head bowed slightly in concentration",
            "listening": "standing attentively, head tilted slightly, one hand cupped behind ear",
            # --- Islamic spiritual poses ---
            "worshipping": "body bowed forward in reverence, head lowered with eyes closed, hands raised near face in dua or placed on knees in ruku — deep spiritual submission, face showing profound awe",
            "humble": "head bowed LOW with chin nearly touching chest, eyes cast downward at ground, shoulders rounded inward making body appear small, hands clasped low — total self-effacement",
            "submitting": "body bent forward at waist, head lowered, eyes directed downward, arms relaxed hanging or hands on knees — willing peaceful surrender, face showing calm acceptance",
            "supplicating": "hands raised HIGH with palms open toward sky, eyes looking upward with vulnerable dependence, body slightly leaning forward — earnest desperate plea to Allah",
            "awed": "eyes wide with wonder, body pulled slightly backward by magnitude of what is witnessed, one hand on chest, head tilted back to look up — overwhelmed by divine majesty",
            "remembering": "eyes closed in meditative focus, lips slightly moving in silent dhikr, face serene, body swaying very gently — completely absorbed in Allah's remembrance",
            "ascending": "eyes looking upward with hope, body positioned rising or climbing, arms slightly lifted, face radiating growing light — spiritual elevation toward the Divine",
            "surrendering": "palms open facing upward at sides, eyes gently closed, face radiating calm acceptance, shoulders completely relaxed and dropped — releasing control to Allah",
            "vigilant": "eyes wide and alert scanning surroundings, jaw firm, body in slight forward lean of alertness, one hand near heart — conscious awareness of Allah's presence, walking carefully",
            "enduring": "jaw set firmly with quiet resolve, eyes steady and unwavering, chin slightly up with strength, shoulders bearing weight but standing tall — dignified patience under trial",
        },
    },
}

# Default hero preset — urban is the primary character across all cards
DEFAULT_HERO = "urban"


# ═══════════════════════════════════════════════════════════════
# HERO CHARACTER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_hero_preset(style: str = None) -> Dict:
    """Get a hero character preset by style name.

    Args:
        style: 'traditional' or 'urban'. Defaults to DEFAULT_HERO.

    Returns:
        Full hero preset dict with character prompt, clothing, poses, etc.
    """
    return HERO_PRESETS.get(style or DEFAULT_HERO, HERO_PRESETS[DEFAULT_HERO])


def get_hero_prompt(style: str = None, pose: str = "presenting") -> str:
    """Get a complete character description prompt for image generation.

    Combines the character base, face details, and a specific pose
    into a single prompt-ready string.

    Args:
        style: 'traditional' or 'urban'
        pose: One of the defined poses (thinking, learning, realizing, etc.)

    Returns:
        String ready for injection into image generation prompts
    """
    preset = get_hero_preset(style)

    # Base character
    char_desc = preset["character_prompt"]

    # Face
    face_desc = preset["face_details"]

    # Pose
    poses = preset["poses"]
    pose_desc = poses.get(pose, poses.get("presenting", "standing naturally"))

    # Clothing highlights
    clothing = preset["clothing"]
    clothing_desc = (
        f"Wearing: {clothing['top']}. "
        f"Head: {clothing['headwear']}. "
    )
    if clothing.get("accessories"):
        clothing_desc += f"Accessories: {clothing['accessories']}. "

    return (
        f"HERO CHARACTER (same person on every card): {char_desc}\n"
        f"FACE: {face_desc}\n"
        f"CLOTHING: {clothing_desc}\n"
        f"POSE: {pose_desc}"
    )


def get_hero_clothing_instruction(style: str = None) -> str:
    """Get just the clothing/accessory description for the hero.

    Useful when the hero is already described but you need
    to specify what they're wearing in a new scene.

    Args:
        style: 'traditional' or 'urban'

    Returns:
        Clothing description string
    """
    preset = get_hero_preset(style)
    clothing = preset["clothing"]

    parts = []
    for item_type, desc in clothing.items():
        parts.append(f"{item_type}: {desc}")

    islamic_elements = preset.get("islamic_design_elements", [])
    if islamic_elements:
        parts.append("Islamic design details: " + "; ".join(islamic_elements[:3]))

    return "\n".join(parts)


def get_hero_pose(style: str = None, pose: str = "presenting") -> str:
    """Get a specific pose description.

    Args:
        style: 'traditional' or 'urban'
        pose: Pose name

    Returns:
        Pose description string
    """
    preset = get_hero_preset(style)
    return preset["poses"].get(pose, "standing naturally, one hand gesturing")


def suggest_pose_for_visual_type(visual_type: str) -> str:
    """Suggest the best hero pose for a given visual type.

    Maps visual types to poses that make narrative sense —
    the hero interacts with the diagram/concept appropriately.

    Args:
        visual_type: One of the 20 visual types

    Returns:
        Suggested pose name
    """
    pose_map = {
        "sequential_chain": "presenting",
        "cycle_loop": "reflecting",
        "tripod": "presenting",
        "pyramid_hierarchy": "ascending",
        "scale_balance": "comparing",
        "iceberg": "realizing",
        "venn_diagram": "comparing",
        "comparison": "comparing",
        "force_diagram": "struggling",
        "funnel": "presenting",
        "decision_tree": "thinking",
        "matrix_2x2": "comparing",
        "fishbone": "thinking",
        "network_graph": "presenting",
        "timeline": "walking",
        "s_curve": "learning",
        "exponential_curve": "realizing",
        "flow_chart": "presenting",
        "spectrum": "comparing",
        "nested_circles": "reflecting",
    }
    return pose_map.get(visual_type, "presenting")


def build_hero_injection(card_data: Dict, hero_style: str = None) -> str:
    """Build a complete hero character prompt injection for a card.

    Analyzes the card's visual type and content to choose the best
    pose, then builds a full character description.

    Args:
        card_data: Card data dict with visual_type, steps, etc.
        hero_style: 'traditional' or 'urban'. Uses DEFAULT_HERO if None.

    Returns:
        Complete hero character prompt block ready for injection
    """
    style = hero_style or card_data.get("hero_style", DEFAULT_HERO)
    visual_type = card_data.get("visual_type", "sequential_chain")

    # Auto-select pose based on visual type
    pose = suggest_pose_for_visual_type(visual_type)

    # Allow card_data to override pose
    if card_data.get("hero_pose"):
        pose = card_data["hero_pose"]

    hero_prompt = get_hero_prompt(style, pose)

    return (
        f"\nHERO CHARACTER (appears in the illustration):\n"
        f"{hero_prompt}\n"
        f"The hero character should be INTERACTING with the diagram/concept — "
        f"not just standing next to it. Place the hero naturally within the illustration "
        f"as if they are experiencing or demonstrating the mental model.\n"
    )


def list_hero_styles() -> list:
    """List available hero style names."""
    return list(HERO_PRESETS.keys())


def list_poses(style: str = None) -> list:
    """List available poses for a hero style."""
    preset = get_hero_preset(style)
    return list(preset["poses"].keys())


def get_hero_summary(style: str = None) -> Dict:
    """Get a summary of a hero preset for API responses."""
    preset = get_hero_preset(style or DEFAULT_HERO)
    return {
        "name": preset["name"],
        "description": preset["description"],
        "poses": list(preset["poses"].keys()),
        "islamic_design_elements": preset.get("islamic_design_elements", []),
        "clothing_items": list(preset["clothing"].keys()),
    }
