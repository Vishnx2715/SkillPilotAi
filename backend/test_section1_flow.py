import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


async def test_end_to_end_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        print("\n--- 1. Testing Registration ---")
        reg_payload = {
            "email": "learner_test@skillpilot.ai",
            "username": "learner_test",
            "password": "Password123!",
            "confirm_password": "Password123!"
        }
        res = await client.post("/api/v1/auth/register", json=reg_payload)
        if res.status_code == 400 and "already registered" in res.text:
            print("User already registered, logging in...")
            login_payload = {
                "username_or_email": "learner_test",
                "password": "Password123!"
            }
            res = await client.post("/api/v1/auth/login", json=login_payload)
        
        assert res.status_code in [200, 201], f"Auth failed: {res.status_code} {res.text}"
        print(f"Auth Success: User logged in, cookies received: {list(client.cookies.keys())}")

        print("\n--- 2. Testing Onboarding (Python 3, SQL 2, HTML 2) ---")
        onboarding_payload = {
            "full_name": "Alex Acceptance Tester",
            "education_level": "Bachelor's Degree",
            "experience_level": "Beginner",
            "weekly_study_hours": 12,
            "learning_preference": "Hands-on projects",
            "skills": [
                {"skill_name": "Python", "level": 3},
                {"skill_name": "SQL", "level": 2},
                {"skill_name": "HTML", "level": 2}
            ],
            "projects": [
                {"title": "Test Portfolio", "description": "HTML/CSS site", "tech_stack": ["HTML", "CSS"]}
            ]
        }
        res = await client.post("/api/v1/profile", json=onboarding_payload)
        assert res.status_code == 200, f"Profile onboarding failed: {res.text}"
        profile_data = res.json()
        print(f"Profile saved: {profile_data['full_name']} with {len(profile_data['learner_skills'])} skills")

        print("\n--- 3. Testing Career Role Selection (Full Stack Developer) ---")
        # Find Full Stack Developer ID
        roles_res = await client.get("/api/v1/careers")
        roles = roles_res.json()
        fs_role = next(r for r in roles if r["name"] == "Full Stack Developer")
        da_role = next(r for r in roles if r["name"] == "Data Analyst")
        
        res = await client.post("/api/v1/careers/select", json={"career_role_id": fs_role["id"]})
        assert res.status_code == 200, f"Career select failed: {res.text}"
        print(f"Selected Career Role: {fs_role['name']} (ID: {fs_role['id']})")

        print("\n--- 4. Testing Skill Gap Analysis ---")
        res = await client.get("/api/v1/skills/gap-analysis")
        assert res.status_code == 200, f"Gap analysis failed: {res.text}"
        gap_data = res.json()
        print(f"Readiness Score: {gap_data['readiness_score']}%")
        print(f"Gaps Identified: {[g['skill'] for g in gap_data['gaps']]}")
        print(f"Next Best Action: {gap_data['next_best_action']}")
        gap_skill_names = [g["skill"] for g in gap_data["gaps"]]
        assert "JavaScript" in gap_skill_names, "JavaScript must be in gaps"
        assert "React" in gap_skill_names, "React must be in gaps"
        assert "Node.js" in gap_skill_names, "Node.js must be in gaps"

        print("\n--- 5. Testing Prerequisite-Aware Roadmap Generation ---")
        # Generate roadmap
        gen_res = await client.post("/api/v1/roadmap/generate")
        assert gen_res.status_code == 200, f"Roadmap generation failed: {gen_res.text}"
        roadmap_data = gen_res.json()
        print(f"Roadmap Version: {roadmap_data['version']}, Status: {roadmap_data['status']}")
        
        modules = roadmap_data["modules"]
        module_status_map = {m["skill_name"]: m["status"] for m in modules}
        print("Module statuses:")
        for s_name, stat in module_status_map.items():
            print(f"  - {s_name}: {stat}")

        assert module_status_map.get("JavaScript") in ["available", "in_progress"], "JavaScript should be available"
        assert module_status_map.get("React") == "locked", "React must be locked initially"
        assert module_status_map.get("Node.js") == "locked", "Node.js must be locked initially"

        print("\n--- 6. Testing Diagnostic Assessment: JavaScript ---")
        # Start JavaScript assessment (id: 1)
        start_res = await client.post("/api/v1/assessments/1/start")
        assert start_res.status_code == 200, f"Start assessment failed: {start_res.text}"
        test_session = start_res.json()
        attempt_id = test_session["attempt_id"]
        questions = test_session["questions"]
        print(f"Started attempt {attempt_id} with {len(questions)} questions")

        print("\n--- 7. Testing Adaptive Replanning: Low Score (<50%) ---")
        # Intentionally submit incorrect answers to simulate <50% score
        low_answers = [{"question_id": q["id"], "selected_option": "D"} for q in questions]
        sub_res = await client.post(f"/api/v1/assessments/attempts/{attempt_id}/submit", json={"answers": low_answers})
        assert sub_res.status_code == 200, f"Submit failed: {sub_res.text}"
        sub_data = sub_res.json()
        print(f"Low Score Result: {sub_data['mastery_percentage']}%")
        print(f"Roadmap Changes: {sub_data['roadmap_changes']}")
        
        # Verify roadmap reflects needs_revision and locked dependents
        rm_res = await client.get("/api/v1/roadmap/active")
        active_rm = rm_res.json()
        js_mod = next(m for m in active_rm["modules"] if m["skill_name"] == "JavaScript")
        react_mod = next(m for m in active_rm["modules"] if m["skill_name"] == "React")
        print(f"JavaScript Module Status: {js_mod['status']}")
        print(f"React Module Status: {react_mod['status']}")
        assert js_mod["status"] == "needs_revision", "JavaScript must be marked needs_revision on low score"
        assert react_mod["status"] == "locked", "React must stay locked"

        print("\n--- 8. Testing Adaptive Replanning: High Score (>=85%) ---")
        # Start a new attempt for JavaScript
        start2_res = await client.post("/api/v1/assessments/1/start")
        attempt2_id = start2_res.json()["attempt_id"]
        # Correct answers for JS: Q1:B, Q2:B, Q3:C, Q4:B, Q5:A, Q6:C, Q7:B, Q8:B
        correct_map = {1: "B", 2: "B", 3: "C", 4: "B", 5: "A", 6: "C", 7: "B", 8: "B"}
        high_answers = [{"question_id": q["id"], "selected_option": correct_map.get(q["id"], "B")} for q in questions]
        sub2_res = await client.post(f"/api/v1/assessments/attempts/{attempt2_id}/submit", json={"answers": high_answers})
        assert sub2_res.status_code == 200, f"Submit 2 failed: {sub2_res.text}"
        sub2_data = sub2_res.json()
        print(f"High Score Result: {sub2_data['mastery_percentage']}%")
        print(f"Roadmap Changes: {sub2_data['roadmap_changes']}")
        assert sub2_data["mastery_percentage"] >= 85.0, "Score must be >= 85%"

        # Verify React and Node.js are unlocked
        rm2_res = await client.get("/api/v1/roadmap/active")
        active_rm2 = rm2_res.json()
        react_mod2 = next(m for m in active_rm2["modules"] if m["skill_name"] == "React")
        node_mod2 = next(m for m in active_rm2["modules"] if m["skill_name"] == "Node.js")
        print(f"React Module Status after >=85% JS: {react_mod2['status']}")
        print(f"Node.js Module Status after >=85% JS: {node_mod2['status']}")
        assert react_mod2["status"] == "available", "React must unlock to available"
        assert node_mod2["status"] == "available", "Node.js must unlock to available"

        print("\n--- 9. Testing Career Goal Change to Data Analyst ---")
        change_res = await client.post("/api/v1/careers/select", json={"career_role_id": da_role["id"]})
        assert change_res.status_code == 200
        # Generate new Data Analyst roadmap
        da_gen = await client.post("/api/v1/roadmap/generate")
        assert da_gen.status_code == 200
        da_rm = da_gen.json()
        print(f"New Active Roadmap: {da_rm['career_role_name']}")
        assert da_rm["career_role_name"] == "Data Analyst"
        # Check preserved transferable skills (Python & SQL)
        prof_res = await client.get("/api/v1/profile/me")
        preserved_skills = {s["skill_name"]: s["verified_level"] for s in prof_res.json()["learner_skills"]}
        print(f"Preserved Learner Skills: {preserved_skills}")
        assert preserved_skills.get("Python", 0) >= 3.0, "Python level 3 must be preserved"
        assert preserved_skills.get("SQL", 0) >= 2.0, "SQL level 2 must be preserved"

        print("\n=======================================================")
        print("🎉 ALL 9 ACCEPTANCE CRITERIA VERIFIED AND PASSING 100%!")
        print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(test_end_to_end_flow())
