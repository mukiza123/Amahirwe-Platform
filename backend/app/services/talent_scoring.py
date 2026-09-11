"""
Turns a list of assessment answers into ranked talent results (SRS
section 26: a simple talent-discovery prototype, not sophisticated
psychological analysis).

Scoring is just a tally: for each talent area, count how many answers
pointed to it. The areas with the most answers become the student's
results, highest first. Ties are broken by the order talent areas first
appeared in the student's answers, so the result is deterministic.
"""

from collections import Counter

from app.models.talent import TalentArea

EXPLANATIONS = {
    TalentArea.TECHNOLOGY: "You show strong interest in understanding how things work and building or fixing them.",
    TalentArea.LEADERSHIP: "You show strong interest in organizing people and helping a group succeed.",
    TalentArea.CREATIVITY: "You show strong interest in coming up with new ideas, stories or inventions.",
    TalentArea.SPORT: "You show strong interest in physical activity and competing.",
    TalentArea.ART: "You show strong interest in making things that look or sound beautiful.",
    TalentArea.PUBLIC_SPEAKING: "You show strong interest in speaking up and sharing ideas with others.",
    TalentArea.AGRICULTURE: "You show strong interest in growing things and working with nature.",
}


def score_answers(talent_areas: list[TalentArea], max_results: int = 3) -> list[dict]:
    """Given the talent area each answer pointed to, return up to
    max_results ranked results as [{"talent_area", "score", "rank"}, ...].
    """
    if not talent_areas:
        return []

    counts = Counter(talent_areas)

    # Preserve first-appearance order among ties, so the result is stable
    # rather than depending on Counter's arbitrary internal ordering.
    first_seen_order = list(dict.fromkeys(talent_areas))
    ranked_areas = sorted(first_seen_order, key=lambda area: counts[area], reverse=True)

    results = []
    for index, area in enumerate(ranked_areas[:max_results]):
        results.append({"talent_area": area, "score": counts[area], "rank": index + 1})
    return results


def explanation_for(talent_area: TalentArea) -> str:
    return EXPLANATIONS.get(talent_area, "You show strength in this area.")
