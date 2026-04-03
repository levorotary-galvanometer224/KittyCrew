from __future__ import annotations

from pathlib import Path

from kittycrew.models import SkillOption


def default_skill_roots(project_root: Path) -> list[Path]:
    roots = [
        Path.home() / ".codex",
        Path.home() / "PycharmProjects" / "kucoin" / ".github" / "skills",
        project_root / ".github" / "skills",
    ]
    existing: list[Path] = []
    for root in roots:
        if root.exists() and root not in existing:
            existing.append(root)
    return existing


def discover_skills(roots: list[Path]) -> list[SkillOption]:
    seen_paths: set[Path] = set()
    skills: list[SkillOption] = []

    for root in roots:
        if not root.exists():
            continue
        for skill_file in root.rglob("SKILL.md"):
            resolved = skill_file.resolve()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            skills.append(_read_skill_metadata(resolved))

    skills.sort(key=lambda item: (item.name.lower(), item.path.lower()))
    return skills


def resolve_skill_reference(reference: str | None, available_skills: list[SkillOption]) -> SkillOption | None:
    if not reference:
        return None

    normalized = reference.strip()
    if not normalized:
        return None

    normalized_lower = normalized.lower()
    for skill in available_skills:
        if normalized_lower == skill.name.lower():
            return skill

    path_candidate = Path(normalized).expanduser()
    if path_candidate.is_dir():
        path_candidate = path_candidate / "SKILL.md"
    if path_candidate.exists():
        return _read_skill_metadata(path_candidate.resolve())

    for skill in available_skills:
        if normalized == skill.path:
            return skill

    raise ValueError(f"Skill '{normalized}' was not found. Choose a listed skill or provide a valid SKILL.md path.")


def resolve_skill_references(references: list[str] | None, available_skills: list[SkillOption]) -> list[SkillOption]:
    resolved: list[SkillOption] = []
    seen_paths: set[str] = set()

    for reference in references or []:
        skill = resolve_skill_reference(reference, available_skills)
        if not skill or skill.path in seen_paths:
            continue
        seen_paths.add(skill.path)
        resolved.append(skill)

    return resolved


def load_skill_text(skill_path: str | None) -> str | None:
    if not skill_path:
        return None

    path = Path(skill_path).expanduser()
    if not path.exists():
        return None

    return path.read_text(encoding="utf-8")


def _read_skill_metadata(path: Path) -> SkillOption:
    text = path.read_text(encoding="utf-8")
    metadata = _parse_frontmatter(text)
    name = metadata.get("name") or path.parent.name
    description = metadata.get("description")
    return SkillOption(name=name, path=str(path), description=description)


def _parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}

    metadata: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata
