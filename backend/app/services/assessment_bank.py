"""
The talent-discovery assessment content (SRS FR-1.1).

Fixed, hardcoded question bank rather than a database table: the
questions don't need to be admin-editable for this prototype, and keeping
them here means the assessment can be served and scored without any
extra tables or an admin content-management screen.

Each choice is tagged with the talent area it points to. Scoring simply
counts, per talent area, how many of a student's answers pointed to it,
transparent and easy to explain in the presentation, matching the
"simple, not a sophisticated psychological analysis" approach the SRS
asks for (section 26 of the design brief).
"""

from __future__ import annotations

from app.models.talent import TalentArea

QUESTION_BANK = [
    {
        "id": "q1",
        "text": "What do you enjoy doing most in your free time?",
        "choices": [
            {"id": "q1a", "text": "Building or fixing things", "talent_area": TalentArea.TECHNOLOGY},
            {"id": "q1b", "text": "Organizing an activity with friends", "talent_area": TalentArea.LEADERSHIP},
            {"id": "q1c", "text": "Making up stories, songs or drawings", "talent_area": TalentArea.CREATIVITY},
            {"id": "q1d", "text": "Playing a sport", "talent_area": TalentArea.SPORT},
        ],
    },
    {
        "id": "q2",
        "text": "Which of these would you rather spend an afternoon doing?",
        "choices": [
            {"id": "q2a", "text": "Painting, drawing or making something beautiful", "talent_area": TalentArea.ART},
            {"id": "q2b", "text": "Talking to a group about an idea you have", "talent_area": TalentArea.PUBLIC_SPEAKING},
            {"id": "q2c", "text": "Growing plants or caring for animals", "talent_area": TalentArea.AGRICULTURE},
            {"id": "q2d", "text": "Exploring how a phone or computer works", "talent_area": TalentArea.TECHNOLOGY},
        ],
    },
    {
        "id": "q3",
        "text": "When your class works on a group project, what do you usually do?",
        "choices": [
            {"id": "q3a", "text": "Help plan and organize the group", "talent_area": TalentArea.LEADERSHIP},
            {"id": "q3b", "text": "Come up with creative ideas", "talent_area": TalentArea.CREATIVITY},
            {"id": "q3c", "text": "Keep everyone energized and moving", "talent_area": TalentArea.SPORT},
            {"id": "q3d", "text": "Design how the final project looks", "talent_area": TalentArea.ART},
        ],
    },
    {
        "id": "q4",
        "text": "If your school had an open day, what would you want to do?",
        "choices": [
            {"id": "q4a", "text": "Welcome visitors and explain things", "talent_area": TalentArea.PUBLIC_SPEAKING},
            {"id": "q4b", "text": "Show a small garden project", "talent_area": TalentArea.AGRICULTURE},
            {"id": "q4c", "text": "Demonstrate something you built", "talent_area": TalentArea.TECHNOLOGY},
            {"id": "q4d", "text": "Help organize the whole day", "talent_area": TalentArea.LEADERSHIP},
        ],
    },
    {
        "id": "q5",
        "text": "What kind of achievement would make you proudest?",
        "choices": [
            {"id": "q5a", "text": "Finishing a story, song or piece of art", "talent_area": TalentArea.CREATIVITY},
            {"id": "q5b", "text": "Winning a sports competition", "talent_area": TalentArea.SPORT},
            {"id": "q5c", "text": "Creating something people find beautiful", "talent_area": TalentArea.ART},
            {"id": "q5d", "text": "Giving a speech people remember", "talent_area": TalentArea.PUBLIC_SPEAKING},
        ],
    },
    {
        "id": "q6",
        "text": "Which of these sounds most like you?",
        "choices": [
            {"id": "q6a", "text": "I like growing things and working with nature", "talent_area": TalentArea.AGRICULTURE},
            {"id": "q6b", "text": "I like understanding how things work", "talent_area": TalentArea.TECHNOLOGY},
            {"id": "q6c", "text": "I like helping a group get organized", "talent_area": TalentArea.LEADERSHIP},
            {"id": "q6d", "text": "I like inventing new ideas or stories", "talent_area": TalentArea.CREATIVITY},
        ],
    },
    {
        "id": "q7",
        "text": "In a football match or sports day, what do you enjoy most?",
        "choices": [
            {"id": "q7a", "text": "Playing and competing", "talent_area": TalentArea.SPORT},
            {"id": "q7b", "text": "Designing the team's colours or banner", "talent_area": TalentArea.ART},
            {"id": "q7c", "text": "Cheering and getting others excited", "talent_area": TalentArea.PUBLIC_SPEAKING},
            {"id": "q7d", "text": "Helping prepare the field or snacks", "talent_area": TalentArea.AGRICULTURE},
        ],
    },
    {
        "id": "q8",
        "text": "Your friends usually come to you when they need...",
        "choices": [
            {"id": "q8a", "text": "Someone to fix or build something", "talent_area": TalentArea.TECHNOLOGY},
            {"id": "q8b", "text": "Someone to lead the plan", "talent_area": TalentArea.LEADERSHIP},
            {"id": "q8c", "text": "Someone with a creative idea", "talent_area": TalentArea.CREATIVITY},
            {"id": "q8d", "text": "Someone to get them moving and active", "talent_area": TalentArea.SPORT},
        ],
    },
    {
        "id": "q9",
        "text": "Which school subject do you enjoy the most?",
        "choices": [
            {"id": "q9a", "text": "Art or music", "talent_area": TalentArea.ART},
            {"id": "q9b", "text": "Debate or public speaking", "talent_area": TalentArea.PUBLIC_SPEAKING},
            {"id": "q9c", "text": "Agriculture or environmental studies", "talent_area": TalentArea.AGRICULTURE},
            {"id": "q9d", "text": "Science or computer studies", "talent_area": TalentArea.TECHNOLOGY},
        ],
    },
    {
        "id": "q10",
        "text": "If you had to present something in front of your class, what would you show?",
        "choices": [
            {"id": "q10a", "text": "A plan you organized", "talent_area": TalentArea.LEADERSHIP},
            {"id": "q10b", "text": "A story or idea you made up", "talent_area": TalentArea.CREATIVITY},
            {"id": "q10c", "text": "A sport or physical skill", "talent_area": TalentArea.SPORT},
            {"id": "q10d", "text": "A drawing or design", "talent_area": TalentArea.ART},
        ],
    },
    {
        "id": "q11",
        "text": "What would you rather learn more about?",
        "choices": [
            {"id": "q11a", "text": "How to speak confidently in public", "talent_area": TalentArea.PUBLIC_SPEAKING},
            {"id": "q11b", "text": "How to grow crops or raise animals", "talent_area": TalentArea.AGRICULTURE},
            {"id": "q11c", "text": "How computers and technology work", "talent_area": TalentArea.TECHNOLOGY},
            {"id": "q11d", "text": "How to lead and organize people", "talent_area": TalentArea.LEADERSHIP},
        ],
    },
    {
        "id": "q12",
        "text": "What do you enjoy doing most?",
        "choices": [
            {"id": "q12a", "text": "Creating things with your imagination", "talent_area": TalentArea.CREATIVITY},
            {"id": "q12b", "text": "Playing sports", "talent_area": TalentArea.SPORT},
            {"id": "q12c", "text": "Making art", "talent_area": TalentArea.ART},
            {"id": "q12d", "text": "Talking and sharing ideas with others", "talent_area": TalentArea.PUBLIC_SPEAKING},
        ],
    },
]

# Fast lookup: question_id -> {choice_id: TalentArea}
_QUESTION_INDEX = {q["id"]: {c["id"]: c["talent_area"] for c in q["choices"]} for q in QUESTION_BANK}

VALID_QUESTION_IDS = set(_QUESTION_INDEX.keys())


def talent_area_for_choice(question_id: str, choice_id: str) -> TalentArea | None:
    """Look up which talent area a given answer points to, or None if the
    question_id/choice_id pair doesn't exist in the question bank."""
    choices = _QUESTION_INDEX.get(question_id)
    if choices is None:
        return None
    return choices.get(choice_id)
