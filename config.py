"""Configuration for Quran Visual Cards Pipeline"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# Flask
SECRET_KEY = os.environ.get("SECRET_KEY", "quran-cards-dev-key")
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 5001))

# Anthropic — set via environment variable or .env file (NEVER hardcode keys)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Google AI (Gemini) — set via environment variable or .env file (NEVER hardcode keys)
GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY", "")
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# Card Defaults
CARD_WIDTH = 400
CARD_HEIGHT = 560
EXPORT_DPI = 300
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "static", "exports")

# Data
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CARDS_DB = os.path.join(DATA_DIR, "cards.json")
MENTAL_MODELS_DB = os.path.join(DATA_DIR, "mental_models.json")

# Islamic Guardrails
ISLAMIC_GUARDRAILS_ENABLED = True

# Themes
THEMES = {
    "cool_mint": {
        "name": "Cool Mint",
        "bg_gradient": ["#C5E8D8", "#E8F5EE"],
        "accent": "#4A9B7F",
        "text": "#2C3E50",
        "title": "#1A2530",
        "back_bg": "#F0F0F0",
        "back_text": "#333333",
        "category_color": "#4A9B7F",
        "quote_color": "#2C3E50",
        "number_bg": "#B8DFD0",
    },
    "warm_parchment": {
        "name": "Warm Parchment",
        "bg_gradient": ["#F5E6C8", "#FDF3E0"],
        "accent": "#C8902E",
        "text": "#5C3D1A",
        "title": "#4A2E0A",
        "back_bg": "#FDF3E0",
        "back_text": "#4A2E0A",
        "category_color": "#C8902E",
        "quote_color": "#5C3D1A",
        "number_bg": "#E8D5B0",
    },
}

# Legacy model types (backward compatibility) — maps old 6 types to visual_types
LEGACY_MODEL_TYPES = {
    "sequential_chain": "sequential_chain",
    "tripod": "tripod",
    "loop_cycle": "cycle_loop",
    "fail_constraint": "comparison",
    "strategic_interlock": "force_diagram",
    "mutual_gain": "venn_diagram",
}

# Mental Model Types — expanded from 6 to cover all visual types
MODEL_TYPES = {
    # Original 6 (preserved for backward compatibility)
    "sequential_chain": {
        "name": "Sequential Chain",
        "description": "Imperatives linked logically in a specific order (A → B → C)",
        "default_theme": "warm_parchment",
        "icon_type": "chain",
        "visual_type": "sequential_chain",
    },
    "tripod": {
        "name": "Tripod / Balance",
        "description": "Three necessary, co-equal pillars or legs",
        "default_theme": "warm_parchment",
        "icon_type": "tripod",
        "visual_type": "tripod",
    },
    "loop_cycle": {
        "name": "Loop / Cycle",
        "description": "Processes that feed back into themselves",
        "default_theme": "warm_parchment",
        "icon_type": "cycle",
        "visual_type": "cycle_loop",
    },
    "fail_constraint": {
        "name": "Fail / Constraint Metaphor",
        "description": "Actions that look similar but fail due to mismatch",
        "default_theme": "cool_mint",
        "icon_type": "fail",
        "visual_type": "comparison",
    },
    "strategic_interlock": {
        "name": "Strategic Interlock",
        "description": "Concepts requiring precise fitting (Lock & Key)",
        "default_theme": "cool_mint",
        "icon_type": "interlock",
        "visual_type": "force_diagram",
    },
    "mutual_gain": {
        "name": "Mutual Gain / Venn",
        "description": "Overlapping interests or win-win scenarios",
        "default_theme": "cool_mint",
        "icon_type": "venn",
        "visual_type": "venn_diagram",
    },
}

# Visual Types — full catalog of 20 visualization approaches
VISUAL_TYPES = {
    "venn_diagram": {
        "name": "Venn Diagram",
        "description": "Overlapping circles showing intersections and shared areas",
        "icon_hint": "overlapping circles",
    },
    "cycle_loop": {
        "name": "Cycle / Loop",
        "description": "Circular flow showing self-reinforcing or repeating pattern",
        "icon_hint": "circular arrows",
    },
    "sequential_chain": {
        "name": "Sequential Chain",
        "description": "Linear progression A→B→C with dependencies",
        "icon_hint": "linked chain arrows",
    },
    "decision_tree": {
        "name": "Decision Tree",
        "description": "Branching yes/no decision paths",
        "icon_hint": "branching tree",
    },
    "matrix_2x2": {
        "name": "2×2 Matrix",
        "description": "Four quadrants formed by two axes",
        "icon_hint": "four-quadrant grid",
    },
    "pyramid_hierarchy": {
        "name": "Pyramid / Hierarchy",
        "description": "Stacked triangular levels from broad base to narrow peak",
        "icon_hint": "pyramid layers",
    },
    "iceberg": {
        "name": "Iceberg",
        "description": "Visible tip above waterline, hidden mass below",
        "icon_hint": "iceberg cross-section",
    },
    "fishbone": {
        "name": "Fishbone / Ishikawa",
        "description": "Central spine with branching cause categories",
        "icon_hint": "fish skeleton",
    },
    "funnel": {
        "name": "Funnel",
        "description": "Wide top narrowing progressively to bottom",
        "icon_hint": "narrowing funnel",
    },
    "scale_balance": {
        "name": "Scale / Balance",
        "description": "Two-pan balance scale showing weight comparison",
        "icon_hint": "balance scale",
    },
    "network_graph": {
        "name": "Network Graph",
        "description": "Nodes connected by multiple relationship lines",
        "icon_hint": "connected nodes",
    },
    "timeline": {
        "name": "Timeline",
        "description": "Horizontal chronological progression with milestones",
        "icon_hint": "horizontal timeline",
    },
    "s_curve": {
        "name": "S-Curve",
        "description": "S-shaped adoption or growth curve with threshold",
        "icon_hint": "S-shaped curve",
    },
    "exponential_curve": {
        "name": "Exponential Curve",
        "description": "Hockey-stick exponential growth pattern",
        "icon_hint": "exponential curve",
    },
    "comparison": {
        "name": "Side-by-Side Comparison",
        "description": "Two panels contrasting right vs wrong or before vs after",
        "icon_hint": "split panel",
    },
    "tripod": {
        "name": "Tripod / Three Pillars",
        "description": "Three equal pillars supporting a unified platform",
        "icon_hint": "three columns",
    },
    "flow_chart": {
        "name": "Flow Chart",
        "description": "Multi-path process flow with decision diamonds",
        "icon_hint": "flow diagram",
    },
    "force_diagram": {
        "name": "Force Diagram",
        "description": "Arrows pushing/pulling on a central element",
        "icon_hint": "opposing arrows",
    },
    "spectrum": {
        "name": "Spectrum / Continuum",
        "description": "Gradient bar from one extreme to another",
        "icon_hint": "gradient bar",
    },
    "nested_circles": {
        "name": "Nested Circles",
        "description": "Concentric circles showing containment and layers",
        "icon_hint": "concentric circles",
    },
}
