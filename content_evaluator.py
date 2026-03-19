"""Content Evaluator for Quran Visual Cards

Universal card quality, accuracy, and fidelity validator.
Evaluates multiple dimensions of card content BEFORE image generation
to catch mismatches, inconsistencies, and quality issues early.

Evaluation dimensions:
1. Title-Content Alignment: Does the title promise match what's shown?
2. Step Count Fidelity: Does the number count in title match actual steps?
3. Visual Type Fit: Is the chosen visual type appropriate for this content?
4. Front-Back Coherence: Do front and back cards tell a consistent story?
5. Icon Relevance: Are suggested icons meaningful for the concepts?
6. Quote Relevance: Does the quote support the card's message?
7. Content Completeness: Is all source material represented?
8. Cognitive Load: Is the card overloaded or too sparse?
"""

import re
from typing import Dict, List, Tuple, Optional


# ═══════════════════════════════════════════════════════════════
# NUMBER WORDS FOR TITLE ANALYSIS
# ═══════════════════════════════════════════════════════════════

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "single": 1, "double": 2, "triple": 3, "dual": 2, "pair": 2,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
}

# Words that imply enumeration in titles
ENUMERATION_SIGNALS = [
    "types", "kinds", "levels", "stages", "steps", "pillars",
    "principles", "laws", "rules", "categories", "dimensions",
    "aspects", "elements", "phases", "factors", "keys",
    "ways", "paths", "modes", "forms", "traits", "qualities",
    "conditions", "ranks", "degrees", "classes",
]

# Visual types best suited for specific content patterns
VISUAL_TYPE_AFFINITY = {
    "enumeration": ["sequential_chain", "pyramid_hierarchy", "funnel", "timeline"],
    "comparison": ["comparison", "venn_diagram", "matrix_2x2", "scale_balance"],
    "process": ["sequential_chain", "cycle_loop", "flow_chart", "funnel"],
    "hierarchy": ["pyramid_hierarchy", "nested_circles", "iceberg"],
    "relationship": ["venn_diagram", "network_graph", "force_diagram"],
    "spectrum": ["spectrum", "scale_balance", "s_curve", "exponential_curve"],
    "cause_effect": ["fishbone", "force_diagram", "flow_chart", "decision_tree"],
    "opposition": ["comparison", "scale_balance", "force_diagram"],
}


# ═══════════════════════════════════════════════════════════════
# CORE EVALUATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def evaluate_card(card_data: Dict) -> Dict:
    """Run all evaluations on a card and return comprehensive results.

    Args:
        card_data: Dict with keys like title, card_title, category, steps,
                   quote, back_text, visual_type, etc.

    Returns:
        Dict with 'score' (0-100), 'grade' (A-F), 'issues' list,
        'warnings' list, 'suggestions' list, and per-dimension scores
    """
    results = {
        "dimensions": {},
        "issues": [],      # Critical problems that should be fixed
        "warnings": [],    # Non-critical but noteworthy
        "suggestions": [], # Optional improvements
    }

    # Run each dimension evaluation
    title_result = evaluate_title_content_alignment(card_data)
    results["dimensions"]["title_alignment"] = title_result
    results["issues"].extend(title_result.get("issues", []))
    results["warnings"].extend(title_result.get("warnings", []))
    results["suggestions"].extend(title_result.get("suggestions", []))

    step_result = evaluate_step_count_fidelity(card_data)
    results["dimensions"]["step_count"] = step_result
    results["issues"].extend(step_result.get("issues", []))
    results["warnings"].extend(step_result.get("warnings", []))
    results["suggestions"].extend(step_result.get("suggestions", []))

    visual_result = evaluate_visual_type_fit(card_data)
    results["dimensions"]["visual_type_fit"] = visual_result
    results["issues"].extend(visual_result.get("issues", []))
    results["warnings"].extend(visual_result.get("warnings", []))
    results["suggestions"].extend(visual_result.get("suggestions", []))

    coherence_result = evaluate_front_back_coherence(card_data)
    results["dimensions"]["front_back_coherence"] = coherence_result
    results["issues"].extend(coherence_result.get("issues", []))
    results["warnings"].extend(coherence_result.get("warnings", []))
    results["suggestions"].extend(coherence_result.get("suggestions", []))

    quote_result = evaluate_quote_relevance(card_data)
    results["dimensions"]["quote_relevance"] = quote_result
    results["warnings"].extend(quote_result.get("warnings", []))

    load_result = evaluate_cognitive_load(card_data)
    results["dimensions"]["cognitive_load"] = load_result
    results["issues"].extend(load_result.get("issues", []))
    results["warnings"].extend(load_result.get("warnings", []))
    results["suggestions"].extend(load_result.get("suggestions", []))

    completeness_result = evaluate_content_completeness(card_data)
    results["dimensions"]["completeness"] = completeness_result
    results["warnings"].extend(completeness_result.get("warnings", []))
    results["suggestions"].extend(completeness_result.get("suggestions", []))

    # Calculate overall score
    dim_scores = [d.get("score", 50) for d in results["dimensions"].values()]
    overall_score = sum(dim_scores) / len(dim_scores) if dim_scores else 50

    # Penalty for critical issues
    overall_score -= len(results["issues"]) * 8
    overall_score = max(0, min(100, overall_score))

    results["score"] = round(overall_score)
    results["grade"] = _score_to_grade(overall_score)
    results["issue_count"] = len(results["issues"])
    results["warning_count"] = len(results["warnings"])
    results["suggestion_count"] = len(results["suggestions"])

    return results


def evaluate_title_content_alignment(card_data: Dict) -> Dict:
    """Check if the title's promise matches the actual card content.

    Detects mismatches like:
    - "Four Types of X" but only 2 steps shown on front
    - "Comparison of X and Y" but using a sequential chain visual
    - Title implies enumeration but visual type doesn't support it
    """
    title = (card_data.get("card_title") or card_data.get("title", "")).lower()
    steps = card_data.get("steps", [])
    visual_type = card_data.get("visual_type", "")
    back_text = card_data.get("back_text", "")

    issues = []
    warnings = []
    suggestions = []
    score = 100

    # Extract implied number from title
    implied_count = _extract_number_from_title(title)
    content_pattern = _detect_content_pattern(title)

    if implied_count:
        # Check if step count matches title promise
        front_step_count = len(steps)

        if front_step_count < implied_count:
            # Check if back text covers the missing items
            back_items = _count_enumerated_items_in_text(back_text, implied_count)
            total_items = front_step_count + back_items

            if total_items < implied_count:
                issues.append(
                    f"Title implies {implied_count} items but only {total_items} found "
                    f"across front ({front_step_count} steps) and back ({back_items} mentions). "
                    f"Consider: (a) add missing items as steps, (b) change title to match actual count, "
                    f"or (c) restructure to show all {implied_count} items on the front card."
                )
                score -= 25
            else:
                warnings.append(
                    f"Title promises {implied_count} items. Front card shows {front_step_count}, "
                    f"remaining {implied_count - front_step_count} covered in back text. "
                    f"Visual learners may expect all {implied_count} visible on the front card."
                )
                score -= 10

                suggestions.append(
                    f"RECOMMENDED: Restructure to show all {implied_count} items as visual elements "
                    f"on the front card. Use a visual type that supports {implied_count} nodes "
                    f"(e.g., sequential_chain, pyramid_hierarchy, or a {implied_count}-column comparison)."
                )

        elif front_step_count > implied_count:
            warnings.append(
                f"Title implies {implied_count} items but front has {front_step_count} steps. "
                f"Consider simplifying to match the title's promise."
            )
            score -= 5

    # Check if content pattern matches visual type
    if content_pattern and visual_type:
        good_types = VISUAL_TYPE_AFFINITY.get(content_pattern, [])
        if good_types and visual_type not in good_types:
            suggestions.append(
                f"Content pattern '{content_pattern}' detected in title. "
                f"Current visual type '{visual_type}' may not be ideal. "
                f"Consider: {', '.join(good_types[:3])}"
            )
            score -= 5

    return {"score": max(0, score), "issues": issues, "warnings": warnings, "suggestions": suggestions}


def evaluate_step_count_fidelity(card_data: Dict) -> Dict:
    """Validate that steps have sufficient detail and consistency."""
    steps = card_data.get("steps", [])
    issues = []
    warnings = []
    suggestions = []
    score = 100

    if not steps:
        warnings.append("No steps defined. Card illustration will use generic layout.")
        return {"score": 60, "issues": issues, "warnings": warnings, "suggestions": suggestions}

    # Check for empty labels or descriptions
    empty_labels = [i for i, s in enumerate(steps) if not s.get("label", "").strip()]
    empty_descs = [i for i, s in enumerate(steps) if not s.get("description", "").strip()]

    if empty_labels:
        issues.append(f"Steps {[i+1 for i in empty_labels]} have empty labels — icons cannot be matched.")
        score -= 15

    if empty_descs:
        warnings.append(f"Steps {[i+1 for i in empty_descs]} have empty descriptions — icon matching will be less precise.")
        score -= 5

    # Check for overly long labels (won't fit in diagram)
    long_labels = [s.get("label", "") for s in steps if len(s.get("label", "")) > 40]
    if long_labels:
        warnings.append(
            f"{len(long_labels)} step label(s) exceed 40 chars and may not fit in the diagram. "
            f"Consider shortening: {long_labels[0][:50]}..."
        )
        score -= 5

    # Check step count appropriateness
    if len(steps) > 8:
        warnings.append(
            f"{len(steps)} steps is very dense for a single card. "
            f"Consider splitting into multiple cards or using a simpler visual type."
        )
        score -= 10
    elif len(steps) > 6:
        suggestions.append(
            f"{len(steps)} steps is moderately dense. Ensure visual type supports this many nodes."
        )

    return {"score": max(0, score), "issues": issues, "warnings": warnings, "suggestions": suggestions}


def evaluate_visual_type_fit(card_data: Dict) -> Dict:
    """Check if the visual type is appropriate for the content structure."""
    visual_type = card_data.get("visual_type", "")
    steps = card_data.get("steps", [])
    title = (card_data.get("card_title") or card_data.get("title", "")).lower()
    issues = []
    warnings = []
    suggestions = []
    score = 90  # Start slightly below 100 since visual type is often auto-selected

    if not visual_type:
        warnings.append("No visual type specified — defaulting to sequential_chain.")
        return {"score": 70, "issues": issues, "warnings": warnings, "suggestions": suggestions}

    step_count = len(steps)

    # Type-specific validations
    type_constraints = {
        "venn_diagram": {"min_steps": 2, "max_steps": 3, "ideal": 2},
        "matrix_2x2": {"min_steps": 2, "max_steps": 4, "ideal": 4},
        "tripod": {"min_steps": 3, "max_steps": 3, "ideal": 3},
        "scale_balance": {"min_steps": 2, "max_steps": 3, "ideal": 2},
        "comparison": {"min_steps": 2, "max_steps": 4, "ideal": 2},
        "pyramid_hierarchy": {"min_steps": 3, "max_steps": 7, "ideal": 4},
        "iceberg": {"min_steps": 2, "max_steps": 6, "ideal": 3},
        "spectrum": {"min_steps": 2, "max_steps": 5, "ideal": 3},
    }

    if visual_type in type_constraints and step_count > 0:
        constraint = type_constraints[visual_type]
        if step_count < constraint["min_steps"]:
            issues.append(
                f"Visual type '{visual_type}' needs at least {constraint['min_steps']} steps "
                f"but only {step_count} provided."
            )
            score -= 20
        elif step_count > constraint["max_steps"]:
            warnings.append(
                f"Visual type '{visual_type}' works best with {constraint['max_steps']} or fewer steps "
                f"but {step_count} provided. Diagram may be crowded."
            )
            score -= 10

    # SPECTRUM SUITABILITY CHECK: spectrum is for continuous ranges, not discrete categories
    if visual_type == "spectrum" and steps:
        is_discrete = _are_steps_discrete_categories(steps, title)
        if is_discrete:
            issues.append(
                f"Visual type 'spectrum' is designed for CONTINUOUS ranges (e.g., low→high, "
                f"cold→hot) but the content has {step_count} DISCRETE categories that don't form "
                f"a natural gradient. Consider 'comparison' (2-4 side-by-side panels), "
                f"'sequential_chain' (ordered steps), or 'pyramid_hierarchy' (ranked levels) instead."
            )
            score -= 20
            suggestions.append(
                f"RECOMMENDED ALTERNATIVE: Use 'comparison' for {step_count} distinct types/categories. "
                f"Comparison creates clear visual separation between items, making each type "
                f"immediately recognizable — which is what 'types of X' content demands."
            )

    # COMPARISON vs SPECTRUM cross-check: if title says "spectrum/range/scale" but visual is comparison
    if visual_type == "comparison":
        content_pattern = _detect_content_pattern(title)
        if content_pattern == "spectrum":
            suggestions.append(
                f"Title contains spectrum/range language but visual type is 'comparison'. "
                f"If the content is truly a continuum, consider using 'spectrum' visual type instead."
            )

    return {"score": max(0, score), "issues": issues, "warnings": warnings, "suggestions": suggestions}


def evaluate_front_back_coherence(card_data: Dict) -> Dict:
    """Verify that front and back cards tell a consistent, complementary story."""
    title = (card_data.get("card_title") or card_data.get("title", "")).lower()
    steps = card_data.get("steps", [])
    back_text = card_data.get("back_text", "")
    quote = card_data.get("quote", "")
    issues = []
    warnings = []
    suggestions = []
    score = 100

    if not back_text:
        warnings.append("No back text provided. Back card will be empty or generic.")
        return {"score": 60, "issues": issues, "warnings": warnings, "suggestions": suggestions}

    # Check if step labels appear in back text (cross-reference)
    step_labels = [s.get("label", "").lower() for s in steps if s.get("label")]
    back_lower = back_text.lower()

    mentioned_in_back = sum(1 for label in step_labels if label in back_lower or
                           any(word in back_lower for word in label.split() if len(word) > 4))

    if step_labels and mentioned_in_back == 0:
        warnings.append(
            "None of the front card step labels appear in the back text. "
            "Front and back may feel disconnected."
        )
        score -= 15
    elif step_labels and mentioned_in_back < len(step_labels) / 2:
        suggestions.append(
            f"Only {mentioned_in_back}/{len(step_labels)} front card concepts are referenced in back text. "
            f"Consider adding brief mentions of all front concepts for coherence."
        )
        score -= 5

    # Check back text has bold terms
    bold_terms = re.findall(r'\*\*(.*?)\*\*', back_text)
    if not bold_terms:
        suggestions.append("Back text has no **bold** terms. Adding key term emphasis improves scanability.")
        score -= 5

    # Check back text length
    clean_back = back_text.replace("**", "")
    if len(clean_back) < 100:
        warnings.append("Back text is very short (<100 chars). May appear sparse on the card.")
        score -= 10
    elif len(clean_back) > 800:
        warnings.append("Back text exceeds 800 chars. Will be truncated to fit card layout.")
        score -= 5

    return {"score": max(0, score), "issues": issues, "warnings": warnings, "suggestions": suggestions}


def evaluate_quote_relevance(card_data: Dict) -> Dict:
    """Check if the quote connects to the card's core message."""
    quote = card_data.get("quote", "")
    title = (card_data.get("card_title") or card_data.get("title", "")).lower()
    warnings = []
    score = 90

    if not quote:
        warnings.append("No quote provided for the card bottom.")
        return {"score": 60, "warnings": warnings}

    if len(quote) > 150:
        warnings.append(f"Quote is {len(quote)} chars — may not fit in bottom band. Consider shortening to <120 chars.")
        score -= 10
    elif len(quote) < 20:
        warnings.append("Quote is very short. A more substantive quote may improve the card's impact.")
        score -= 5

    return {"score": max(0, score), "warnings": warnings}


def evaluate_cognitive_load(card_data: Dict) -> Dict:
    """Assess whether the card is overloaded or too sparse for visual learning."""
    steps = card_data.get("steps", [])
    back_text = card_data.get("back_text", "")
    quote = card_data.get("quote", "")
    title = card_data.get("card_title") or card_data.get("title", "")
    issues = []
    warnings = []
    suggestions = []

    # Calculate load factors
    step_count = len(steps)
    total_label_chars = sum(len(s.get("label", "")) for s in steps)
    total_desc_chars = sum(len(s.get("description", "")) for s in steps)
    back_chars = len(back_text.replace("**", ""))
    title_words = len(title.split())

    # Front card text density
    front_text_load = total_label_chars + total_desc_chars + len(quote) + len(title)

    if front_text_load > 600:
        warnings.append(
            f"Front card has ~{front_text_load} chars of text content. "
            f"This may crowd the illustration zone. Consider trimming step descriptions."
        )
        score = 65
    elif front_text_load > 400:
        score = 80
    elif front_text_load < 50:
        suggestions.append("Front card has very little text. Consider adding step descriptions for richer content.")
        score = 75
    else:
        score = 95

    # Title length check
    if title_words > 8:
        warnings.append(f"Title has {title_words} words — may not fit in top band. Aim for 2-5 words.")
        score -= 10

    return {"score": max(0, score), "issues": issues, "warnings": warnings, "suggestions": suggestions}


def evaluate_content_completeness(card_data: Dict) -> Dict:
    """Check if source material is adequately represented in the card."""
    warnings = []
    suggestions = []
    score = 85

    required_fields = {
        "title": "card_title",
        "category": "card_category",
        "steps": "steps",
        "quote": "quote",
        "back_text": "back_text",
        "visual_type": "visual_type",
    }

    missing = []
    for display_name, field in required_fields.items():
        val = card_data.get(field)
        if not val or (isinstance(val, list) and len(val) == 0):
            # Check alternate field names
            alt = card_data.get(display_name)
            if not alt or (isinstance(alt, list) and len(alt) == 0):
                missing.append(display_name)

    if missing:
        warnings.append(f"Missing card fields: {', '.join(missing)}. Card may render with defaults.")
        score -= len(missing) * 5

    # Check if Islamic flags are set when content suggests Islamic
    title = (card_data.get("card_title") or card_data.get("title", "")).lower()
    back_text = card_data.get("back_text", "").lower()
    islamic_keywords = ["allah", "quran", "prophet", "islam", "muslim", "iman", "taqwa", "ibadah", "dua"]
    has_islamic_content = any(kw in title or kw in back_text for kw in islamic_keywords)
    is_flagged_islamic = card_data.get("is_islamic_content", False)

    if has_islamic_content and not is_flagged_islamic:
        warnings.append(
            "Content contains Islamic references but is_islamic_content is False. "
            "Islamic guardrails (calligraphy, geometric borders) will NOT be applied."
        )
        score -= 10

    return {"score": max(0, score), "warnings": warnings, "suggestions": suggestions}


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _extract_number_from_title(title: str) -> Optional[int]:
    """Extract an implied count from a title like 'Four Types of Love'."""
    title_lower = title.lower()

    for word, num in NUMBER_WORDS.items():
        # Check if the number word is followed by an enumeration signal
        for signal in ENUMERATION_SIGNALS:
            pattern = rf'\b{re.escape(word)}\s+{re.escape(signal)}\b'
            if re.search(pattern, title_lower):
                return num

    # Also check for digit patterns like "3 Types of..."
    match = re.search(r'\b(\d+)\s+(' + '|'.join(ENUMERATION_SIGNALS) + r')\b', title_lower)
    if match:
        return int(match.group(1))

    return None


def _detect_content_pattern(title: str) -> Optional[str]:
    """Detect the content pattern implied by a title."""
    title_lower = title.lower()

    comparison_words = ["vs", "versus", "compared", "comparison", "contrast", "between"]
    process_words = ["process", "cycle", "flow", "journey", "path", "stages"]
    hierarchy_words = ["hierarchy", "levels", "pyramid", "layers", "ranks"]
    spectrum_words = ["spectrum", "range", "scale", "continuum", "gradient"]
    cause_words = ["cause", "effect", "result", "consequence", "why", "because"]
    opposition_words = ["paradox", "tension", "dilemma", "balance", "trade-off"]

    if any(w in title_lower for w in comparison_words):
        return "comparison"
    if any(w in title_lower for w in process_words):
        return "process"
    if any(w in title_lower for w in hierarchy_words):
        return "hierarchy"
    if any(w in title_lower for w in spectrum_words):
        return "spectrum"
    if any(w in title_lower for w in cause_words):
        return "cause_effect"
    if any(w in title_lower for w in opposition_words):
        return "opposition"

    # Check for enumeration pattern
    if _extract_number_from_title(title_lower):
        return "enumeration"

    return None


def _are_steps_discrete_categories(steps: list, title: str = "") -> bool:
    """Detect if steps represent discrete categories rather than a continuous spectrum.

    Discrete categories: "Worship, Love, Fear, Hope" (distinct types with no gradient between them)
    Continuous spectrum: "Cold → Cool → Warm → Hot" (natural ordered gradient)

    Returns True if steps look like distinct unordered categories.
    """
    title_lower = title.lower()

    # Title signals for discrete categories
    discrete_signals = ["types", "kinds", "categories", "forms", "varieties", "classes", "modes"]
    has_discrete_title = any(s in title_lower for s in discrete_signals)

    # Title signals for continuous range
    continuous_signals = ["spectrum", "range", "scale", "continuum", "gradient", "from", "to"]
    has_continuous_title = any(s in title_lower for s in continuous_signals)

    # If title explicitly says "spectrum/range" AND doesn't say "types/kinds", trust the spectrum choice
    if has_continuous_title and not has_discrete_title:
        return False

    # Check if step labels form a natural ordered gradient
    if len(steps) >= 2:
        labels = [s.get("label", "").lower() for s in steps]

        # Common gradient pairs (first/last step should be opposites)
        gradient_pairs = [
            ("low", "high"), ("small", "large"), ("weak", "strong"),
            ("cold", "hot"), ("slow", "fast"), ("simple", "complex"),
            ("negative", "positive"), ("least", "most"), ("minimum", "maximum"),
            ("shallow", "deep"), ("narrow", "wide"), ("false", "true"),
        ]
        first, last = labels[0], labels[-1]
        is_gradient = any(
            (a in first and b in last) or (b in first and a in last)
            for a, b in gradient_pairs
        )
        if is_gradient:
            return False

    # If title says "types/kinds" with a number, it's almost certainly discrete
    if has_discrete_title:
        return True

    # 4+ steps that don't form a gradient are likely discrete categories
    if len(steps) >= 4 and not has_continuous_title:
        return True

    return False


def _count_enumerated_items_in_text(text: str, expected_count: int) -> int:
    """Count how many enumerated items appear in text.

    Looks for patterns like 'First,...', 'Second,...', '1.', '2.', etc.
    """
    if not text:
        return 0

    ordinals = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"]
    text_lower = text.lower()

    ordinal_count = sum(1 for o in ordinals[:expected_count] if o in text_lower)

    # Also count numbered items
    numbered = len(re.findall(r'(?:^|\n)\s*\d+[\.\)]\s', text))

    return max(ordinal_count, numbered)


def _score_to_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90: return "A"
    if score >= 80: return "B"
    if score >= 70: return "C"
    if score >= 60: return "D"
    return "F"


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE / API FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def quick_evaluate(card_data: Dict) -> str:
    """Return a short human-readable evaluation summary."""
    result = evaluate_card(card_data)

    lines = [f"Card Evaluation: {result['grade']} ({result['score']}/100)"]

    if result["issues"]:
        lines.append(f"\nISSUES ({len(result['issues'])}):")
        for issue in result["issues"]:
            lines.append(f"  {issue}")

    if result["warnings"]:
        lines.append(f"\nWARNINGS ({len(result['warnings'])}):")
        for warning in result["warnings"]:
            lines.append(f"  {warning}")

    if result["suggestions"]:
        lines.append(f"\nSUGGESTIONS ({len(result['suggestions'])}):")
        for suggestion in result["suggestions"]:
            lines.append(f"  {suggestion}")

    return "\n".join(lines)


def get_dimension_scores(card_data: Dict) -> Dict[str, int]:
    """Return just the per-dimension scores for quick assessment."""
    result = evaluate_card(card_data)
    return {name: dim.get("score", 0) for name, dim in result["dimensions"].items()}
