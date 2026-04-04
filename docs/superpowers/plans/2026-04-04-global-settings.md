# Global Settings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persisted global settings modal for theme selection and global skill allowlisting, and enforce that member skill selection only uses globally selected skills.

**Architecture:** Persist global settings in `AppState`, expose them through the existing bootstrap payload, and update them through a dedicated settings endpoint. The frontend reads those settings into app state, applies the selected theme through CSS variables, and routes all member skill pickers through the persisted allowlist while the backend enforces the same rule.

**Tech Stack:** FastAPI, Pydantic, vanilla JavaScript modules, CSS, pytest, Node test runner

---

### Task 1: Add failing backend tests for persisted settings and allowlist enforcement

**Files:**
- Modify: `tests/test_app.py`
- Modify: `tests/test_service.py`

- [ ] **Step 1: Write failing API/state tests**

```python
def test_bootstrap_includes_default_global_settings(client):
    payload = client.get("/api/state").json()
    assert payload["state"]["site_theme"] == "candy-soft"
    assert payload["state"]["global_skills"] == []

def test_patch_settings_persists_theme_and_global_skills(client):
    skills = client.get("/api/skills").json()["skills"]
    skill_path = skills[0]["path"]

    response = client.patch(
        "/api/settings",
        json={"site_theme": "midnight-ink", "global_skill_references": [skill_path]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"]["site_theme"] == "midnight-ink"
    assert [item["path"] for item in body["state"]["global_skills"]] == [skill_path]
```

- [ ] **Step 2: Run backend state tests to verify they fail**

Run: `pytest tests/test_app.py -q`
Expected: FAIL because `AppState` and `/api/settings` do not yet support global settings

- [ ] **Step 3: Write failing service validation tests**

```python
async def test_create_member_rejects_skill_outside_global_allowlist(service):
    crew = await service.create_crew()
    available = service.list_skills()
    await service.update_settings(site_theme="candy-soft", global_skill_references=[available[0].path])
    with pytest.raises(ValueError, match="global skill list"):
        await service.create_member(
            crew.id,
            ProviderType.CODEX,
            title="Scout",
            working_dir="/tmp/scout",
            skill_references=[available[-1].path],
        )
```

- [ ] **Step 4: Run service tests to verify they fail**

Run: `pytest tests/test_service.py -q`
Expected: FAIL because settings persistence and allowlist validation do not exist

### Task 2: Add failing frontend tests for allowlist filtering and strict skill resolution

**Files:**
- Modify: `tests/test_app_ui_state.mjs`

- [ ] **Step 1: Write failing UI state tests**

```javascript
test("filters member skill suggestions against the global allowlist", () => {
  const allSkills = [
    { name: "frontend-design", path: "/skills/frontend-design/SKILL.md" },
    { name: "brainstorming", path: "/skills/brainstorming/SKILL.md" },
  ];
  const allowedSkills = [allSkills[1]];

  const suggestions = getSkillSuggestions(allowedSkills, "front", []);
  assert.deepEqual(suggestions, []);
});

test("does not treat arbitrary text as a valid skill reference", () => {
  const skills = [{ name: "brainstorming", path: "/skills/brainstorming/SKILL.md" }];
  assert.equal(resolveSkillReference("custom-skill", skills), null);
});
```

- [ ] **Step 2: Run UI tests to verify they fail**

Run: `node --test tests/test_app_ui_state.mjs`
Expected: FAIL because free-form text still resolves as a value and the allowlist flow is not encoded in state helpers

### Task 3: Implement persisted settings and backend validation

**Files:**
- Modify: `src/kittycrew/models.py`
- Modify: `src/kittycrew/service.py`
- Modify: `src/kittycrew/app.py`
- Modify: `src/kittycrew/store.py`
- Modify: `tests/test_app.py`
- Modify: `tests/test_service.py`

- [ ] **Step 1: Add `AppState` fields and request/response models**

```python
class AppState(BaseModel):
    crews: list[Crew] = Field(default_factory=list)
    site_theme: str = "candy-soft"
    global_skills: list[SkillOption] = Field(default_factory=list)

class UpdateSettingsRequest(BaseModel):
    site_theme: str
    global_skill_references: list[str] = Field(default_factory=list)
```

- [ ] **Step 2: Add service update logic and allowlist validation**

```python
def _resolve_allowed_member_skills(self, state: AppState, references: list[str] | None) -> list[SkillOption]:
    resolved = resolve_skill_references(references or [], self.list_skills())
    allowed_paths = {skill.path for skill in state.global_skills}
    disallowed = [skill.name for skill in resolved if skill.path not in allowed_paths]
    if disallowed:
        raise ValueError("Member skills must come from the global skill list.")
    return resolved
```

- [ ] **Step 3: Add `PATCH /api/settings`**

```python
@app.patch("/api/settings", response_model=AppBootstrap)
async def update_settings(payload: UpdateSettingsRequest) -> AppBootstrap:
    return await active_service.update_settings(
        site_theme=payload.site_theme,
        global_skill_references=payload.global_skill_references,
    )
```

- [ ] **Step 4: Run backend tests until green**

Run: `pytest tests/test_app.py tests/test_service.py -q`
Expected: PASS

### Task 4: Implement global settings modal, theme switching, and allowlist pickers

**Files:**
- Modify: `src/kittycrew/templates/index.html`
- Modify: `src/kittycrew/static/app.js`
- Modify: `src/kittycrew/static/styles.css`
- Modify: `tests/test_app_ui_state.mjs`

- [ ] **Step 1: Add settings button and modal markup**

```html
<section class="settings-bar">
  <button id="global-settings-button" class="settings-trigger" type="button">Global settings</button>
</section>
```

- [ ] **Step 2: Add frontend state, theme application, and modal handlers**

```javascript
state.siteTheme = "candy-soft";
state.globalSkills = [];
state.globalSkillSelections = [];

function applyTheme(themeId) {
  document.body.dataset.theme = themeId;
}
```

- [ ] **Step 3: Route member skill pickers through the global allowlist**

```javascript
const allowedSkills = state.globalSkills;
const skill = resolveSkillReference(state.memberSkillCustom.trim(), allowedSkills);
```

- [ ] **Step 4: Run UI tests until green**

Run: `node --test tests/test_app_ui_state.mjs`
Expected: PASS

### Task 5: Run end-to-end verification

**Files:**
- Modify: `task_plan.md`
- Modify: `progress.md`

- [ ] **Step 1: Run targeted suite**

Run: `pytest tests/test_app.py tests/test_service.py -q && node --test tests/test_app_ui_state.mjs`
Expected: PASS

- [ ] **Step 2: Run full suite**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 3: Record results in planning files**

```markdown
- Verified persisted settings API, service allowlist enforcement, and frontend state/theme behavior.
```
