CONTENT EVALUATOR FOR QURAN VISUAL CARDS
=========================================

FILE: content_evaluator.py (25 KB)

PURPOSE
-------
Universal card quality, accuracy, and fidelity validator that runs BEFORE 
image generation to catch mismatches, inconsistencies, and design issues early.

THE PROBLEM IT SOLVES
---------------------
A card titled "The Four Loves" implies 4 items to visual learners, but the 
front only shows 2 comparison columns. The other 2 are in back text. This 
title-content mismatch violates visual learning principles.

The evaluator detects this systematically across 8 dimensions.

EVALUATION DIMENSIONS
---------------------
1. Title-Content Alignment  - Does title promise match actual content?
2. Step Count Fidelity      - Are counts consistent and well-defined?
3. Visual Type Fit          - Is visual type appropriate for content?
4. Front-Back Coherence     - Do front and back tell consistent story?
5. Quote Relevance          - Does quote support the message?
6. Content Completeness     - Is all source material represented?
7. Cognitive Load           - Is card overloaded or too sparse?
8. Icon Relevance           - Are icons meaningful for concepts?

CORE API
--------
evaluate_card(card_data: Dict) -> Dict
  - Run comprehensive evaluation
  - Returns: score (0-100), grade (A-F), issues, warnings, suggestions

quick_evaluate(card_data: Dict) -> str
  - Get human-readable summary

get_dimension_scores(card_data: Dict) -> Dict[str, int]
  - Get per-dimension scores

USAGE EXAMPLE
-------------
from content_evaluator import evaluate_card

card = {
    'card_title': 'The Four Loves',
    'visual_type': 'comparison',
    'steps': [
        {'label': 'Love Allah', 'description': '...'},
        {'label': 'Love What Allah Loves', 'description': '...'},
    ],
    'back_text': '...',
    'quote': '...',
}

result = evaluate_card(card)
if result['issues']:
    print("Fix these issues before generating images:")
    for issue in result['issues']:
        print(f"  - {issue}")

SCORING
-------
Letter Grades:
  A: 90-100
  B: 80-89
  C: 70-79
  D: 60-69
  F: 0-59

Calculation: Average of 8 dimension scores minus (8 × critical issues)

QUICK TEST
----------
python3 -c "
from content_evaluator import quick_evaluate

card = {
    'card_title': 'The Four Loves',
    'steps': [{'label': 'A'}, {'label': 'B'}],
    'back_text': 'About all four types...',
    'quote': 'A quote',
    'visual_type': 'comparison',
}

print(quick_evaluate(card))
"

KEY FEATURES
------------
✓ Number extraction from titles ("Four Types of X" → 4)
✓ Content pattern detection (process, hierarchy, spectrum, comparison, etc)
✓ Visual type constraint validation (e.g., pyramid_hierarchy needs 3+ steps)
✓ Cross-reference checking (front concepts mentioned in back text?)
✓ Cognitive load assessment (text density, step count)
✓ Islamic content flagging (calligraphy, geometric borders guardrails)
✓ Bold term scanning (back text emphasis)
✓ Missing field detection

TYPICAL ISSUES DETECTED
-----------------------
• "Title implies 4 items but only 2 found across front and back"
• "Visual type needs at least 3 steps but only 2 provided"
• "None of the front card step labels appear in back text"
• "Title has 8 words — may not fit in top band"
• "Content pattern 'process' detected but visual_type is 'comparison'"
• "Missing card fields: category, visual_type"

INTEGRATION POINTS
------------------
1. Pre-image generation validation
2. Batch quality control reports
3. CI/CD pipeline checks
4. Card creation wizard feedback
5. Quality dashboard metrics

SEE ALSO
--------
EVALUATOR_USAGE.md - Detailed usage guide with examples
