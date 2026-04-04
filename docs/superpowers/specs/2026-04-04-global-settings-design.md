# Global Settings Design

## Goal

Add a global settings experience that lets users choose the site theme and define a global skill allowlist. Member creation and member skill editing must only use skills from that allowlist.

## Context

KittyCrew currently exposes member-scoped skill selection in the create-member modal and the member skill management modal. The application bootstraps through `/api/state`, but persisted state only tracks crews. The UI has no system-level settings surface.

## Requirements

1. Add a global settings button below the hero banner.
2. Clicking the button opens a global settings modal.
3. The modal lets users choose a site theme.
4. The theme list includes the existing style plus four additional styles.
5. The modal lets users define a global skill list, initially empty.
6. Users choose global skills from discovered system skills only.
7. Creating a member and editing member skills must only allow skills from the selected global skill list.

## Proposed Design

### State Model

Extend `AppState` with:

- `site_theme`: a fixed theme id string
- `global_skills`: a list of `SkillOption` objects representing the selected allowlist

Use `SkillOption` values instead of only string paths so the frontend can render labels and descriptions without rebuilding them from a second payload. The request payloads will still send `skill_references` as paths, but the persisted state can hold canonical resolved skills.

### Theme Model

Use a fixed enum-like theme set:

- `candy-soft` for the current look
- `sunset-pop`
- `mint-garden`
- `midnight-ink`
- `peach-cream`

The frontend will apply the theme by writing `data-theme="<theme-id>"` on `document.body`. CSS will switch visual tokens through variables scoped by theme selectors.

### API Changes

Add one request/response path for global settings updates:

- `PATCH /api/settings`

Request fields:

- `site_theme`
- `global_skill_references`

`/api/state` continues to bootstrap the entire UI, including global settings. No separate read endpoint is required.

### Validation Rules

Backend validation is authoritative:

- `site_theme` must be one of the supported theme ids
- `global_skill_references` must resolve from discovered system skills only
- member creation skill references must be a subset of the global allowlist
- member skill updates must be a subset of the global allowlist

This prevents client-side bypass and keeps persisted state internally consistent.

### UI Changes

Add a settings row between the hero banner and the main app layout with a single “Global settings” button.

Add a new modal for:

- theme selection with one selected option at a time
- selected global skills list
- skill suggestion list sourced from all discovered system skills

Update member create and member skill modals so:

- suggestions come from `state.globalSkills` instead of all system skills
- free-form path entry is no longer accepted
- empty global allowlist means no selectable skills

### Error Handling

When the user tries to add a skill that is not allowed, show the existing toast error path with the backend message. When the global settings save fails, keep the modal open and preserve the user’s draft.

### Testing

Backend tests will cover:

- bootstrap includes global settings defaults
- settings updates persist theme and global skills
- member creation rejects skills outside the allowlist
- member skill updates reject skills outside the allowlist

Frontend tests will cover:

- suggestion filtering can target the global allowlist
- free-form skill entry no longer resolves to arbitrary paths
- theme options and settings state helpers behave deterministically
