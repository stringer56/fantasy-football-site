"""Validate canonical franchise, owner, asset, route, and Yahoo mappings."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PRIVATE_PATTERNS = (
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:diagnos|medical issue|refresh token|client secret|password)\b", re.I),
)


def load_yaml(name: str) -> dict:
    value = yaml.safe_load((ROOT / "_data" / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"_data/{name}: root must be a mapping")
    return value


def parse_front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError(f"{path.relative_to(ROOT)}: missing front matter")
    closing = text.find("\n---\n", 4)
    value = yaml.safe_load(text[4:closing])
    return value if isinstance(value, dict) else {}


def main() -> None:
    errors: list[str] = []
    franchises_data = load_yaml("franchises.yml")
    owners_data = load_yaml("owners.yml")
    retired_data = load_yaml("retired_franchises.yml")
    generated = json.loads((ROOT / "_data" / "generated" / "teams.json").read_text(encoding="utf-8"))
    history_manifest = json.loads(
        (ROOT / "_data" / "generated" / "history_manifest.json").read_text(encoding="utf-8")
    )

    for name, payload in (
        ("franchises.yml", franchises_data),
        ("owners.yml", owners_data),
        ("retired_franchises.yml", retired_data),
    ):
        if payload.get("schema_version") != 1:
            errors.append(f"_data/{name}: schema_version must be 1")

    franchises = franchises_data.get("franchises")
    owners = owners_data.get("owners")
    retired_ids = retired_data.get("retired_franchise_ids")
    if not isinstance(franchises, list) or not isinstance(owners, list) or not isinstance(retired_ids, list):
        raise SystemExit("Franchise validation failed: canonical arrays are missing")

    if len(franchises) != 13:
        errors.append(f"expected 13 canonical franchises, found {len(franchises)}")
    active = [item for item in franchises if item.get("status") == "active"]
    retired = [item for item in franchises if item.get("status") == "retired"]
    if len(active) != 12 or len(retired) != 1:
        errors.append(f"expected 12 active and 1 retired franchise, found {len(active)} and {len(retired)}")

    owner_by_id: dict[str, dict] = {}
    for owner in owners:
        owner_id = owner.get("owner_id")
        if not isinstance(owner_id, str) or not ID_PATTERN.fullmatch(owner_id):
            errors.append(f"invalid owner_id: {owner_id!r}")
            continue
        if owner_id in owner_by_id:
            errors.append(f"duplicate owner_id: {owner_id}")
        owner_by_id[owner_id] = owner
        if not str(owner.get("display_name") or "").strip():
            errors.append(f"owner {owner_id}: display_name is required")
        if not isinstance(owner.get("aliases"), list):
            errors.append(f"owner {owner_id}: aliases must be an array")

    ids: set[str] = set()
    slugs: set[str] = set()
    identity_to_id: dict[str, str] = {}
    mapped_team_keys: set[str] = set()
    generated_by_key = {team["team_key"]: team for team in generated.get("teams", [])}
    historical_by_key = {
        mapping["yahoo_team_key"]: mapping
        for season in history_manifest.get("seasons", [])
        for mapping in season.get("team_mappings", [])
        if mapping.get("yahoo_team_key") and mapping.get("status") == "verified"
    }
    collection_ids: dict[str, Path] = {}

    for path in sorted((ROOT / "_franchises").glob("*.md")):
        front_matter = parse_front_matter(path)
        franchise_id = front_matter.get("franchise_id")
        if franchise_id in collection_ids:
            errors.append(f"duplicate collection franchise_id: {franchise_id}")
        collection_ids[franchise_id] = path

    for franchise in franchises:
        franchise_id = franchise.get("franchise_id")
        slug = franchise.get("slug")
        label = str(franchise_id or slug or "unknown")
        if not isinstance(franchise_id, str) or not ID_PATTERN.fullmatch(franchise_id):
            errors.append(f"invalid franchise_id: {franchise_id!r}")
            continue
        if not isinstance(slug, str) or not ID_PATTERN.fullmatch(slug):
            errors.append(f"{label}: invalid slug {slug!r}")
        if franchise_id in ids:
            errors.append(f"duplicate franchise_id: {franchise_id}")
        if slug in slugs:
            errors.append(f"duplicate franchise slug: {slug}")
        ids.add(franchise_id)
        slugs.add(slug)

        names = [franchise.get("name"), *(franchise.get("aliases") or [])]
        for name in names:
            normalized = str(name or "").strip().casefold()
            if not normalized:
                errors.append(f"{label}: blank canonical name or alias")
                continue
            previous = identity_to_id.get(normalized)
            if previous and previous != franchise_id:
                errors.append(f"name/alias collision: {name!r} belongs to {previous} and {franchise_id}")
            identity_to_id[normalized] = franchise_id

        owner_ids = franchise.get("owner_ids")
        if not isinstance(owner_ids, list) or not owner_ids:
            errors.append(f"{label}: at least one owner_id is required")
        else:
            for owner_id in owner_ids:
                if owner_id not in owner_by_id:
                    errors.append(f"{label}: unknown owner_id {owner_id}")

        for rival_id in franchise.get("rival_franchise_ids") or []:
            if rival_id == franchise_id:
                errors.append(f"{label}: cannot be its own rival")

        branding = franchise.get("branding") or {}
        for field in ("identity_image", "venue_image"):
            raw_path = branding.get(field)
            if not isinstance(raw_path, str) or not raw_path.startswith("/assets/img/franchises/"):
                errors.append(f"{label}: {field} must be a local franchise asset")
                continue
            asset = (ROOT / raw_path.lstrip("/")).resolve()
            if ROOT.resolve() not in asset.parents or not asset.is_file():
                errors.append(f"{label}: missing asset {raw_path}")
            elif asset.stat().st_size < 1024:
                errors.append(f"{label}: asset is unexpectedly small {raw_path}")
            if not str(branding.get(field.replace("_image", "_alt")) or "").strip():
                errors.append(f"{label}: accessible alt text is required for {field}")
        honors_path = branding.get("honors_image")
        if honors_path and not (ROOT / str(honors_path).lstrip("/")).is_file():
            errors.append(f"{label}: missing honors asset {honors_path}")

        source_url = str((franchise.get("source") or {}).get("google_site_url") or "")
        parsed_source = urlsplit(source_url)
        if parsed_source.scheme != "https" or parsed_source.netloc != "sites.google.com":
            errors.append(f"{label}: invalid Google Site source URL")

        yahoo = franchise.get("yahoo") or {}
        key_map = yahoo.get("team_keys") or {}
        id_map = yahoo.get("team_ids") or {}
        name_map = yahoo.get("team_names") or {}
        if set(key_map) != set(id_map) or set(key_map) != set(name_map):
            errors.append(f"{label}: Yahoo season mapping keys do not align")
        for season, team_key in key_map.items():
            if team_key in mapped_team_keys:
                errors.append(f"duplicate Yahoo team key mapping: {team_key}")
            mapped_team_keys.add(team_key)
            generated_team = generated_by_key.get(team_key)
            historical_team = historical_by_key.get(team_key)
            if season == "2025" and not generated_team:
                errors.append(f"{label}: 2025 team key is absent from generated teams: {team_key}")
            elif generated_team:
                if generated_team.get("team_id") != id_map.get(season):
                    errors.append(f"{label}: Yahoo team_id mismatch for {season}")
                if generated_team.get("team_name") != name_map.get(season):
                    errors.append(f"{label}: Yahoo team_name mismatch for {season}")
                if str(name_map.get(season)).casefold() not in {str(name).casefold() for name in names}:
                    errors.append(f"{label}: Yahoo team_name must be canonical or an alias")
            elif not historical_team:
                errors.append(f"{label}: {season} team key is absent from the verified history manifest: {team_key}")
            else:
                if historical_team.get("candidate_franchise_id") != franchise_id:
                    errors.append(f"{label}: historical Yahoo franchise mismatch for {season}")
                if historical_team.get("yahoo_team_name") != name_map.get(season):
                    errors.append(f"{label}: historical Yahoo team_name mismatch for {season}")
                if str(name_map.get(season)).casefold() not in {str(name).casefold() for name in names}:
                    errors.append(f"{label}: historical Yahoo team_name must be canonical or an alias")

        page_path = collection_ids.get(franchise_id)
        if page_path is None:
            errors.append(f"{label}: collection profile page is missing")
        else:
            front_matter = parse_front_matter(page_path)
            expected = f"/retired/{slug}/" if franchise.get("status") == "retired" else None
            if expected and front_matter.get("permalink") != expected:
                errors.append(f"{label}: retired profile permalink must be {expected}")

    for franchise in franchises:
        for rival_id in franchise.get("rival_franchise_ids") or []:
            if rival_id not in ids:
                errors.append(f"{franchise['franchise_id']}: unknown rival franchise_id {rival_id}")

    expected_retired = {item["franchise_id"] for item in retired}
    if set(retired_ids) != expected_retired or len(retired_ids) != len(set(retired_ids)):
        errors.append("retired_franchises.yml must reference every retired franchise exactly once")
    if set(collection_ids) != ids:
        errors.append("collection profile IDs must exactly match canonical franchise IDs")

    active_owner_ids = [owner_id for item in active for owner_id in item.get("owner_ids", [])]
    if len(active_owner_ids) != 12 or len(set(active_owner_ids)) != 12:
        errors.append("active franchises must resolve to 12 distinct current owners")
    for owner_id in active_owner_ids:
        if owner_id in owner_by_id and owner_by_id[owner_id].get("active") is not True:
            errors.append(f"active franchise references inactive owner {owner_id}")

    public_text = "\n".join(
        (ROOT / "_data" / name).read_text(encoding="utf-8")
        for name in ("franchises.yml", "owners.yml", "retired_franchises.yml")
    )
    for pattern in PRIVATE_PATTERNS:
        if pattern.search(public_text):
            errors.append(f"public franchise data matched private-content pattern: {pattern.pattern}")

    if errors:
        raise SystemExit("Franchise validation failed:\n- " + "\n- ".join(errors))
    print("Validated 12 active franchises, 1 retired franchise, 12 current owners, local assets, routes, aliases, and Yahoo mappings")


if __name__ == "__main__":
    main()
