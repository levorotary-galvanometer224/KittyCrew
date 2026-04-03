from __future__ import annotations

from fastapi.testclient import TestClient

from kittycrew.app import create_app

from test_service import build_service


def test_app_mounts_a2a_agent_cards(tmp_path) -> None:
    client = TestClient(create_app(build_service(tmp_path)))

    index_response = client.get("/")
    assert index_response.status_code == 200
    assert 'rel="icon"' in index_response.text
    assert "/static/avatars/banner-cat.svg" in index_response.text
    assert 'id="expanded-member-modal"' in index_response.text

    state_response = client.get("/api/state")
    assert state_response.status_code == 200

    card_response = client.get("/a2a/claude_code/.well-known/agent-card.json")
    assert card_response.status_code == 200

    card = card_response.json()
    assert card["name"] == "Claude Code A2A Agent"
    assert card["url"].endswith("/a2a/claude_code")
    assert card["capabilities"]["streaming"] is True

    assert client.get("/acp/agents").status_code == 404


def test_app_lists_provider_models_and_updates_member_model(tmp_path) -> None:
    client = TestClient(create_app(build_service(tmp_path)))

    crew_response = client.post("/api/crews")
    crew_id = crew_response.json()["crew"]["id"]

    member_response = client.post(f"/api/crews/{crew_id}/members", json={"provider": "claude_code"})
    member_id = member_response.json()["member"]["id"]

    models_response = client.get("/api/providers/claude_code/models")
    assert models_response.status_code == 200
    assert [model["id"] for model in models_response.json()["models"]] == ["claude_code-default", "claude_code-pro"]

    update_response = client.patch(f"/api/members/{member_id}/model", json={"model_id": "claude_code-pro"})
    assert update_response.status_code == 200
    assert update_response.json()["member"]["session"]["model_id"] == "claude_code-pro"


def test_app_lists_skills_and_accepts_member_create_options(tmp_path) -> None:
    skill_file = tmp_path / "demo-skill" / "SKILL.md"
    skill_file.parent.mkdir()
    skill_file.write_text(
        "---\nname: demo-skill\ndescription: Demo skill\n---\n\n# Demo Skill\n",
        encoding="utf-8",
    )

    client = TestClient(create_app(build_service(tmp_path)))
    client.app.state.service.skill_roots = [tmp_path]

    skills_response = client.get("/api/skills")
    assert skills_response.status_code == 200
    assert skills_response.json()["skills"][0]["name"] == "demo-skill"

    crew_response = client.post("/api/crews")
    crew_id = crew_response.json()["crew"]["id"]

    member_response = client.post(
        f"/api/crews/{crew_id}/members",
        json={
            "provider": "claude_code",
            "working_dir": str(tmp_path),
            "skill_references": [str(skill_file)],
        },
    )
    assert member_response.status_code == 201
    member = member_response.json()["member"]
    assert member["session"]["working_dir"] == str(tmp_path.resolve())
    assert member["session"]["skills"][0]["name"] == "demo-skill"


def test_app_updates_member_skills(tmp_path) -> None:
    first_skill = tmp_path / "first-skill" / "SKILL.md"
    first_skill.parent.mkdir()
    first_skill.write_text("---\nname: first-skill\n---\n", encoding="utf-8")
    second_skill = tmp_path / "second-skill" / "SKILL.md"
    second_skill.parent.mkdir()
    second_skill.write_text("---\nname: second-skill\n---\n", encoding="utf-8")

    service = build_service(tmp_path)
    service.skill_roots = [tmp_path]
    client = TestClient(create_app(service))

    crew_id = client.post("/api/crews").json()["crew"]["id"]
    member_id = client.post(
        f"/api/crews/{crew_id}/members",
        json={"provider": "claude_code", "skill_references": [str(first_skill)]},
    ).json()["member"]["id"]

    response = client.patch(
        f"/api/members/{member_id}/skills",
        json={"skill_references": [str(second_skill)]},
    )
    assert response.status_code == 200
    assert [skill["name"] for skill in response.json()["member"]["session"]["skills"]] == ["second-skill"]
