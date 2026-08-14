"""Schema context builder - merges introspection with curated annotations."""

import os
from typing import Any

import yaml

from app.schema.introspector import get_full_schema


_annotations_cache: dict | None = None
_schema_cache: dict | None = None
_db_relationships_cache: dict | None = None


def load_annotations() -> dict:
    """Load the curated annotations YAML file."""
    global _annotations_cache
    if _annotations_cache is None:
        annotations_path = os.path.join(
            os.path.dirname(__file__), "annotations.yaml"
        )
        with open(annotations_path, "r") as f:
            _annotations_cache = yaml.safe_load(f)
    return _annotations_cache


def load_schema_cache() -> dict:
    """Load the cached schema reference (centers, batches, enums, etc.)."""
    global _schema_cache
    if _schema_cache is None:
        cache_path = os.path.join(
            os.path.dirname(__file__), "schema_cache.yaml"
        )
        if os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                _schema_cache = yaml.safe_load(f)
        else:
            _schema_cache = {}
    return _schema_cache


def load_db_relationships() -> dict:
    """Load the complete FK relationship graph."""
    global _db_relationships_cache
    if _db_relationships_cache is None:
        rel_path = os.path.join(
            os.path.dirname(__file__), "db_relationships.yaml"
        )
        if os.path.exists(rel_path):
            with open(rel_path, "r") as f:
                _db_relationships_cache = yaml.safe_load(f)
        else:
            _db_relationships_cache = {}
    return _db_relationships_cache


def get_domain_tables(domain: str) -> list[str]:
    """Get the list of tables relevant to a specific domain."""
    annotations = load_annotations()
    domains = annotations.get("domains", {})
    if domain in domains:
        return domains[domain].get("tables", [])
    # If domain not found, return all tables
    all_tables = set()
    for d in domains.values():
        all_tables.update(d.get("tables", []))
    return list(all_tables)


def get_domain_notes(domain: str) -> list[str]:
    """Get domain-specific notes and guidelines."""
    annotations = load_annotations()
    domains = annotations.get("domains", {})
    if domain in domains:
        return domains[domain].get("notes", [])
    return []


def get_excluded_columns() -> list[str]:
    """Get columns that should be excluded from schema context."""
    annotations = load_annotations()
    return annotations.get("excluded_columns", [])


def get_table_annotation(table_name: str) -> dict[str, Any]:
    """Get annotation for a specific table."""
    annotations = load_annotations()
    tables = annotations.get("tables", {})
    return tables.get(table_name, {})


def get_relationships() -> list[str]:
    """Get all relationship definitions."""
    annotations = load_annotations()
    return annotations.get("relationships", [])


async def build_schema_context(
    domain: str | None = None, include_relationships: bool = True
) -> str:
    """
    Build a schema context string for the LLM prompt.

    Args:
        domain: If specified, only include tables for this domain.
                If None, include all tables.
        include_relationships: Whether to include relationship info.

    Returns:
        Formatted schema context string ready for LLM prompt.
    """
    # Get live schema from DB
    full_schema = await get_full_schema()
    excluded_cols = get_excluded_columns()

    # Determine which tables to include
    if domain:
        relevant_tables = get_domain_tables(domain)
    else:
        relevant_tables = list(full_schema.keys())

    # Build the context string
    lines = []

    if domain:
        annotations = load_annotations()
        domain_info = annotations.get("domains", {}).get(domain, {})
        lines.append(f"## Domain: {domain.title()}")
        if domain_info.get("description"):
            lines.append(f"Description: {domain_info['description']}")
        lines.append("")

        # Domain notes
        notes = get_domain_notes(domain)
        if notes:
            lines.append("### Important Notes:")
            for note in notes:
                lines.append(f"- {note}")
            lines.append("")

    lines.append("### Database Tables:\n")

    for table_name in relevant_tables:
        if table_name not in full_schema:
            continue

        columns = full_schema[table_name]
        annotation = get_table_annotation(table_name)

        # Table header with description
        table_desc = annotation.get("description", "")
        lines.append(f"**{table_name}** - {table_desc}")

        # Column details
        col_annotations = annotation.get("columns", {})
        lines.append("| Column | Type | Description |")
        lines.append("|--------|------|-------------|")

        for col in columns:
            col_name = col["column_name"]
            # Skip excluded columns
            if col_name in excluded_cols:
                continue
            col_type = col["data_type"]
            col_desc = col_annotations.get(col_name, "")
            pk_marker = " (PK)" if col.get("is_primary_key") else ""
            lines.append(f"| {col_name}{pk_marker} | {col_type} | {col_desc} |")

        lines.append("")

    # Add relationships
    if include_relationships:
        relationships = get_relationships()
        # Filter to relevant tables
        relevant_rels = []
        for rel in relationships:
            for table in relevant_tables:
                if table in rel:
                    relevant_rels.append(rel)
                    break

        if relevant_rels:
            lines.append("### Relationships (JOINs):")
            for rel in relevant_rels:
                lines.append(f"- {rel}")
            lines.append("")

    # Add cached reference data (centers, enums, etc.)
    cache = load_schema_cache()
    if cache:
        lines.append("### Reference Data (exact values in DB):")
        if cache.get("centers"):
            lines.append(f"- Centers: {', '.join(cache['centers'][:10])}...")
        if cache.get("enums"):
            for enum_name, values in cache["enums"].items():
                if any(enum_name in note.lower() for note in (get_domain_notes(domain) if domain else [])):
                    lines.append(f"- {enum_name}: {', '.join(values)}")
        if cache.get("table_quoting"):
            quoted = cache["table_quoting"].get("needs_quotes", [])
            if quoted:
                lines.append(f"- Tables needing double quotes: {', '.join(quoted[:8])}...")
        lines.append("")

    # Add common JOIN paths from db_relationships
    db_rels = load_db_relationships()
    if db_rels and db_rels.get("common_paths"):
        lines.append("### Common JOIN Paths:")
        # Include relevant paths based on domain
        domain_to_path_keys = {
            "attendance": ["student_with_center_and_batch", "student_attendance_with_class", "attendance_in_semester", "student_nth_semester"],
            "academics": ["student_exam_marks", "student_with_center_and_batch", "student_semester", "student_nth_semester"],
            "coding": ["student_submissions", "student_with_center_and_batch"],
            "clubs": ["club_members_with_center", "student_with_center_and_batch"],
            "students": ["student_with_center_and_batch", "student_semester"],
            "placements": ["student_with_center_and_batch"],
        }
        path_keys = domain_to_path_keys.get(domain, list(db_rels["common_paths"].keys())[:4])
        for key in path_keys:
            if key in db_rels["common_paths"]:
                lines.append(f"```\n-- {key}:\n{db_rels['common_paths'][key].strip()}\n```")
        lines.append("")

    # Add domain-specific FK relationships
    if db_rels:
        domain_to_rel_keys = {
            "attendance": ["student_joins", "attendance_joins"],
            "academics": ["student_joins", "academics_joins"],
            "coding": ["student_joins", "coding_joins"],
            "clubs": ["student_joins", "club_joins"],
            "placements": ["student_joins", "career_joins"],
            "students": ["student_joins", "organization_joins"],
        }
        rel_keys = domain_to_rel_keys.get(domain, ["student_joins", "organization_joins"])
        rel_lines = []
        for key in rel_keys:
            if key in db_rels:
                rel_lines.extend(db_rels[key])
        if rel_lines:
            lines.append("### FK Relationships:")
            for rel in rel_lines[:15]:  # Limit to avoid token bloat
                lines.append(f"- {rel}")
            lines.append("")

    return "\n".join(lines)


def get_available_domains() -> list[str]:
    """Get list of all available domains."""
    annotations = load_annotations()
    return list(annotations.get("domains", {}).keys())
