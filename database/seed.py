"""
Amahirwe demo data seed script.

Populates fictional demo accounts and data so the platform can be
demonstrated end to end. Safe to re-run: it skips anything that already
exists (matched by email/name) rather than creating duplicates.

Covers auth, student/assessment, teacher, mentor matching, opportunities
and admin: one school, one student with a completed assessment, a
teacher and mentor at that school, a pending mentor match awaiting the
teacher's review, and one opportunity posted by the provider account.

Run with:

    cd backend && source venv/bin/activate && python ../database/seed.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.audit import Notification  # noqa: E402
from app.models.mentor import MatchStatus, Mentor, MentorExpertise, MentorMatch  # noqa: E402
from app.models.opportunity import Opportunity  # noqa: E402
from app.models.school import School  # noqa: E402
from app.models.student import Student  # noqa: E402
from app.models.talent import AssessmentAnswer, TalentArea, TalentAssessment, TalentResult  # noqa: E402
from app.models.teacher import TeacherProfile  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.services.assessment_bank import QUESTION_BANK  # noqa: E402
from app.services.talent_scoring import score_answers  # noqa: E402

DEMO_PASSWORD = "password123"


def get_or_create_school(db, name, district, province):
    school = db.query(School).filter(School.name == name).first()
    if school is None:
        school = School(name=name, district=district, province=province)
        db.add(school)
        db.flush()
        print(f"  + school: {name}")
    return school


def get_or_create_user(db, full_name, email, role, is_verified=True):
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(DEMO_PASSWORD),
            role=role,
            is_verified=is_verified,
        )
        db.add(user)
        db.flush()
        print(f"  + user: {email} ({role.value})")
    return user


def get_or_create_student(db, user, school, full_name, age_range):
    student = db.query(Student).filter(Student.user_id == user.id).first()
    if student is None:
        student = Student(
            user_id=user.id,
            school_id=school.id,
            full_name=full_name,
            age_range=age_range,
        )
        db.add(student)
        db.flush()
        print(f"  + student profile: {full_name}")
    return student


def seed_demo_assessment(db, student):
    """Give the demo student one completed assessment so the talent
    results screen has something to show. Answers lean toward technology
    and leadership so the demo consistently tells the same story."""
    existing = db.query(TalentAssessment).filter(TalentAssessment.student_id == student.id).first()
    if existing is not None:
        return

    # Alternating a/b answers lean the demo assessment toward whichever
    # talent areas questions 1, 3, 5... and 2, 4, 6... happen to tag "a"
    # and "b" with, which is technology/leadership across this bank.
    answers = []
    talent_areas = []
    for index, question in enumerate(QUESTION_BANK):
        letter = "a" if index % 2 == 0 else "b"
        choice_id = f"{question['id']}{letter}"
        chosen = next(c for c in question["choices"] if c["id"] == choice_id)
        answers.append({"question_id": question["id"], "choice_id": choice_id})
        talent_areas.append(chosen["talent_area"])

    assessment = TalentAssessment(student_id=student.id)
    db.add(assessment)
    db.flush()

    for answer in answers:
        db.add(AssessmentAnswer(assessment_id=assessment.id, question_id=answer["question_id"], choice_id=answer["choice_id"]))

    for entry in score_answers(talent_areas):
        db.add(
            TalentResult(
                assessment_id=assessment.id,
                student_id=student.id,
                talent_area=entry["talent_area"],
                score=entry["score"],
                rank=entry["rank"],
            )
        )
    print(f"  + demo talent assessment for {student.full_name}")


def get_or_create_teacher_profile(db, user, school):
    profile = db.query(TeacherProfile).filter(TeacherProfile.user_id == user.id).first()
    if profile is None:
        profile = TeacherProfile(user_id=user.id, school_id=school.id)
        db.add(profile)
        db.flush()
        print(f"  + teacher profile: {user.full_name} @ {school.name}")
    return profile


def get_or_create_mentor(db, user, district, expertise_areas):
    mentor = db.query(Mentor).filter(Mentor.user_id == user.id).first()
    if mentor is None:
        mentor = Mentor(
            user_id=user.id,
            district=district,
            bio="Software engineer volunteering to guide students interested in technology and leadership.",
        )
        db.add(mentor)
        db.flush()
        for area in expertise_areas:
            db.add(MentorExpertise(mentor_id=mentor.id, talent_area=area))
        print(f"  + mentor profile: {user.full_name} ({', '.join(a.value for a in expertise_areas)})")
    return mentor


def get_or_create_opportunity(db, provider):
    existing = db.query(Opportunity).filter(Opportunity.provider_id == provider.id).first()
    if existing is None:
        existing = Opportunity(
            provider_id=provider.id,
            title="Junior Developer Scholarship",
            description=(
                "A 6-week coding bootcamp scholarship for students who show strong interest "
                "in technology, followed by a paid internship at TechHub Rwanda."
            ),
            talent_area=TalentArea.TECHNOLOGY,
            location="Kigali",
        )
        db.add(existing)
        db.flush()
        print(f"  + opportunity: {existing.title}")
    return existing


def seed_demo_match(db, student, mentor, teacher_profile):
    """A pending mentor match so the teacher dashboard has something to
    review, demonstrating the approve/reject workflow end to end."""

    existing = (
        db.query(MentorMatch)
        .filter(MentorMatch.student_id == student.id, MentorMatch.mentor_id == mentor.id)
        .first()
    )
    if existing is not None:
        return existing

    match = MentorMatch(
        student_id=student.id,
        mentor_id=mentor.id,
        talent_area=TalentArea.TECHNOLOGY,
        status=MatchStatus.PENDING,
    )
    db.add(match)
    db.flush()
    db.add(
        Notification(
            user_id=teacher_profile.user_id,
            message=f"{student.full_name} requested a mentor match (technology). Review it in your dashboard.",
        )
    )
    print(f"  + pending mentor match: {student.full_name} <-> {mentor.user_id}")
    return match


def main():
    db = SessionLocal()
    try:
        print("Seeding demo data...")

        school = get_or_create_school(db, "Nyagatare Secondary School", "Nyagatare", "Eastern Province")

        student_user = get_or_create_user(db, "Aline Uwase", "student@amahirwe.demo", UserRole.STUDENT)
        teacher_user = get_or_create_user(db, "Jean Bosco Habimana", "teacher@amahirwe.demo", UserRole.TEACHER)
        mentor_user = get_or_create_user(db, "Grace Mukamana", "mentor@amahirwe.demo", UserRole.MENTOR)
        provider_user = get_or_create_user(db, "TechHub Rwanda", "provider@amahirwe.demo", UserRole.PROVIDER)
        get_or_create_user(db, "Amahirwe Admin", "admin@amahirwe.demo", UserRole.ADMIN)
        get_or_create_user(db, "Emmanuel Nshuti", "parent@amahirwe.demo", UserRole.PARENT)

        student = get_or_create_student(db, student_user, school, "Aline Uwase", "15-16")
        seed_demo_assessment(db, student)

        teacher_profile = get_or_create_teacher_profile(db, teacher_user, school)
        mentor = get_or_create_mentor(db, mentor_user, school.district, [TalentArea.TECHNOLOGY, TalentArea.LEADERSHIP])
        get_or_create_opportunity(db, provider_user)
        seed_demo_match(db, student, mentor, teacher_profile)

        db.commit()
        print("Done.")
        print(f"\nDemo accounts (password for all: {DEMO_PASSWORD}):")
        print("  student@amahirwe.demo, teacher@amahirwe.demo, mentor@amahirwe.demo,")
        print("  provider@amahirwe.demo, admin@amahirwe.demo, parent@amahirwe.demo")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
