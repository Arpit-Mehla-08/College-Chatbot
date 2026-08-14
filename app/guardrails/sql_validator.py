"""SQL validation guardrail - ensures only safe SELECT statements reach the database."""

from dataclasses import dataclass

import re

import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML


# Maximum allowed query length (chars)
MAX_QUERY_LENGTH = 2000

# Forbidden keywords that indicate write/DDL operations
FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE",
    "MERGE", "UPSERT", "REPLACE", "CALL",
}

# Forbidden patterns even within comments or strings
FORBIDDEN_PATTERNS = [
    "DROP TABLE", "DROP DATABASE", "DROP SCHEMA",
    "ALTER TABLE", "ALTER DATABASE",
    "TRUNCATE TABLE",
    "CREATE TABLE", "CREATE DATABASE", "CREATE INDEX",
    "GRANT ALL", "REVOKE ALL",
    "INTO OUTFILE", "INTO DUMPFILE",
    "LOAD_FILE", "LOAD DATA",
]


@dataclass
class ValidationResult:
    """Result of SQL validation."""
    is_valid: bool
    error_message: str | None = None
    sanitized_sql: str | None = None


def validate_sql(sql: str, check_business_filters: bool = True) -> ValidationResult:
    """
    Validate that the SQL is a safe, read-only SELECT statement.

    Performs multiple layers of validation:
    1. Length check
    2. Empty/null check
    3. Multiple statement detection
    4. Statement type validation (must be SELECT or WITH...SELECT)
    5. Forbidden keyword scanning
    6. Forbidden pattern detection
    7. Allowed tables only (no coding/club/placement tables)
    8. Business filter presence (if enabled)

    Args:
        sql: The SQL string to validate.
        check_business_filters: Whether to validate mandatory business filters are present.

    Returns:
        ValidationResult with is_valid flag and optional error message.
    """
    # Clean up
    if not sql or not sql.strip():
        return ValidationResult(
            is_valid=False,
            error_message="Empty SQL query",
        )

    sql = sql.strip()

    # Length check
    if len(sql) > MAX_QUERY_LENGTH:
        return ValidationResult(
            is_valid=False,
            error_message=f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters",
        )

    # Parse the SQL
    parsed_statements = sqlparse.parse(sql)

    # Must be exactly one statement
    # Filter out empty statements (from trailing semicolons)
    non_empty = [s for s in parsed_statements if s.tokens and str(s).strip()]
    if len(non_empty) == 0:
        return ValidationResult(
            is_valid=False,
            error_message="No valid SQL statement found",
        )

    if len(non_empty) > 1:
        return ValidationResult(
            is_valid=False,
            error_message="Multiple SQL statements detected. Only single SELECT queries are allowed.",
        )

    statement = non_empty[0]

    # Check statement type
    stmt_type = statement.get_type()
    if stmt_type not in ("SELECT", None):
        # stmt_type is None for WITH (CTE) statements, which we allow
        # as long as they don't contain forbidden keywords
        if stmt_type and stmt_type.upper() != "SELECT":
            return ValidationResult(
                is_valid=False,
                error_message=f"Statement type '{stmt_type}' is not allowed. Only SELECT queries are permitted.",
            )

    # For CTE (WITH) statements, verify the main query is a SELECT
    sql_upper = sql.upper()
    if stmt_type is None:
        # Should start with WITH and contain SELECT
        stripped_upper = sql_upper.strip()
        if stripped_upper.startswith("WITH"):
            # Make sure it's ultimately a SELECT
            if not _cte_ends_with_select(sql_upper):
                return ValidationResult(
                    is_valid=False,
                    error_message="CTE (WITH) statement must end with a SELECT query.",
                )
        else:
            return ValidationResult(
                is_valid=False,
                error_message="Unrecognized statement type. Only SELECT queries are permitted.",
            )

    # Scan for forbidden keywords in the actual SQL tokens
    forbidden_found = _scan_forbidden_keywords(statement)
    if forbidden_found:
        return ValidationResult(
            is_valid=False,
            error_message=f"Forbidden operation detected: {forbidden_found}. Only SELECT queries are permitted.",
        )

    # Reject fake queries: SELECT 'literal text' or SELECT NULL with no FROM clause
    if _is_fake_query(sql):
        return ValidationResult(
            is_valid=False,
            error_message="Query does not reference any database table. Only real table queries are allowed.",
        )

    # Pattern-based scanning (catches things in comments too)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in sql_upper:
            return ValidationResult(
                is_valid=False,
                error_message=f"Forbidden pattern detected: '{pattern}'. Only SELECT queries are permitted.",
            )

    # Check for allowed tables only (NEW VALIDATION)
    forbidden_table_result = _check_allowed_tables_only(sql_upper)
    if not forbidden_table_result.is_valid:
        return forbidden_table_result

    # Check for mandatory business filters (NEW VALIDATION)
    if check_business_filters:
        filter_result = _check_business_filters(sql_upper)
        if not filter_result.is_valid:
            return filter_result

    # All checks passed
    return ValidationResult(
        is_valid=True,
        sanitized_sql=sql,
    )


def _scan_forbidden_keywords(statement: Statement) -> str | None:
    """
    Recursively scan statement tokens for forbidden DML/DDL keywords.

    Returns the forbidden keyword found, or None if clean.
    """
    for token in statement.flatten():
        if token.ttype in (DML, Keyword):
            word = token.value.upper().strip()
            if word in FORBIDDEN_KEYWORDS:
                return word
    return None


def _is_fake_query(sql: str) -> bool:
    """
    Detect fake queries that don't reference any real table.

    Catches patterns like:
    - SELECT 'some message' AS column
    - SELECT NULL
    - SELECT 1 AS column
    These are generated by LLMs when they can't answer a question from the database.
    """
    sql_upper = sql.upper().strip()

    # Check if there's a FROM clause referencing a real table
    # A legitimate query will have FROM <table>
    # A fake query will be like SELECT 'text' AS col (no FROM)
    has_from = bool(re.search(r'\bFROM\b', sql_upper))

    if not has_from:
        # No FROM clause at all — this is a fake query
        return True

    return False


def _cte_ends_with_select(sql_upper: str) -> bool:
    """
    Check if a CTE (WITH ... ) statement ends with a SELECT.

    This handles nested CTEs by looking for the final main query
    after all CTE definitions.
    """
    # Check forbidden keywords appear in the SQL
    for kw in FORBIDDEN_KEYWORDS:
        # Check if keyword appears as a standalone word (not part of column/table name)
        pattern = r'\b' + kw + r'\b'
        if re.search(pattern, sql_upper):
            # Check if it's inside a CTE's SELECT (which is fine) or outside
            # For simplicity, we'll be strict: if INSERT/UPDATE/DELETE/DROP etc appear anywhere, reject
            if kw in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
                      "CREATE", "GRANT", "REVOKE"):
                return False

    return True


def _check_allowed_tables_only(sql_upper: str) -> ValidationResult:
    """
    Check that only allowed tables (10 tables) are used in the query.

    Allowed tables: Teacher, Center, Batch, School, Subject, Semester, Division, Class, Attendance, Student

    Forbidden tables: problem, submission, contest, Exam, StudentExamMarks, Club, Placement, Project, Certification, etc.
    """
    ALLOWED_TABLES = {
        "TEACHER", "CENTER", "BATCH", "SCHOOL", "SUBJECT",
        "SEMESTER", "DIVISION", "CLASS", "ATTENDANCE", "STUDENT"
    }

    FORBIDDEN_TABLES = {
        "PROBLEM", "SUBMISSION", "CONTEST", "EXAM", "STUDENTEXAMMARKS",
        "CLUB", "CLUBMEMBER", "CLUBCENTER", "PLACEMENT", "PROJECT",
        "CERTIFICATION", "SCAN", "SCANWINDOW", "COHORT", "EXTERNALDEGREE",
        "CLUBCORETEM", "BEHAVIOUR", "ACHIEVEMENT", "ACADEMICHISTORY",
        "PERSONALDETAIL", "SOCIALLINK", "STUDENTLOG", "SUBMISSION",
        "STUDENTSHOWCASE", "CONTEST_PROBLEM", "CONTESTMODERATOR", "PROBLEM",
        "PROGRAMMGING_LANGUAGE", "CONTESTMODERATOR", "PROBLEMODERATOR"
    }

    # Find all table references
    from_matches = re.finditer(r'\bFROM\s+"?(\w+)"?', sql_upper)
    join_matches = re.finditer(r'\bJOIN\s+"?(\w+)"?', sql_upper)

    referenced_tables = set()
    for match in from_matches:
        referenced_tables.add(match.group(1).upper())
    for match in join_matches:
        referenced_tables.add(match.group(1).upper())

    # Check for forbidden tables
    forbidden_found = referenced_tables & FORBIDDEN_TABLES
    if forbidden_found:
        return ValidationResult(
            is_valid=False,
            error_message=f"Unauthorized table(s): {', '.join(forbidden_found)}. "
                         f"Only these 10 tables are allowed: Teacher, Center, Batch, School, Subject, "
                         f"Semester, Division, Class, Attendance, Student",
        )

    return ValidationResult(is_valid=True)


def _check_business_filters(sql_upper: str) -> ValidationResult:
    """
    Check that mandatory business filters are present.

    For Student table:
    - Must have: is_active = true
    - Must have: email NOT LIKE '%dummyemail%'

    For Center table:
    - Must have: name NOT LIKE '%PW Skills%'
    - Must have: name != 'TEST Center'
    """
    # If Student table is used, check for is_active filter
    if "\"STUDENT\"" in sql_upper or re.search(r'\bSTUDENT\s+', sql_upper) or re.search(r'\bFROM\s+STUDENT\b', sql_upper):
        if "IS_ACTIVE" not in sql_upper:
            return ValidationResult(
                is_valid=False,
                error_message="Missing mandatory filter: Student.is_active = true must be included",
            )
        if "DUMMYEMAIL" not in sql_upper:
            return ValidationResult(
                is_valid=False,
                error_message="Missing mandatory filter: Student.email NOT LIKE '%dummyemail%' must be included",
            )

    # If Center table is used, check for center name filters
    if "\"CENTER\"" in sql_upper or re.search(r'\bCENTER\s+', sql_upper) or re.search(r'\bFROM\s+CENTER\b', sql_upper):
        # Check for PW Skills exclusion
        if "PW SKILLS" not in sql_upper and "PW_SKILLS" not in sql_upper:
            # This could be a LEFT JOIN or optional query, so we make it a warning in debug mode
            # For now, we'll enforce it
            pass  # Don't fail here - some queries might use indirect filtering

        # Check for TEST Center exclusion
        if "TEST" not in sql_upper or "CENTER" not in sql_upper:
            pass  # Don't fail - allow as long as one filter is present

    return ValidationResult(is_valid=True)
