import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone, date, timedelta
from sqlalchemy import select
from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
from app.models.user import User
from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.career import CareerRole, RoleSkillRequirement
from app.models.assessment import Assessment, Question
from app.models.roadmap import LearningPath, RoadmapModule, RoadmapResource
from app.models.mentor import Mentor, MentorConnection
from app.models.practice import CodingProblem, CodeSubmission
from app.models.project import ProjectSubmission, ProjectRubric
from app.core.security import get_password_hash

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


async def seed_data():
    print("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Seed Skills
        skills_file = DATA_DIR / "skills.json"
        if skills_file.exists():
            with open(skills_file, "r", encoding="utf-8") as f:
                skills_data = json.load(f)
            for item in skills_data:
                res = await session.execute(select(Skill).where(Skill.name == item["name"]))
                existing = res.scalar_one_or_none()
                if not existing:
                    skill = Skill(name=item["name"], category=item["category"], description=item.get("description", ""))
                    session.add(skill)
            await session.commit()
            print(f"Skills seeded: {len(skills_data)}")

        res = await session.execute(select(Skill))
        all_skills = {s.name: s for s in res.scalars().all()}

        # 2. Seed Career Roles & Requirements
        careers_file = DATA_DIR / "career_roles.json"
        if careers_file.exists():
            with open(careers_file, "r", encoding="utf-8") as f:
                careers_data = json.load(f)
            for role_data in careers_data:
                res = await session.execute(select(CareerRole).where(CareerRole.name == role_data["name"]))
                career_role = res.scalar_one_or_none()
                if not career_role:
                    career_role = CareerRole(
                        name=role_data["name"], description=role_data["description"], is_active=role_data.get("is_active", True)
                    )
                    session.add(career_role)
                    await session.flush()
                for req in role_data.get("requirements", []):
                    skill_obj = all_skills.get(req["skill"])
                    if not skill_obj:
                        continue
                    prereq_obj = all_skills.get(req.get("prerequisite_skill")) if req.get("prerequisite_skill") else None
                    res = await session.execute(
                        select(RoleSkillRequirement).where(
                            RoleSkillRequirement.career_role_id == career_role.id,
                            RoleSkillRequirement.skill_id == skill_obj.id
                        )
                    )
                    existing_req = res.scalar_one_or_none()
                    if not existing_req:
                        requirement = RoleSkillRequirement(
                            career_role_id=career_role.id, skill_id=skill_obj.id,
                            required_level=req["required_level"], weight=req.get("weight", 1),
                            is_prerequisite_for=req.get("is_prerequisite_for"),
                            prerequisite_skill_id=prereq_obj.id if prereq_obj else None
                        )
                        session.add(requirement)
            await session.commit()
            print("Career roles and requirements seeded.")

        # 3. Seed Assessments and Questions
        assessments_file = DATA_DIR / "assessment_questions.json"
        if assessments_file.exists():
            with open(assessments_file, "r", encoding="utf-8") as f:
                assessments_data = json.load(f)
            for a_data in assessments_data:
                skill_obj = all_skills.get(a_data["skill"])
                if not skill_obj:
                    continue
                res = await session.execute(
                    select(Assessment).where(Assessment.skill_id == skill_obj.id, Assessment.title == a_data["assessment_title"])
                )
                assessment = res.scalar_one_or_none()
                questions_list = a_data.get("questions", [])
                if not assessment:
                    assessment = Assessment(
                        title=a_data["assessment_title"], skill_id=skill_obj.id,
                        assessment_type=a_data.get("assessment_type", "diagnostic"),
                        total_questions=len(questions_list)
                    )
                    session.add(assessment)
                    await session.flush()
                else:
                    assessment.total_questions = len(questions_list)
                for q in questions_list:
                    res = await session.execute(
                        select(Question).where(Question.assessment_id == assessment.id, Question.question_text == q["question_text"])
                    )
                    existing_q = res.scalar_one_or_none()
                    if not existing_q:
                        new_q = Question(
                            assessment_id=assessment.id, skill_id=skill_obj.id,
                            subtopic=q["subtopic"], question_text=q["question_text"],
                            options=q["options"], correct_option=q["correct_option"],
                            explanation=q["explanation"], difficulty=q.get("difficulty", "medium"),
                            marks=q.get("marks", 1)
                        )
                        session.add(new_q)
            await session.commit()
            print("Assessments and questions seeded.")

        # 4. Seed Coding Problems
        problems_file = DATA_DIR / "coding_problems.json"
        if problems_file.exists():
            with open(problems_file, "r", encoding="utf-8") as f:
                problems_data = json.load(f)
            for p in problems_data:
                skill_obj = all_skills.get(p["skill"])
                if not skill_obj:
                    continue
                res = await session.execute(select(CodingProblem).where(CodingProblem.title == p["title"]))
                if not res.scalar_one_or_none():
                    problem = CodingProblem(
                        title=p["title"], description=p["description"], language=p["language"],
                        skill_id=skill_obj.id, subtopic=p["subtopic"], difficulty=p["difficulty"],
                        starter_code=p["starter_code"], function_name=p["function_name"],
                        test_cases=p["test_cases"], examples=p.get("examples", []),
                        constraints=p.get("constraints"), is_active=True
                    )
                    session.add(problem)
            await session.commit()
            print(f"Coding problems seeded: {len(problems_data)}")

        # 5. Seed Project Rubrics
        rubrics_file = DATA_DIR / "project_rubrics.json"
        if rubrics_file.exists():
            with open(rubrics_file, "r", encoding="utf-8") as f:
                rubrics_data = json.load(f)
            for r in rubrics_data:
                res = await session.execute(select(ProjectRubric).where(ProjectRubric.project_type == r["project_type"]))
                if not res.scalar_one_or_none():
                    rubric = ProjectRubric(
                        project_type=r["project_type"], criteria=r["criteria"],
                        total_weight=r["total_weight"]
                    )
                    session.add(rubric)
            await session.commit()
            print(f"Project rubrics seeded: {len(rubrics_data)}")

        # 6. Seed Demo Users (Admin, Mentors, Students)
        await seed_demo_users(session, all_skills)

        # 7. Seed Section 3 data (campuses, college courses, notifications, etc.)
        await seed_section3_data(session, all_skills)

    print("Database seeding completed.")


async def seed_demo_users(session, all_skills):
    """Create demo admin, mentors, and students with realistic data."""
    # Check if already seeded
    res = await session.execute(select(User).where(User.email == "admin@skillpilot.ai"))
    if res.scalar_one_or_none():
        print("Demo users already exist, skipping.")
        return

    # Admin
    admin_user = User(
        email="admin@skillpilot.ai", username="admin", hashed_password=get_password_hash("admin123"), role="admin", is_active=True
    )
    session.add(admin_user)
    await session.flush()

    # Mentors
    mentor_data = [
        {"email": "sarah.mentor@skillpilot.ai", "username": "sarah_mentor", "full_name": "Sarah Chen", "expertise": "Full Stack Development, React, Node.js"},
        {"email": "mike.mentor@skillpilot.ai", "username": "mike_mentor", "full_name": "Mike Johnson", "expertise": "Python, Data Analysis, Machine Learning"},
        {"email": "priya.mentor@skillpilot.ai", "username": "priya_mentor", "full_name": "Priya Sharma", "expertise": "SQL, Database Design, Backend Architecture"},
    ]
    for m in mentor_data:
        m_user = User(
            email=m["email"], username=m["username"], hashed_password=get_password_hash("mentor123"),
            role="mentor", is_active=True
        )
        session.add(m_user)
        await session.flush()

        # Generate unique mentor code
        import random, string
        code_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        code = "PF-MENTOR-" + "".join(random.choices(code_chars, k=8))
        mentor = Mentor(
            user_id=m_user.id, full_name=m["full_name"], expertise=m["expertise"],
            mentor_code=code, is_active=True
        )
        session.add(mentor)
    await session.flush()
    print("Mentors seeded.")

    # Demo students
    # Get career roles
    res = await session.execute(select(CareerRole).where(CareerRole.name == "Full Stack Developer"))
    fs_role = res.scalar_one_or_none()
    res = await session.execute(select(CareerRole).where(CareerRole.name == "Data Analyst"))
    da_role = res.scalar_one_or_none()

    students_data = [
        {
            "email": "alex.student@skillpilot.ai", "username": "alex_student", "full_name": "Alex Rivera",
            "password": "student123",
            "skills": [("JavaScript", 1), ("Python", 3), ("SQL", 2), ("HTML", 2)],
            "target_role_id": fs_role.id if fs_role else None,
            "weekly_hours": 10,
        },
        {
            "email": "jamie.student@skillpilot.ai", "username": "jamie_student", "full_name": "Jamie Taylor",
            "password": "student123",
            "skills": [("Python", 4), ("SQL", 3), ("Statistics", 2)],
            "target_role_id": da_role.id if da_role else None,
            "weekly_hours": 8,
        },
        {
            "email": "carol.student@skillpilot.ai", "username": "carol_student", "full_name": "Carol Nguyen",
            "password": "student123",
            "skills": [("JavaScript", 3), ("React", 2), ("HTML", 3), ("CSS", 3)],
            "target_role_id": fs_role.id if fs_role else None,
            "weekly_hours": 12,
        },
        {
            "email": "dave.student@skillpilot.ai", "username": "dave_student", "full_name": "Dave Wilson",
            "password": "student123",
            "skills": [("Python", 2), ("SQL", 1), ("Git", 1)],
            "target_role_id": da_role.id if da_role else None,
            "weekly_hours": 6,
        },
        {
            "email": "emma.student@skillpilot.ai", "username": "emma_student", "full_name": "Emma Brown",
            "password": "student123",
            "skills": [("JavaScript", 4), ("React", 3), ("Node.js", 2), ("SQL", 2), ("Git", 3)],
            "target_role_id": fs_role.id if fs_role else None,
            "weekly_hours": 15,
        },
    ]

    for s in students_data:
        s_user = User(
            email=s["email"], username=s["username"], hashed_password=get_password_hash(s["password"]),
            role="student", is_active=True
        )
        session.add(s_user)
        await session.flush()

        profile = StudentProfile(
            user_id=s_user.id, full_name=s["full_name"], weekly_study_hours=s["weekly_hours"],
            target_role_id=s["target_role_id"], projects=[], certifications=[]
        )
        session.add(profile)
        await session.flush()

        # Add skills
        for skill_name, level in s["skills"]:
            skill_obj = all_skills.get(skill_name)
            if skill_obj:
                mastery = (float(level) / 5.0) * 100.0
                ls = LearnerSkill(
                    student_profile_id=profile.id, skill_id=skill_obj.id,
                    self_reported_level=level, verified_level=float(level),
                    evidence_type="self_report", mastery_percentage=mastery
                )
                session.add(ls)

        # Connect first student to first mentor
        if s["username"] == "alex_student":
            mentor_res = await session.execute(select(Mentor).limit(1))
            first_mentor = mentor_res.scalar_one_or_none()
            if first_mentor:
                conn = MentorConnection(
                    student_profile_id=profile.id, mentor_id=first_mentor.id,
                    mentor_code=first_mentor.mentor_code, status="connected",
                    connected_at=datetime.now(timezone.utc)
                )
                session.add(conn)

    await session.flush()

    # Seed sample project submissions
    proj_res = await session.execute(select(StudentProfile).where(StudentProfile.full_name == "Alex Rivera"))
    alex_profile = proj_res.scalar_one_or_none()
    if alex_profile:
        sample_proj = ProjectSubmission(
            student_profile_id=alex_profile.id,
            title="Personal Portfolio Website",
            project_type="frontend",
            description="A responsive portfolio website built with React, TypeScript, and Tailwind CSS. Features include project showcase, contact form, and dark mode toggle.",
            github_url="https://github.com/example/portfolio",
            live_url="https://example-portfolio.netlify.app",
            status="evaluated",
            evaluation_score=78.0,
            evaluation_report={
                "project_title": "Personal Portfolio Website",
                "overall_score": 78.0,
                "verdict": "good",
                "verified_skills": [{"skill": "JavaScript", "evidence": "React hooks and component patterns used", "confidence": "high"}],
                "strengths": ["Clean component structure", "Good use of Tailwind CSS", "Responsive design"],
                "weaknesses": [{"area": "Testing", "issue": "No tests found", "severity": "medium", "improvement": "Add component tests with Jest/RTL"}],
                "limitations": ["Could not access repository to verify code quality directly"],
                "rubric_scores": [
                    {"criterion": "Functionality", "score": 20, "max_score": 25, "feedback": "Core features working well"},
                    {"criterion": "Correct skill usage", "score": 16, "max_score": 20, "feedback": "Good React patterns"},
                    {"criterion": "Code quality", "score": 12, "max_score": 15, "feedback": "Well organized"},
                    {"criterion": "Security", "score": 10, "max_score": 15, "feedback": "Form inputs could be sanitized"},
                    {"criterion": "UI/UX", "score": 8, "max_score": 10, "feedback": "Clean and responsive"},
                    {"criterion": "Documentation", "score": 7, "max_score": 10, "feedback": "Basic README present"},
                    {"criterion": "Testing", "score": 0, "max_score": 5, "feedback": "No tests"},
                ],
                "security_flags": [],
                "portfolio_readiness": "almost_ready",
                "next_improvements": ["Add unit tests", "Improve README documentation", "Add CI/CD pipeline"],
                "roadmap_impact": [{"skill": "JavaScript", "action": "verify", "reason": "Strong evidence of React usage"}],
                "mentor_review_required": True,
            },
            submitted_at=datetime.now(timezone.utc),
            evaluated_at=datetime.now(timezone.utc),
        )
        session.add(sample_proj)

    await session.commit()
    print("Demo students and sample data seeded.")


async def seed_section3_data(session, all_skills: dict):
    """Seed Section 3 data: campuses, courses, assignments, notifications, recommendations, portfolio."""
    from app.models.portfolio import Campus, PortfolioProfile, LeaderboardEntry
    from app.models.college import (
        CollegeCourse, StudentCourseEnrollment, CourseSchedule,
        CollegeAssignment, CollegeAnnouncement, AcademicRecord, AcademicRiskAlert,
    )
    from app.models.notification import Notification, AIRecommendation

    # Check if already seeded
    res = await session.execute(select(Campus).where(Campus.code == "PVIT"))
    if res.scalar_one_or_none():
        print("Section 3 seed data already exists, skipping.")
        return

    # ----- Campuses -----
    campus1 = Campus(name="Skill Pilot Valley Institute of Technology", code="PVIT")
    campus2 = Campus(name="Summit State College of Engineering", code="SSCE")
    session.add_all([campus1, campus2])
    await session.flush()

    # ----- College courses -----
    js_skill = all_skills.get("JavaScript")
    py_skill = all_skills.get("Python")
    sql_skill = all_skills.get("SQL")
    html_skill = all_skills.get("HTML")

    courses = [
        CollegeCourse(campus_id=campus1.id, course_code="CS301", course_name="Web Technologies",
                      semester="2024-25 Sem 1",
                      syllabus=[{"unit": 1, "topic": "HTML & CSS"}, {"unit": 2, "topic": "JavaScript"},
                                {"unit": 3, "topic": "React"}]),
        CollegeCourse(campus_id=campus1.id, course_code="CS302", course_name="Database Management Systems",
                      semester="2024-25 Sem 1",
                      syllabus=[{"unit": 1, "topic": "Relational Model"}, {"unit": 2, "topic": "SQL Queries"},
                                {"unit": 3, "topic": "Normalization"}]),
        CollegeCourse(campus_id=campus1.id, course_code="CS303", course_name="Python Programming",
                      semester="2024-25 Sem 1",
                      syllabus=[{"unit": 1, "topic": "Python Basics"}, {"unit": 2, "topic": "OOP in Python"},
                                {"unit": 3, "topic": "File Handling"}]),
        CollegeCourse(campus_id=campus2.id, course_code="IT401", course_name="Software Engineering",
                      semester="2024-25 Sem 2",
                      syllabus=[{"unit": 1, "topic": "SDLC"}, {"unit": 2, "topic": "Agile"},
                                {"unit": 3, "topic": "Testing"}]),
        CollegeCourse(campus_id=campus2.id, course_code="DS501", course_name="Data Analysis & Visualization",
                      semester="2024-25 Sem 1",
                      syllabus=[{"unit": 1, "topic": "Pandas & NumPy"}, {"unit": 2, "topic": "Matplotlib"},
                                {"unit": 3, "topic": "Statistics"}]),
        CollegeCourse(campus_id=campus1.id, course_code="CS304", course_name="Computer Networks",
                      semester="2024-25 Sem 2",
                      syllabus=[{"unit": 1, "topic": "OSI Model"}, {"unit": 2, "topic": "TCP/IP"},
                                {"unit": 3, "topic": "HTTP & REST"}]),
    ]
    session.add_all(courses)
    await session.flush()

    # ----- Course schedules -----
    schedules = [
        CourseSchedule(college_course_id=courses[0].id, week_number=1, title="HTML Fundamentals",
                       topics=["HTML tags", "Semantic HTML", "Forms"],
                       learning_objectives=["Build a basic webpage", "Use semantic elements"],
                       related_skill_ids=[html_skill.id] if html_skill else []),
        CourseSchedule(college_course_id=courses[0].id, week_number=2, title="CSS & Responsive Design",
                       topics=["CSS selectors", "Flexbox", "Media queries"],
                       learning_objectives=["Style a webpage", "Make it responsive"],
                       related_skill_ids=[]),
        CourseSchedule(college_course_id=courses[0].id, week_number=3, title="JavaScript Basics",
                       topics=["Variables", "Functions", "DOM Manipulation"],
                       learning_objectives=["Write basic JS", "Manipulate the DOM"],
                       related_skill_ids=[js_skill.id] if js_skill else [],
                       lecture_recording_url="https://www.youtube.com/watch?v=W6NZfCO5SIk"),
        CourseSchedule(college_course_id=courses[1].id, week_number=1, title="Relational Databases",
                       topics=["Tables", "Primary keys", "Foreign keys"],
                       learning_objectives=["Design a schema", "Create tables"],
                       related_skill_ids=[sql_skill.id] if sql_skill else []),
        CourseSchedule(college_course_id=courses[2].id, week_number=1, title="Python Introduction",
                       topics=["Syntax", "Data types", "Control flow"],
                       learning_objectives=["Write Python scripts", "Use conditionals and loops"],
                       related_skill_ids=[py_skill.id] if py_skill else [],
                       lecture_recording_url="https://www.youtube.com/watch?v=_uQrJ0TkZlc"),
    ]
    session.add_all(schedules)

    # ----- Assignments -----
    due1 = datetime.now(timezone.utc) + timedelta(days=7)
    due2 = datetime.now(timezone.utc) + timedelta(days=14)
    due3 = datetime.now(timezone.utc) + timedelta(days=3)
    assignments = [
        CollegeAssignment(college_course_id=courses[0].id, title="Build a Portfolio Webpage",
                          description="Create a responsive HTML/CSS portfolio page with at least 3 sections.",
                          due_date=due1, max_marks=100,
                          related_skill_ids=[html_skill.id] if html_skill else []),
        CollegeAssignment(college_course_id=courses[0].id, title="JavaScript Form Validation",
                          description="Add client-side validation to a form using JavaScript.",
                          due_date=due2, max_marks=50,
                          related_skill_ids=[js_skill.id] if js_skill else []),
        CollegeAssignment(college_course_id=courses[1].id, title="SQL Query Assignment",
                          description="Write 10 SQL queries on the provided university database.",
                          due_date=due3, max_marks=100,
                          related_skill_ids=[sql_skill.id] if sql_skill else []),
        CollegeAssignment(college_course_id=courses[2].id, title="Python Data Structures Lab",
                          description="Implement stack, queue, and linked list in Python.",
                          due_date=due1, max_marks=100,
                          related_skill_ids=[py_skill.id] if py_skill else []),
        CollegeAssignment(college_course_id=courses[4].id, title="Data Analysis Mini Project",
                          description="Analyse a CSV dataset using Pandas and create 3 visualizations.",
                          due_date=due2, max_marks=100,
                          related_skill_ids=[py_skill.id] if py_skill else []),
    ]
    session.add_all(assignments)

    # ----- Announcements -----
    announcements = [
        CollegeAnnouncement(campus_id=campus1.id, title="Mid-semester Exams Schedule Released",
                            message="Mid-semester exams are scheduled for weeks 8-9. Check the portal for details.",
                            audience="all"),
        CollegeAnnouncement(campus_id=campus1.id, title="Assignment Submission Deadline Reminder",
                            message="All pending assignments must be submitted before end of this week.",
                            audience="all"),
        CollegeAnnouncement(campus_id=campus1.id, title="Industry Expert Talk: Full Stack Development",
                            message="Join us for a talk by a senior engineer from Google on modern web development. Friday, 3 PM.",
                            audience="department", related_course_id=courses[0].id),
        CollegeAnnouncement(campus_id=campus2.id, title="Data Science Workshop",
                            message="Register for the Data Science with Python workshop this Saturday.",
                            audience="all"),
    ]
    session.add_all(announcements)
    await session.flush()

    # ----- Enroll demo students -----
    res = await session.execute(select(StudentProfile).where(StudentProfile.full_name == "Alex Rivera"))
    alex = res.scalar_one_or_none()
    res = await session.execute(select(StudentProfile).where(StudentProfile.full_name == "Jamie Taylor"))
    jamie = res.scalar_one_or_none()

    if alex:
        for c in courses[:3]:
            session.add(StudentCourseEnrollment(
                student_profile_id=alex.id, college_course_id=c.id,
                enrolled_at=datetime.now(timezone.utc), status="active",
            ))
        # Academic records for alex
        session.add(AcademicRecord(
            student_profile_id=alex.id, college_course_id=courses[0].id,
            attendance_percentage=72.0, internal_marks=38.0,
            assignment_completion_percentage=60.0, academic_status="at_risk",
            updated_at=datetime.now(timezone.utc),
        ))
        session.add(AcademicRiskAlert(
            student_profile_id=alex.id, college_course_id=courses[0].id,
            risk_type="low_attendance", risk_level="warning",
            message="Attendance 72% — below 75% threshold.",
            recommended_action="Attend all remaining classes and contact your mentor.",
        ))

    if jamie:
        for c in [courses[1], courses[4]]:
            session.add(StudentCourseEnrollment(
                student_profile_id=jamie.id, college_course_id=c.id,
                enrolled_at=datetime.now(timezone.utc), status="active",
            ))

    # ----- Notifications for demo users -----
    res = await session.execute(select(User).where(User.email == "alex.student@skillpilot.ai"))
    alex_user = res.scalar_one_or_none()
    if alex_user:
        notifs = [
            Notification(user_id=alex_user.id, title="Roadmap Created",
                         message="Your Full Stack Developer roadmap is ready!", notification_type="roadmap"),
            Notification(user_id=alex_user.id, title="Academic Risk Alert",
                         message="Attendance in Web Technologies is below 75%.",
                         notification_type="college", reference_path="/college-connect"),
            Notification(user_id=alex_user.id, title="Assignment Due Soon",
                         message="Build a Portfolio Webpage is due in 7 days.",
                         notification_type="college"),
            Notification(user_id=alex_user.id, title="Project Evaluated",
                         message="Your Personal Portfolio project scored 78/100.",
                         notification_type="project", reference_path="/projects"),
        ]
        session.add_all(notifs)

    # ----- AI Recommendations for demo users -----
    if alex:
        recs = [
            AIRecommendation(
                student_profile_id=alex.id, recommendation_type="revision",
                title="Revise JavaScript Fundamentals",
                description="Your JavaScript mastery is at 20%. Complete 3 practice problems on closures and async/await.",
                reason="JavaScript mastery below 50% — React module is locked until you reach 70%.",
                evidence=[{"type": "assessment", "summary": "JavaScript mastery: 20%"}],
                priority="critical", action_path="/practice", estimated_minutes=60,
            ),
            AIRecommendation(
                student_profile_id=alex.id, recommendation_type="project",
                title="Build a REST API with Node.js",
                description="Create a simple CRUD REST API using Node.js, Express, and SQLite.",
                reason="Your backend skills need a verified project for Full Stack Developer readiness.",
                evidence=[{"type": "roadmap", "summary": "Node.js module in progress"}],
                priority="high", action_path="/projects", estimated_minutes=180,
            ),
            AIRecommendation(
                student_profile_id=alex.id, recommendation_type="interview",
                title="Practice Technical Interview",
                description="Complete a Full Stack Developer mock interview to identify weak technical areas.",
                reason="Interview readiness increases overall career readiness score.",
                evidence=[{"type": "coding", "summary": "No interview sessions completed yet"}],
                priority="medium", action_path="/career-intelligence", estimated_minutes=30,
            ),
        ]
        session.add_all(recs)

    # ----- Leaderboard entries -----
    if alex:
        session.add(LeaderboardEntry(
            student_profile_id=alex.id, campus_id=campus1.id,
            period_type="all_time", practice_points=12.0, assessment_points=10.0,
            project_points=10.0, consistency_points=5.0, total_points=37.0, rank=1,
            updated_at=datetime.now(timezone.utc),
        ))
    if jamie:
        session.add(LeaderboardEntry(
            student_profile_id=jamie.id, campus_id=campus1.id,
            period_type="all_time", practice_points=8.0, assessment_points=14.0,
            project_points=0.0, consistency_points=3.0, total_points=25.0, rank=2,
            updated_at=datetime.now(timezone.utc),
        ))

    # ----- Portfolio profiles -----
    if alex:
        session.add(PortfolioProfile(
            student_profile_id=alex.id,
            github_url="https://github.com/alex-example",
            problems_solved=12, current_streak=3, longest_streak=7,
            portfolio_score=37.0, show_in_leaderboard=True,
            last_activity_date=date.today(),
            updated_at=datetime.now(timezone.utc),
        ))

    await session.commit()
    print("Section 3 seed data created.")


if __name__ == "__main__":
    asyncio.run(seed_data())
