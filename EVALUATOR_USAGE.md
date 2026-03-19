# Content Evaluator - Usage Guide

## Overview

The `content_evaluator.py` module is a universal quality validator for Quran Visual Cards. It detects title-content mismatches, inconsistencies, and design issues before image generation.

## Problem It Solves

The core issue: A card titled "The Four Loves" promises 4 items to a visual learner, but the front only shows 2 comparison columns. The remaining 2 items are buried in back text. This mismatch violates visual learning principles.

The evaluator systematically detects this class of issue across 8 dimensions:

1. Title-Content Alignment - Does the title promise match actual content?
2. Step Count Fidelity - Are step counts consistent and well-defined?
3. Visual Type Fit - Is the visual type appropriate for the content?
4. Front-Back Coherence - Do front and back tell a consistent story?
5. Quote Relevance - Does the quote support the message?
6. Content Completeness - Is all source material represented?
7. Cognitive Load - Is the card overloaded or too sparse?
8. Icon Relevance - Are icons meaningful for concepts?

## Main API Functions

### evaluate_card(card_data: Dict) -> Dict

Run comprehensive evaluation on a card.

Returns:
- score (0-100): Overall quality score
- grade (A-F): Letter grade
- dimensions: Per-dimension scores and details
- issues: Critical problems (8-point penalty each)
- warnings: Non-critical but noteworthy findings
- suggestions: Optional improvements

### quick_evaluate(card_data: Dict) -> str

Get a human-readable evaluation summary.

### get_dimension_scores(card_data: Dict) -> Dict[str, int]

Get per-dimension scores for quick assessment.

## Integration Example

```python
from content_evaluator import evaluate_card

def generate_card(card_data):
    # Validate BEFORE generating images
    evaluation = evaluate_card(card_data)

    if evaluation['issues']:
        # Block generation, return issues to user
        return {'status': 'error', 'issues': evaluation['issues']}

    # Safe to proceed with image generation
    return generate_visual(card_data)
```

## Scoring Details

Letter Grade Mapping:
- A: 90-100
- B: 80-89
- C: 70-79
- D: 60-69
- F: 0-59

Overall score is the average of 8 dimension scores, minus 8 points per critical issue.

## Detection Examples

### Good Design: "Four Loves"

Title: 'The Four Loves'
Steps: 2 items on front
Back text: Explicitly covers all 4 types with bold emphasis
Visual type: comparison

Result: Grade A (94/100)

### Critical Mismatch: "Four Pillars"

Title: 'The Four Pillars'
Steps: 2 items on front
Back text: Generic, no enumeration
Visual type: pyramid_hierarchy (needs 3+ items)

Result: Grade D (70/100)
Issues:
  - Title implies 4 items but only 2 found across front+back
  - pyramid_hierarchy needs at least 3 steps but only 2 provided

## Troubleshooting

### "Title implies 4 items but only 2 found"

Solution options:
1. Add the missing 2 items as steps on the front card
2. Change the title to match actual count
3. Restructure back text to explicitly enumerate all 4 types

### "Visual type needs at least N steps"

Solution:
- Add more steps to match the visual type's constraints
- OR switch to a visual type that supports fewer items

### "None of the front card step labels appear in back text"

Solution:
- Reference the step labels in the back text by name
- This creates coherence between front and back

## Card Data Structure

Required fields:
- card_title: Short title (2-5 words ideal)
- card_category: Category label
- steps: List of {label, description} dicts
- visual_type: e.g. 'comparison', 'pyramid_hierarchy'
- quote: 20-150 chars ideal
- back_text: 100-800 chars, use **bold** for emphasis
- is_islamic_content: Boolean flag

Optional fields:
- islamic_elements: List of visual elements
- card_number: Position in series
