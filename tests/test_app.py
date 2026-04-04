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

    settings_response = client.patch(
        "/api/settings",
        json={
            "site_theme": "candy-soft",
            "global_skill_references": [str(skill_file)],
        },
    )
    assert settings_response.status_code == 200

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


def test_app_bootstrap_includes_default_global_settings(tmp_path) -> None:
    client = TestClient(create_app(build_service(tmp_path)))

    response = client.get("/api/state")
    assert response.status_code == 200

    payload = response.json()
    assert payload["state"]["site_theme"] == "candy-soft"
    assert payload["state"]["global_skills"] == []


def test_app_updates_global_settings(tmp_path) -> None:
    skill_file = tmp_path / "demo-skill" / "SKILL.md"
    skill_file.parent.mkdir()
    skill_file.write_text("---\nname: demo-skill\n---\n", encoding="utf-8")

    service = build_service(tmp_path)
    service.skill_roots = [tmp_path]
    client = TestClient(create_app(service))

    response = client.patch(
        "/api/settings",
        json={
            "site_theme": "midnight-ink",
            "global_skill_references": [str(skill_file)],
        },
    )
    assert response.status_code == 200

    body = response.json()
    assert body["state"]["site_theme"] == "midnight-ink"
    assert [skill["path"] for skill in body["state"]["global_skills"]] == [str(skill_file.resolve())]


def test_app_create_member_accepts_title_and_rejects_duplicate_names(tmp_path) -> None:
    client = TestClient(create_app(build_service(tmp_path)))

    crew_id = client.post("/api/crews").json()["crew"]["id"]

    created = client.post(
        f"/api/crews/{crew_id}/members",
        json={"provider": "claude_code", "title": "Mochi Whiskers"},
    )
    assert created.status_code == 201
    assert created.json()["member"]["title"] == "Mochi Whiskers"

    duplicate = client.post(
        f"/api/crews/{crew_id}/members",
        json={"provider": "codex", "title": "Mochi Whiskers"},
    )
    assert duplicate.status_code == 422
    assert "already in use" in duplicate.json()["detail"]


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

    settings_response = client.patch(
        "/api/settings",
        json={
            "site_theme": "candy-soft",
            "global_skill_references": [str(first_skill), str(second_skill)],
        },
    )
    assert settings_response.status_code == 200

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


def test_app_rejects_member_skill_outside_global_skill_list(tmp_path) -> None:
    allowed_skill = tmp_path / "allowed-skill" / "SKILL.md"
    allowed_skill.parent.mkdir()
    allowed_skill.write_text("---\nname: allowed-skill\n---\n", encoding="utf-8")
    blocked_skill = tmp_path / "blocked-skill" / "SKILL.md"
    blocked_skill.parent.mkdir()
    blocked_skill.write_text("---\nname: blocked-skill\n---\n", encoding="utf-8")

    service = build_service(tmp_path)
    service.skill_roots = [tmp_path]
    client = TestClient(create_app(service))

    settings_response = client.patch(
        "/api/settings",
        json={
            "site_theme": "candy-soft",
            "global_skill_references": [str(allowed_skill)],
        },
    )
    assert settings_response.status_code == 200

    crew_id = client.post("/api/crews").json()["crew"]["id"]

    member_response = client.post(
        f"/api/crews/{crew_id}/members",
        json={
            "provider": "claude_code",
            "skill_references": [str(blocked_skill)],
        },
    )
    assert member_response.status_code == 422
    assert "global skill list" in member_response.json()["detail"]
