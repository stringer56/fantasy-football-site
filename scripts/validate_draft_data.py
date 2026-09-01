"""Validate canonical draft records, mappings, assets, and collection routes."""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_YEARS = {2021, 2022, 2023, 2024}
VALID_MAPPING_STATUSES = {"resolved", "unresolved"}


def load(name: str) -> dict:
    value = yaml.safe_load((ROOT / "_data" / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(f"_data/{name}: expected a schema_version 1 mapping")
    return value


def local_asset(raw_path: object, year: int) -> bool:
    prefix = f"/assets/img/drafts/{year}/"
    if not isinstance(raw_path, str) or not raw_path.startswith(prefix):
        return False
    path = (ROOT / raw_path.lstrip("/")).resolve()
    return ROOT.resolve() in path.parents and path.is_file() and path.stat().st_size > 50_000


def main() -> None:
    errors: list[str] = []
    drafts_data = load("drafts.yml")
    franchises_data = load("franchises.yml")
    seasons_data = load("seasons.yml")
    drafts = drafts_data.get("drafts")
    franchises = franchises_data.get("franchises")
    seasons = seasons_data.get("seasons")
    if not all(isinstance(items, list) for items in (drafts, franchises, seasons)):
        raise SystemExit("Draft validation failed: canonical arrays are missing")

    franchise_ids = {item.get("franchise_id") for item in franchises}
    season_years = {item.get("year") for item in seasons}
    years = [item.get("year") for item in drafts]
    if set(years) != EXPECTED_YEARS or len(years) != len(set(years)):
        errors.append("draft years must contain 2021-2024 exactly once")

    resolved_count = 0
    unresolved_count = 0
    asset_count = 0
    for draft in drafts:
        year = draft.get("year")
        label = str(year)
        if not isinstance(year, int):
            errors.append(f"{label}: year must be an integer")
            continue
        if year not in season_years:
            errors.append(f"{year}: corresponding season record is missing")
        route = ROOT / "_drafts" / f"{year}.md"
        if not route.is_file() or f"permalink: /drafts/{year}/" not in route.read_text(encoding="utf-8"):
            errors.append(f"{year}: collection route /drafts/{year}/ is missing")
        if draft.get("status") != "source_verified_images":
            errors.append(f"{year}: unsupported status {draft.get('status')!r}")
        if not str(draft.get("source_url") or "").startswith(
            "https://sites.google.com/view/road-to-glory-ffl/"
        ):
            errors.append(f"{year}: public Google source URL is required")
        if draft.get("draft_date") == "" or draft.get("location") == "":
            errors.append(f"{year}: unknown date/location must be null, never an empty string")
        if draft.get("draft_type") != "snake" or not str(draft.get("draft_type_note") or "").strip():
            errors.append(f"{year}: observed snake format and its provenance note are required")
        rounds = draft.get("rounds")
        team_count = draft.get("team_count")
        if not isinstance(rounds, int) or rounds <= 0:
            errors.append(f"{year}: rounds must be a positive integer")
        if not isinstance(team_count, int) or team_count <= 0:
            errors.append(f"{year}: team_count must be a positive integer")

        order = draft.get("draft_order")
        if not isinstance(order, list) or len(order) != team_count:
            errors.append(f"{year}: draft order length must match team_count")
            order = order if isinstance(order, list) else []
        slots = [entry.get("slot") for entry in order]
        if slots != list(range(1, len(order) + 1)) or len(slots) != len(set(slots)):
            errors.append(f"{year}: draft slots must be unique, complete, and ordered")
        for entry in order:
            slot = entry.get("slot")
            entry_label = f"{year} slot {slot}"
            franchise_id = entry.get("franchise_id")
            mapping_status = entry.get("mapping_status")
            display_name = entry.get("display_name_that_year")
            if mapping_status not in VALID_MAPPING_STATUSES:
                errors.append(f"{entry_label}: invalid mapping_status {mapping_status!r}")
            if not isinstance(display_name, str) or not display_name.strip():
                errors.append(f"{entry_label}: historical display name is required")
            if franchise_id == 0:
                errors.append(f"{entry_label}: unresolved identity must be null, never zero")
            if mapping_status == "resolved":
                resolved_count += 1
                if franchise_id not in franchise_ids:
                    errors.append(f"{entry_label}: unknown franchise_id {franchise_id!r}")
            elif mapping_status == "unresolved":
                unresolved_count += 1
                if franchise_id is not None:
                    errors.append(f"{entry_label}: unresolved mapping must have a null franchise_id")

        assets = draft.get("results_assets")
        if not isinstance(assets, list) or len(assets) != 3:
            errors.append(f"{year}: exactly three result image assets are required")
            assets = assets if isinstance(assets, list) else []
        asset_paths: set[str] = set()
        for asset in assets:
            raw_path = asset.get("path")
            if raw_path in asset_paths:
                errors.append(f"{year}: duplicate result asset {raw_path!r}")
            asset_paths.add(raw_path)
            if not local_asset(raw_path, year):
                errors.append(f"{year}: missing, small, or invalid result asset {raw_path!r}")
            if not str(asset.get("rounds") or "").strip() or not str(asset.get("alt") or "").strip():
                errors.append(f"{year}: every result asset needs rounds and descriptive alt text")
            asset_count += 1
        for optional_asset in ("board_asset", "recap_asset"):
            value = draft.get(optional_asset)
            if value == "":
                errors.append(f"{year}: unknown {optional_asset} must be null, never empty")
            elif value is not None and not local_asset(value, year):
                errors.append(f"{year}: invalid {optional_asset} {value!r}")
        if draft.get("pick_data_status") != "image_only_unverified" or draft.get("picks") is not None:
            errors.append(f"{year}: unverified image-only pick data must remain explicitly null")
        if not isinstance(draft.get("notes"), list) or not draft["notes"]:
            errors.append(f"{year}: source notes are required")

    if errors:
        raise SystemExit("Draft validation failed:\n- " + "\n- ".join(errors))
    print(
        f"Validated {len(drafts)} drafts, {resolved_count} resolved and "
        f"{unresolved_count} unresolved order entries, {asset_count} local assets, and collection routes"
    )


if __name__ == "__main__":
    main()
