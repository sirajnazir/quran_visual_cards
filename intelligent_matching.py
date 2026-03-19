"""Intelligent Mental Model Matching Engine

Loads the comprehensive mental models repository and scores/matches
incoming content against all 100+ models to find the best fit.
"""
import json
import os
import re
from collections import defaultdict
from config import MENTAL_MODELS_DB, VISUAL_TYPES


class ModelRepository:
    """Loads and indexes the mental models repository for fast matching."""

    def __init__(self):
        self.models = []
        self.models_by_id = {}
        self.models_by_category = defaultdict(list)
        self.keyword_index = defaultdict(list)
        self.visual_types_catalog = {}
        self.categories = []
        self._loaded = False
        self._load()

    def _load(self):
        """Load mental_models.json and build indexes."""
        if not os.path.exists(MENTAL_MODELS_DB):
            print(f"[ModelRepository] Warning: {MENTAL_MODELS_DB} not found. Using empty repo.")
            self._loaded = False
            return

        try:
            with open(MENTAL_MODELS_DB, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.models = data.get("models", [])
            self.visual_types_catalog = data.get("visual_types_catalog", {})
            self.categories = data.get("categories", [])

            # Build indexes
            for model in self.models:
                mid = model["id"]
                self.models_by_id[mid] = model
                self.models_by_category[model.get("category", "Unknown")].append(model)

                # Keyword index: map each keyword to model IDs
                for kw in model.get("keywords", []):
                    self.keyword_index[kw.lower()].append(mid)

                # Also index name words
                for word in model.get("name", "").lower().split():
                    if len(word) > 3:
                        self.keyword_index[word].append(mid)

            self._loaded = True
            print(f"[ModelRepository] Loaded {len(self.models)} models, "
                  f"{len(self.categories)} categories, "
                  f"{len(self.visual_types_catalog)} visual types")

        except Exception as e:
            print(f"[ModelRepository] Error loading: {e}")
            self._loaded = False

    @property
    def is_loaded(self):
        return self._loaded and len(self.models) > 0

    def get_model(self, model_id):
        """Get a single model by ID."""
        return self.models_by_id.get(model_id)

    def get_category_models(self, category):
        """Get all models in a category."""
        return self.models_by_category.get(category, [])

    def search(self, query, limit=10):
        """Simple keyword search across all models."""
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        scored = []

        for model in self.models:
            score = 0
            model_text = f"{model['name']} {model.get('description', '')} {' '.join(model.get('keywords', []))}".lower()

            # Exact phrase match in name
            if query_lower in model["name"].lower():
                score += 10

            # Word matches
            for word in query_words:
                if word in model_text:
                    score += 1
                # Keyword exact match gets bonus
                if word in [k.lower() for k in model.get("keywords", [])]:
                    score += 2

            if score > 0:
                scored.append((score, model))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:limit]]

    def get_all_visual_types(self):
        """Return the visual types catalog."""
        return self.visual_types_catalog


def extract_signals(title, category, analysis_text):
    """Extract topic signals, structural patterns, and metaphors from input text.

    Returns a dict of signals used for model scoring.
    """
    text = f"{title} {category} {analysis_text}".lower()
    words = set(re.findall(r'\w+', text))

    signals = {
        "title": title,
        "category": category,
        "words": words,
        "text_lower": text,
        "structural_patterns": [],
        "metaphors": [],
        "relationships": [],
        "topic_hints": [],
    }

    # Detect structural patterns
    pattern_keywords = {
        "sequential": ["then", "leads to", "step", "first", "second", "third", "chain",
                       "sequence", "order", "follows", "next", "preceding", "after",
                       "progression", "journey", "path", "stage", "advance", "develop",
                       "evolve", "transform"],
        "cyclical": ["cycle", "loop", "repeat", "circular", "feedback", "reinforc",
                     "self-perpetuat", "revolv", "spiral", "recursive", "back to",
                     "trap", "caught", "addic", "habit", "return", "temptation",
                     "desire", "pull", "enslav"],
        "hierarchical": ["hierarchy", "level", "layer", "foundation", "top", "bottom",
                         "base", "pinnacle", "pyramid", "priority", "rank"],
        "comparative": ["versus", "vs", "compared", "contrast", "differ", "similar",
                        "unlike", "opposite", "paradox", "tension", "conflict",
                        "duality", "struggle", "resist", "fight", "tempt", "choice",
                        "inner conflict"],
        "categorization": ["types", "type", "kinds", "kind", "categories", "category",
                           "classification", "forms", "varieties", "classes", "modes",
                           "distinction", "distinguish", "separate", "divide", "divided",
                           "groups", "grouping", "sort", "sorting", "taxonomy",
                           "four", "three", "two", "multiple", "several", "different",
                           "each", "respectively", "among", "some", "others",
                           "quality", "qualities"],
        "causal": ["cause", "effect", "result", "consequence", "because", "therefore",
                   "impact", "influence", "leads", "produces", "generates",
                   "motivat", "driven by", "root cause", "underlying", "stemming from"],
        "balance": ["balance", "equilibrium", "trade-off", "tradeoff", "moderate",
                    "middle", "between", "both", "neither", "spectrum",
                    "resist", "extremes", "boundary", "limit", "moderat", "temptation",
                    "test", "trial", "self-control", "discipline"],
        "accumulative": ["compound", "accumulate", "grow", "exponential", "snowball",
                         "build up", "increase", "multiply", "accelerat"],
        "filtering": ["filter", "narrow", "select", "eliminate", "reduce", "funnel",
                      "distill", "focus", "prioritize", "cut"],
        "network": ["connect", "network", "relationship", "link", "system",
                    "interdepend", "ecosystem", "web", "cluster"],
        "threshold": ["tipping", "threshold", "critical mass", "breaking point",
                      "trigger", "catalyst", "inflection", "pivot",
                      "resist", "boundary", "limit", "crossing", "point of no return",
                      "moral", "test", "trial", "moment of truth", "decision point",
                      "brink"],
        "warning_contrast": ["beware", "warning", "danger", "avoid", "forbidden",
                             "wrong", "right", "correct", "incorrect", "true", "false",
                             "authentic", "fake", "superficial", "genuine", "real",
                             "mere", "claim", "claims", "sufficient", "insufficient",
                             "polytheist", "believer", "hypocrit"],
    }

    for pattern, keywords in pattern_keywords.items():
        matches = sum(1 for kw in keywords if kw in text)
        if matches >= 2:
            signals["structural_patterns"].append((pattern, matches))

    # Sort patterns by match strength
    signals["structural_patterns"].sort(key=lambda x: x[1], reverse=True)

    # Detect topic hints
    topic_keywords = {
        "cognitive_bias": ["bias", "heuristic", "fallacy", "cognitive", "thinking error",
                           "judgment", "perception", "illusion"],
        "decision_making": ["decision", "choose", "option", "alternative", "judgment",
                            "evaluate", "assess", "weigh"],
        "economics": ["cost", "benefit", "value", "market", "price", "supply",
                      "demand", "economy", "trade", "incentive"],
        "psychology": ["behavior", "motivation", "emotion", "mindset", "belief",
                       "attitude", "personality", "habit", "influence"],
        "systems": ["system", "feedback", "dynamic", "complex", "emergent",
                    "interaction", "component", "holistic"],
        "strategy": ["strategy", "competitive", "advantage", "position",
                     "differentiat", "innovate", "disrupt"],
        "islamic": ["quran", "allah", "prophet", "surah", "islamic", "muslim",
                    "taqwa", "ibadah", "deen", "ummah", "sunnah", "iman",
                    "tawakkul", "dunya", "akhira", "sabr", "shukr",
                    # Prophet names
                    "yusuf", "musa", "ibrahim", "adam", "nuh", "isa", "dawud",
                    "sulayman", "ayyub", "yunus", "muhammad",
                    # Spiritual concepts
                    "temptation", "test", "trial", "fitna", "patience", "sin",
                    "repentance", "tawbah", "nafs", "shaytan", "haram", "halal",
                    "jannah", "hellfire", "believer", "worship", "prayer",
                    "forgiveness", "mercy", "guidance", "hidayah", "rizq",
                    # Spiritual states
                    "dhikr", "khushu", "zuhd", "yaqeen", "ihsan", "tawbah",
                    "ikhlas", "birr", "fasad", "istighfar"],
    }

    for topic, keywords in topic_keywords.items():
        matches = sum(1 for kw in keywords if kw in text)
        # Islamic content triggers on a single keyword (e.g., a prophet name)
        threshold = 1 if topic == "islamic" else 2
        if matches >= threshold:
            signals["topic_hints"].append((topic, matches))

    signals["topic_hints"].sort(key=lambda x: x[1], reverse=True)

    return signals


def score_models(signals, repo):
    """Score all models in the repository against extracted signals.

    Returns list of (model, score, breakdown) tuples sorted by score descending.
    """
    if not repo.is_loaded:
        return []

    results = []
    words = signals["words"]
    text = signals["text_lower"]

    for model in repo.models:
        breakdown = {"keyword": 0, "when_to_use": 0, "category": 0, "visual_pattern": 0, "name": 0}

        # 1. Keyword matching (20% weight)
        model_keywords = [kw.lower() for kw in model.get("keywords", [])]
        keyword_hits = sum(1 for kw in model_keywords if kw in text)
        keyword_score = min(keyword_hits / max(len(model_keywords), 1), 1.0)
        breakdown["keyword"] = keyword_score

        # 2. when_to_use overlap (10% weight)
        when_to_use = model.get("when_to_use", "").lower()
        if when_to_use:
            wtu_words = set(re.findall(r'\w+', when_to_use))
            wtu_words -= {"the", "a", "an", "is", "of", "and", "or", "to", "for", "with", "when", "this", "that", "it"}
            wtu_overlap = len(words & wtu_words) / max(len(wtu_words), 1)
            breakdown["when_to_use"] = min(wtu_overlap, 1.0)

        # 3. Category/topic relevance (15% weight)
        category_score = 0
        model_category = model.get("category", "").lower()
        for topic, strength in signals.get("topic_hints", []):
            # Map topic hints to model categories
            topic_cat_map = {
                "cognitive_bias": "cognitive biases",
                "decision_making": "decision-making",
                "economics": "economics & strategy",
                "psychology": "psychology & behavioral",
                "systems": "systems thinking",
                "strategy": "economics & strategy",
                "islamic": "islamic / quranic",
            }
            mapped_cat = topic_cat_map.get(topic, "")
            if mapped_cat and mapped_cat in model_category:
                category_score = min(strength / 4, 1.0)
                break
        breakdown["category"] = category_score

        # 4. Visual pattern matching (30% weight)
        visual_score = 0
        model_visual = model.get("visual_type", "")
        model_visual_alts = [v.lower() for v in model.get("visual_types_alt", [])]
        pattern_visual_map = {
            "sequential": ["sequential_chain", "flow_chart", "timeline"],
            "cyclical": ["cycle_loop", "flow_chart", "force_diagram"],
            "hierarchical": ["pyramid_hierarchy", "nested_circles", "iceberg"],
            "comparative": ["comparison", "venn_diagram", "matrix_2x2", "force_diagram",
                            "scale_balance", "spectrum"],
            "categorization": ["comparison", "matrix_2x2", "pyramid_hierarchy",
                               "sequential_chain", "nested_circles"],
            "causal": ["fishbone", "sequential_chain", "decision_tree", "force_diagram"],
            "balance": ["scale_balance", "spectrum", "tripod", "force_diagram", "cycle_loop"],
            "accumulative": ["exponential_curve", "s_curve"],
            "filtering": ["funnel", "pyramid_hierarchy"],
            "network": ["network_graph", "force_diagram", "venn_diagram"],
            "threshold": ["s_curve", "exponential_curve", "force_diagram", "scale_balance",
                          "spectrum"],
            "warning_contrast": ["comparison", "force_diagram", "scale_balance",
                                 "decision_tree"],
        }

        for pattern, strength in signals.get("structural_patterns", []):
            matching_visuals = pattern_visual_map.get(pattern, [])
            # Primary visual match
            if model_visual in matching_visuals:
                visual_score = max(visual_score, min(strength / 4, 1.0))
            # Alt visual matches get 70% credit
            for alt_v in model_visual_alts:
                if alt_v in matching_visuals:
                    alt_score = min(strength / 4, 1.0) * 0.70
                    visual_score = max(visual_score, alt_score)
        breakdown["visual_pattern"] = visual_score

        # 5. Name/description similarity (25% weight)
        name_words = set(model.get("name", "").lower().split())
        desc_words = set(re.findall(r'\w+', model.get("description", "").lower()))
        name_overlap = len(words & name_words) / max(len(name_words), 1)
        desc_overlap = len(words & desc_words) / max(min(len(desc_words), 20), 1)
        name_score = min(name_overlap * 0.6 + desc_overlap * 0.4, 1.0)

        # Bonus: exact title match
        if model.get("name", "").lower() in text:
            name_score = min(name_score + 0.5, 1.0)
        breakdown["name"] = name_score

        # 6. Cross-domain structural affinity (NEW — enables non-Quranic models to surface for Islamic content)
        # If content has structural patterns AND this model's visual type matches those patterns,
        # give it credit even if it's from a different topic/category domain.
        # This is how "System 1 vs System 2" (comparison) can surface for Quranic "types of love" content.
        cross_domain_score = 0
        if signals.get("structural_patterns") and not model.get("is_quranic"):
            for pattern, strength in signals["structural_patterns"]:
                matching_visuals = pattern_visual_map.get(pattern, [])
                if model_visual in matching_visuals:
                    cross_domain_score = max(cross_domain_score, min(strength / 5, 0.8))
                for alt_v in model_visual_alts:
                    if alt_v in matching_visuals:
                        alt_score = min(strength / 5, 0.8) * 0.60
                        cross_domain_score = max(cross_domain_score, alt_score)
        breakdown["cross_domain"] = cross_domain_score

        # Weighted total (20% + 10% + 15% + 25% + 25% + 5% = 100%)
        # Reduced visual_pattern from 30→25%, added cross_domain at 5%
        total = (
            breakdown["keyword"] * 0.20 +
            breakdown["when_to_use"] * 0.10 +
            breakdown["category"] * 0.15 +
            breakdown["visual_pattern"] * 0.25 +
            breakdown["name"] * 0.25 +
            breakdown["cross_domain"] * 0.05
        )

        # Bonus for Quranic models if Islamic content detected
        if model.get("is_quranic") and any(t[0] == "islamic" for t in signals.get("topic_hints", [])):
            total = min(total + 0.15, 1.0)

        if total > 0.05:  # Minimum threshold
            results.append((model, round(total, 3), breakdown))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def get_top_matches(title, category, analysis_text, repo, n=5, expand_related=False):
    """High-level function: extract signals and return top N matching models.

    Returns list of dicts with model info and confidence scores.
    When expand_related=True, pulls related_models from top 3 and merges
    them into candidates if they scored > 0.05. Caps at n+2 models.
    """
    signals = extract_signals(title, category, analysis_text)
    scored = score_models(signals, repo)

    # Build scored lookup for expand_related
    scored_by_id = {m["id"]: (m, s, b) for m, s, b in scored}

    top = []
    seen_ids = set()
    for model, score, breakdown in scored[:n]:
        seen_ids.add(model["id"])
        top.append(_model_to_dict(model, score, breakdown))

    # Expand related models from top 3
    if expand_related and len(top) >= 1:
        related_candidates = []
        for match in top[:3]:
            for related_id in match.get("related_models", []):
                if related_id not in seen_ids and related_id in scored_by_id:
                    r_model, r_score, r_breakdown = scored_by_id[related_id]
                    if r_score > 0.05:
                        seen_ids.add(related_id)
                        related_candidates.append(_model_to_dict(r_model, r_score, r_breakdown))
        # Merge related candidates, cap at n+2
        related_candidates.sort(key=lambda m: m["confidence"], reverse=True)
        for rc in related_candidates:
            if len(top) >= n + 2:
                break
            top.append(rc)

    # ─── CROSS-DOMAIN STRUCTURAL TEMPLATES ───
    # If all top matches are from ONE category (e.g., all Quranic), inject the best
    # structurally-relevant model from a DIFFERENT domain as a "structural template".
    # This gives Claude a non-domain model to ADAPT from (e.g., "System 1 vs System 2"
    # as a structural template for "Types of Love" — both are comparison/categorization).
    if expand_related and len(top) >= 2:
        top_categories = set(m.get("category", "") for m in top)
        if len(top_categories) <= 1:
            # All from same category — find best cross-domain structural match
            dominant_cat = top_categories.pop() if top_categories else ""
            # Find the best cross-domain model — prefer models whose visual type
            # matches the content's strongest structural pattern (not just highest score)
            best_pattern = signals["structural_patterns"][0][0] if signals.get("structural_patterns") else ""
            pattern_visuals = {
                "categorization": ["comparison", "matrix_2x2"],
                "comparative": ["comparison", "scale_balance"],
                "sequential": ["sequential_chain", "flow_chart"],
                "cyclical": ["cycle_loop"],
                "hierarchical": ["pyramid_hierarchy", "nested_circles"],
                "warning_contrast": ["comparison", "force_diagram"],
                "balance": ["scale_balance", "spectrum"],
                "causal": ["fishbone", "force_diagram"],
            }
            preferred_visuals = pattern_visuals.get(best_pattern, [])

            cross_domain_best = None
            cross_domain_fallback = None
            for model, score, breakdown in scored:
                if model["id"] not in seen_ids and model.get("category", "") != dominant_cat:
                    if breakdown.get("visual_pattern", 0) > 0 or breakdown.get("cross_domain", 0) > 0:
                        # Prefer model whose primary visual matches the content pattern
                        if model.get("visual_type", "") in preferred_visuals:
                            cross_domain_best = (model, score, breakdown)
                            break
                        elif not cross_domain_fallback:
                            cross_domain_fallback = (model, score, breakdown)
            if not cross_domain_best:
                cross_domain_best = cross_domain_fallback
            if cross_domain_best:
                cd_model, cd_score, cd_breakdown = cross_domain_best
                seen_ids.add(cd_model["id"])
                cd_entry = _model_to_dict(cd_model, cd_score, cd_breakdown)
                cd_entry["cross_domain_template"] = True  # Flag for Phase 2 context
                top.append(cd_entry)
                print(f"[Matching] Injected cross-domain template: {cd_model['name']} "
                      f"({cd_model.get('category', '')}) score={cd_score:.3f}")

    # Re-sort the full list
    top.sort(key=lambda m: m["confidence"], reverse=True)

    return top, signals


def _model_to_dict(model, score, breakdown):
    """Convert a model + score + breakdown into a standard match dict."""
    return {
        "id": model["id"],
        "name": model["name"],
        "category": model.get("category", ""),
        "visual_type": model.get("visual_type", ""),
        "visual_description": model.get("visual_description", ""),
        "description": model.get("description", ""),
        "confidence": score,
        "breakdown": breakdown,
        "is_quranic": model.get("is_quranic", False),
        "key_elements": model.get("key_elements", []),
        "keywords": model.get("keywords", [])[:8],
        "when_to_use": model.get("when_to_use", ""),
        "visual_types_alt": model.get("visual_types_alt", []),
        "related_models": model.get("related_models", []),
    }


def get_illustration_prompt_for_visual_type(visual_type, card_data=None):
    """Generate detailed illustration description for a given visual type.

    Maps any of the 20 visual types to a detailed hand-drawn sketch description.
    Uses card_data (steps, title, etc.) to customize with specific icons, labels, and Arabic text.
    Uses step_emotions (from LLM Phase 2) to embed per-panel hero emotions INLINE within
    each panel's definition — so Gemini sees them as part of the panel, not an afterthought.

    Matches the quality and specificity of the original PROMPTS.md prompts that produced great images.
    """
    steps = card_data.get("steps", []) if card_data else []
    title = card_data.get("title", "Concept") if card_data else "Concept"
    num_steps = len(steps)
    arabic_labels = ", ".join(s.get("arabic", "") for s in steps if s.get("arabic")) if steps else ""

    # Build step_emotion lookup: label → emotion string
    step_emotions_list = card_data.get("step_emotions", []) if card_data else []
    _emotion_lookup = {}
    if step_emotions_list:
        for entry in step_emotions_list:
            if isinstance(entry, dict):
                _emotion_lookup[entry.get("label", "").lower()] = entry.get("emotion", "")
    # Also index by position for fallback
    _emotion_by_idx = {}
    for idx, entry in enumerate(step_emotions_list):
        if isinstance(entry, dict) and entry.get("emotion"):
            _emotion_by_idx[idx] = entry["emotion"]

    # Build DETAILED step descriptions matching original prompt style:
    # "Step 1: WORSHIP (Servitude) — a man kneeling in prayer, labeled "1. WORSHIP" with Arabic text beneath"
    def _build_detailed_steps():
        if not steps:
            return ""
        lines = []
        for i, s in enumerate(steps):
            label = s.get("label", f"Step {i+1}")
            desc = s.get("description", "")
            arabic = s.get("arabic", "")
            # Derive icon hint from step description instead of generic icon
            icon_hint = f"icon representing {desc[:40]}" if desc else f"icon for {label}"
            step_line = f'  Step {i+1}: {label.upper()}'
            if desc:
                step_line += f' — {desc}'
            step_line += f', shown as a {icon_hint}'
            step_line += f', labeled "{i+1}. {label.upper()}"'
            if arabic:
                step_line += f' with Arabic text "{arabic}" beneath'
            lines.append(step_line)
        result = "\n".join(lines)
        result += "\nEach step shown with a distinct icon derived from its meaning, with labels underneath."
        return result

    steps_desc = "; ".join(f"{s.get('label', '')}" for s in steps) if steps else ""

    prompts = {
        "venn_diagram": (
            f"A Venn diagram with two large overlapping golden/yellow circles. "
            + (f"Left circle labeled \"{steps[0].get('label', 'CONCEPT A')}\", "
               f"right circle labeled \"{steps[1].get('label', 'CONCEPT B')}\". " if len(steps) >= 2
               else "Left circle labeled with first concept, right circle with second concept. ")
            + f"The overlap zone labeled \"WIN/WIN\" with an arrow pointing to it. "
            f"Hand-drawn rough circle edges. "
            f"Simple, bold, conceptual sketch."
        ),
        "cycle_loop": (
            f"A CIRCULAR LOOP / CYCLE with {max(num_steps, 4)} nodes arranged in a circle, "
            f"connected by curved hand-drawn arrows showing continuous cycle:\n"
            + ("\n".join(
                f'  Node {i+1}: "{s.get("label", "").upper()}"'
                + (f' ({s.get("arabic", "")})' if s.get("arabic") else "")
                + (f' — icon of {s.get("description", "")}' if s.get("description") else "")
                for i, s in enumerate(steps)
            ) if steps else "  Nodes with relevant labels and icons")
            + f"\nArrows show the loop getting tighter with each revolution."
            + (f"\n\nHERO IN THE CYCLE: The hero appears at key nodes of the cycle, "
               f"with expression changing to match each node's emotional meaning."
               if num_steps >= 2 else "")
        ),
        "sequential_chain": (
            f"A SEQUENTIAL CHAIN showing {max(num_steps, 3)} steps connected by hand-drawn arrows:\n"
            + _build_detailed_steps()
            + f"\nHand-drawn textured arrows connect each step left-to-right."
            + (f"\n\nHERO ACROSS STEPS: The hero character appears at each step of the chain, "
               f"with facial expression CHANGING to match each step's emotional tone — "
               f"showing the hero's journey/transformation as they progress through the chain."
               if num_steps >= 2 else "")
        ),
        "decision_tree": (
            f"Branching tree structure from a single root question at top. "
            f"Yes/No branches leading to different outcomes. "
            f"3-4 levels deep with diamond decision nodes and rectangular outcome boxes. "
            f"Hand-drawn lines connecting decisions to outcomes."
            + (f"\nBranch labels: " + "; ".join(s.get("label", "") for s in steps) if steps else "")
        ),
        "matrix_2x2": (
            f"Four-quadrant grid drawn with thick hand-drawn lines. "
            f"Two labeled axes (horizontal and vertical). "
            + (f"Quadrants labeled: " + ", ".join(f'"{s.get("label", "")}"' for s in steps[:4]) + ". " if steps else "")
            + f"Key items or icons placed in appropriate quadrants. "
            f"Bold hand-lettered axis labels."
            + (f"\n\nHERO IN EACH QUADRANT: The hero appears in each of the 4 quadrants "
               f"with a DIFFERENT expression matching that quadrant's emotional meaning — "
               f"positive quadrants show happy/confident hero, negative ones show worried/sad hero."
               if num_steps >= 2 else "")
        ),
        "pyramid_hierarchy": (
            f"Triangular pyramid with {max(num_steps, 3)} horizontal levels. "
            f"Widest level at base, narrowest at peak.\n"
            + ("\n".join(
                f'  Level {i+1}: "{s.get("label", "").upper()}"'
                + (f' — {s.get("description", "")}' if s.get("description") else "")
                + (f' with Arabic "{s.get("arabic", "")}"' if s.get("arabic") else "")
                for i, s in enumerate(steps)
            ) if steps else f"  Each level labeled: {steps_desc or 'Foundation, Middle, Peak'}.")
            + f"\nHand-drawn with slight imperfections, cross-hatched shading on each level."
        ),
        "iceberg": (
            f"Large iceberg shape with waterline clearly drawn across middle. "
            + (f'ABOVE water (small tip, ~20%): labeled "{steps[0].get("label", "Visible")}" — {steps[0].get("description", "")}. '
               if steps else "ABOVE water (small tip, ~20%): labeled with visible/surface concept. ")
            + (f'BELOW water (large mass, ~80%): labeled with hidden layers: '
               + ", ".join(f'"{s.get("label", "")}"' for s in steps[1:])
               if len(steps) > 1 else "BELOW water (large mass, ~80%): labeled with hidden/deeper concepts")
            + f". Wavy waterline drawn in blue. Cross-section view."
        ),
        "fishbone": (
            f"Central horizontal spine (the effect/problem) with angled bones branching off. "
            + (f"Main cause categories as major bones: "
               + ", ".join(f'"{s.get("label", "")}"' for s in steps) + ". "
               if steps else "4-6 main cause categories as major bones. ")
            + f"Smaller sub-causes branching from each major bone. "
            f"Fish head on the right side representing the main effect. "
            f"Hand-drawn with visible marker texture."
        ),
        "funnel": (
            f"Wide-mouth funnel at top, narrowing progressively to narrow output at bottom. "
            + (f"{num_steps} labeled stages as the funnel narrows:\n"
               + "\n".join(
                   f'  Stage {i+1}: "{s.get("label", "").upper()}" — {s.get("description", "")}'
                   + (f' (Arabic: "{s.get("arabic", "")}")' if s.get("arabic") else "")
                   for i, s in enumerate(steps))
               if steps else "3-4 labeled stages as the funnel narrows.")
            + f"\nItems/icons entering at top, fewer passing through each stage. "
            f"Hand-drawn with stippled shading showing volume decrease."
        ),
        "scale_balance": (
            f"A DRAMATIC BALANCE SCALE showing tension between competing forces:\n"
            f"\n"
            f"FULCRUM: An ornate, hand-drawn triangular fulcrum at center base, with decorative\n"
            f"cross-hatching and a small ornamental flourish at the apex. The balance beam rests on top.\n"
            f"\n"
            f"BEAM: A thick horizontal beam, visibly TILTED (not level) to show imbalance —\n"
            f"the heavier side dips down dramatically.\n"
            f"\n"
            + (f'LEFT PAN (heavier, lower): Labeled "{steps[0].get("label", "").upper()}"'
               + (f' with Arabic "{steps[0].get("arabic", "")}"' if steps[0].get("arabic") else "")
               + f'. Contains icons/symbols representing {steps[0].get("description", "this concept")}.\n'
               f'RIGHT PAN (lighter, higher): Labeled "{steps[1].get("label", "").upper()}"'
               + (f' with Arabic "{steps[1].get("arabic", "")}"' if steps[1].get("arabic") else "")
               + f'. Contains icons/symbols representing {steps[1].get("description", "this concept")}.\n'
               if len(steps) >= 2
               else "LEFT PAN (heavier, lower): labeled with the dominant concept, icons inside.\n"
                    "RIGHT PAN (lighter, higher): labeled with the weaker concept, icons inside.\n")
            + f"\n"
            f"PAN DETAILS:\n"
            f"  - Pans hang from the beam by chains or thick ropes, hand-drawn with visible links\n"
            f"  - The lighter (higher) pan has elements spilling out or floating away — showing loss\n"
            f"  - The heavier (lower) pan has elements packed in and overflowing — showing weight/importance\n"
            f"  - Small icons/symbols inside each pan representing the concepts being weighed\n"
            f"\n"
            f"LABELS: Bold hand-lettered labels above or below each pan. Arabic text beneath in smaller script.\n"
            f"STYLE: Hand-drawn sketch with visible pen strokes, wobble lines on chains,\n"
            f"cross-hatching on the fulcrum, stippled shading in the pans."
        ),
        "network_graph": (
            f"Multiple circular nodes connected by lines showing relationships. "
            + (f"Nodes: " + ", ".join(f'"{s.get("label", "")}"' for s in steps) + ". " if steps else "")
            + f"Central hub node(s) larger, peripheral nodes smaller. "
            f"Lines vary in thickness to show strength of connection. "
            f"Organic, hand-drawn layout (not perfectly symmetric)."
        ),
        "timeline": (
            f"Horizontal line with milestone markers along it, left to right. "
            + (f"{num_steps} key stages marked with icons above the line:\n"
               + "\n".join(f'  {i+1}. "{s.get("label", "")}" — {s.get("description", "")}' for i, s in enumerate(steps))
               if steps else "3-5 key events or stages marked with icons above the line.")
            + f"\nHand-drawn arrow pointing right showing progression. "
            f"Brief labels above each milestone."
        ),
        "s_curve": (
            f"S-shaped curve on a simple X-Y axis. "
            f"Slow start at bottom-left, rapid growth in middle, plateau at top-right. "
            f"Key inflection point/tipping point marked with a circle and label. "
            + (f"Phases labeled: " + ", ".join(s.get("label", "") for s in steps) + ". " if steps else
               "Three phases labeled: Introduction, Growth, Maturity. ")
            + f"Hand-drawn curve with visible pen strokes."
        ),
        "exponential_curve": (
            f"Hockey-stick shaped curve on X-Y axes. "
            f"Long flat beginning then dramatic upward acceleration. "
            f"Key acceleration point marked with exclamation. "
            f"Comparison dotted line showing linear growth for contrast. "
            f"Labels on axes and the dramatic growth zone."
        ),
        "comparison": (
            f"A COMPARISON / CONTRAST layout with clearly divided panels:\n"
            f"\n"
            f"STRUCTURE: {'Two' if num_steps <= 2 else str(min(num_steps, 4))} side-by-side vertical panels, "
            f"each separated by a bold hand-drawn vertical divider line. Equal width per panel.\n"
            f"The hero character appears in EVERY panel with a DIFFERENT facial expression.\n"
            f"\n"
            + (("\n".join(
                f'PANEL {i+1}: "{s.get("label", "").upper()}"'
                + (f' (Arabic: "{s.get("arabic", "")}")' if s.get("arabic") else "")
                + f'\n  - Central illustration/icon: {s.get("description", "visual representing this concept")}'
                + (f'\n  - {"✗ mark (wrong/rejected)" if i == 0 and "wrong" in s.get("description", "").lower() else "✓ mark (correct/ideal)" if "right" in s.get("description", "").lower() or "correct" in s.get("description", "").lower() else "distinctive icon for this concept"}')
                + f'\n  - 2-3 bullet icons beneath illustrating key attributes'
                # INLINE HERO EMOTION — embedded right in the panel definition
                + (f'\n  - HERO IN THIS PANEL: {_emotion_lookup.get(s.get("label", "").lower(), _emotion_by_idx.get(i, ""))}'
                   if (_emotion_lookup.get(s.get("label", "").lower()) or _emotion_by_idx.get(i))
                   else "")
                for i, s in enumerate(steps[:4])
               ) + "\n")
               if steps
               else "LEFT PANEL: First concept with X mark icon. RIGHT PANEL: Second concept with checkmark.\n")
            + f"\n"
            f"VISUAL CONTRAST (critical for comparison cards):\n"
            f"  - Each panel should look visually DISTINCT — different icons, different hatching patterns\n"
            f"  - Use cross-hatching in one panel vs stipple dots in the other to create visual contrast\n"
            f"  - Panel headers bold and underlined at the top of each panel\n"
            f"  - Mirror layout: labels at same heights across panels for easy left-right scanning\n"
            f"\n"
            f"HERO EMOTIONS ACROSS PANELS (CRITICAL — this makes or breaks the card):\n"
            f"  - The hero character MUST appear in EVERY panel with a CLEARLY DIFFERENT expression\n"
            f"  - This is the MOST IMPORTANT visual element — the emotional contrast tells the story\n"
            f"  - The hero's face in positive panels must be VISIBLY HAPPY (wide smile, bright eyes)\n"
            f"  - The hero's face in negative panels must be VISIBLY SAD/DISTRESSED (frown, downcast eyes, slumped)\n"
            f"  - If all panels show a similar expression, the card FAILS its purpose\n"
            f"  - Draw the hero at roughly 30-40% of panel height so icons and labels still fit\n"
            f"\n"
            f"LABELS: Bold hand-lettered panel headers. Arabic text beneath English labels.\n"
            f"STYLE: Hand-drawn panels with thick divider lines. Clean, high-contrast composition."
        ),
        "tripod": (
            f"A TRIPOD / THREE PILLARS structure:\n"
            f"Three equal pillars supporting a platform beam labeled \"{title.upper()}\" on top.\n"
            + ("\n".join(
                f'  Pillar {i+1}: "{s.get("label", "").upper()}"'
                + (f' with Arabic "{s.get("arabic", "")}"' if s.get("arabic") else "")
                + (f' — icon of {s.get("description", "")}' if s.get("description") else "")
                for i, s in enumerate(steps)
            ) if steps else f"  Pillars labeled: {steps_desc or 'Pillar 1, Pillar 2, Pillar 3'}.")
            + f"\nHand-drawn sketch style, pillars with cross-hatch shading"
        ),
        "flow_chart": (
            f"Process flow with multiple paths and decision points. "
            f"Rounded rectangles for processes, diamonds for decisions. "
            + (f"Process steps: " + " → ".join(s.get("label", "") for s in steps) + ". " if steps else "")
            + f"Arrows showing flow direction, some paths converging. "
            f"Hand-drawn boxes and arrows with visible pen texture."
        ),
        "force_diagram": (
            f"A FORCE DIAGRAM showing competing pressures on a central element:\n"
            f"\n"
            f"CENTER: A bold, rounded rectangle or shield shape in the middle, labeled \"{title.upper()}\"\n"
            f"with thick black outlines and subtle cross-hatching fill to give it weight and presence.\n"
            f"\n"
            + (f"FORCES ({num_steps} total):\n"
               + "\n".join(
                   f'  {"→ PUSH IN" if i % 2 == 0 else "← PUSH OUT"}: '
                   f'thick hand-drawn arrow labeled "{s.get("label", "").upper()}"'
                   + (f' (Arabic: "{s.get("arabic", "")}")' if s.get("arabic") else "")
                   + (f' — {s.get("description", "")}' if s.get("description") else "")
                   for i, s in enumerate(steps)
               ) + "\n"
               if steps
               else "FORCES: 3-4 thick arrows alternating push-in and push-out around the center.\n")
            + f"\n"
            f"ARROW STYLING:\n"
            f"  - Arrows pushing IN (toward center): solid, thick, bold — representing external pressures\n"
            f"  - Arrows pushing OUT (away from center): dashed or double-lined — representing resistance/response\n"
            f"  - Arrow thickness varies to show relative force strength\n"
            f"  - Arrowheads are large, hand-drawn, slightly imperfect\n"
            f"\n"
            f"TENSION VISUALIZATION:\n"
            f"  - Zigzag stress marks or lightning-bolt lines where opposing arrows nearly meet\n"
            f"  - Small radiating lines around the central element showing pressure/stress\n"
            f"  - Cross-hatching in the zones of highest tension\n"
            f"\n"
            f"LABELS: Bold hand-lettered labels on each arrow. Arabic text in smaller script beneath.\n"
            f"STYLE: Hand-drawn sketch with visible pen texture, marker-style fills, slight wobble in lines."
        ),
        "spectrum": (
            f"A SPECTRUM / CONTINUUM BAR showing a range from one quality to its opposite:\n"
            f"\n"
            f"MAIN BAR: A long, thick horizontal bar spanning nearly the full card width.\n"
            f"  - Left edge tapers to a point or has a bold end-cap\n"
            f"  - Right edge tapers to a point or has a bold end-cap\n"
            f"  - Bar filled with diagonal hatching that changes density from left to right\n"
            f"    (sparse hatching on left → dense hatching on right, or vice versa)\n"
            f"  - Bar height: roughly 15-20% of illustration zone height\n"
            f"\n"
            + (f'LEFT EXTREME: Labeled "{steps[0].get("label", "").upper()}"'
               + (f' with Arabic "{steps[0].get("arabic", "")}"' if steps[0].get("arabic") else "")
               + f' — {steps[0].get("description", "")}\n'
               f'  Icon/symbol above or below the left end representing this extreme.\n'
               f'RIGHT EXTREME: Labeled "{steps[-1].get("label", "").upper()}"'
               + (f' with Arabic "{steps[-1].get("arabic", "")}"' if steps[-1].get("arabic") else "")
               + f' — {steps[-1].get("description", "")}\n'
               f'  Icon/symbol above or below the right end representing this extreme.\n'
               if len(steps) >= 2
               else "LEFT EXTREME: labeled with one quality. RIGHT EXTREME: labeled with its opposite.\n")
            + (f"\nMIDPOINT MARKERS ({num_steps - 2} intermediate positions):\n"
               + "\n".join(
                   f'  Position {i}: "{s.get("label", "").upper()}"'
                   + (f' (Arabic: "{s.get("arabic", "")}")' if s.get("arabic") else "")
                   + f' — marked with a downward arrow/pointer on the bar'
                   + (f', icon: {s.get("description", "")}' if s.get("description") else "")
                   for i, s in enumerate(steps[1:-1], 2)
               ) + "\n"
               if len(steps) > 2 else "")
            + f"\nIDEAL ZONE: One segment of the bar highlighted with accent color wash,\n"
            f"  showing the recommended/healthy/Quranic ideal position. Small star or check icon above it.\n"
            f"\n"
            f"LABELS:\n"
            f"  - Bold hand-lettered labels ABOVE the bar for each extreme and marker\n"
            f"  - Thin vertical tick marks on the bar at each labeled position\n"
            f"  - Small arrow/pointer from each label down to its tick mark\n"
            f"  - Arabic text in smaller script directly beneath English labels\n"
            f"\n"
            f"STYLE: Hand-drawn bar with visible pen wobble. Hatching density creates visual gradient\n"
            f"WITHOUT using color gradients. End-caps are hand-drawn with slight imperfection.\n"
            f"Tick marks are short vertical lines crossing the bar edge."
        ),
        "nested_circles": (
            f"3-4 concentric circles, outermost largest, innermost smallest.\n"
            + ("\n".join(
                f'  Ring {i+1}: "{s.get("label", "").upper()}"'
                + (f' — {s.get("description", "")}' if s.get("description") else "")
                for i, s in enumerate(steps)
            ) if steps else f"  Each ring labeled: {steps_desc or 'Outer, Middle, Inner, Core'}.")
            + f"\nInnermost circle highlighted in warm accent (most important/fundamental). "
            f"Hand-drawn with slightly imperfect circles."
        ),
    }

    return prompts.get(visual_type, (
        f"Conceptual hand-drawn illustration representing '{title}'. "
        f"Simple doodle-style diagram with labeled elements and hand-drawn arrows. "
        f"Clean, minimal design with thick black outlines."
    ))


def format_models_for_llm_context(top_matches, max_models=5):
    """Format top matching models as context string for the LLM analysis prompt.

    Returns a string to inject into the ANALYSIS_PROMPT.
    """
    if not top_matches:
        return "No pre-matched models available. Analyze freely."

    lines = ["TOP MATCHING MENTAL MODELS FROM REPOSITORY:"]
    for i, match in enumerate(top_matches[:max_models], 1):
        quranic_tag = " [QURANIC]" if match.get("is_quranic") else ""
        cross_domain_tag = " [STRUCTURAL TEMPLATE — adapt structure, not content]" if match.get("cross_domain_template") else ""
        keywords_str = ", ".join(match.get("keywords", [])[:8])
        alt_visuals = ", ".join(match.get("visual_types_alt", []))
        related = ", ".join(match.get("related_models", []))
        entry = (
            f"  {i}. {match['name']}{quranic_tag}{cross_domain_tag} (ID: {match['id']}) — {match['category']}\n"
            f"     Visual: {match['visual_type']}"
        )
        if alt_visuals:
            entry += f" | Alt visuals: {alt_visuals}"
        entry += f" | Confidence: {match['confidence']:.0%}\n"
        entry += f"     Description: {match['description']}\n"
        entry += f"     Key elements: {', '.join(match.get('key_elements', []))}"
        when_to_use = match.get("when_to_use", "")
        if when_to_use:
            entry += f"\n     When to use: {when_to_use}"
        if keywords_str:
            entry += f"\n     Keywords: {keywords_str}"
        if related:
            entry += f"\n     Related models: {related}"
        if cross_domain_tag:
            entry += ("\n     ADAPTATION NOTE: This model is from a different domain but shares "
                      "the same STRUCTURAL pattern as the input content. Use its visual structure "
                      "and layout as a template — replace its content with the Quranic content.")
        lines.append(entry)

    lines.append(
        "\nSTRONGLY PREFER selecting one of these pre-matched models. They were scored "
        "against 100+ curated models using keyword, visual pattern, and category analysis. "
        "Only use model_id='custom' as an absolute last resort when EVERY listed model "
        "is fundamentally incompatible with the content."
    )
    return "\n".join(lines)
