"""Chart analyzer - inspects raw query results and determines chart metadata."""

from typing import Optional


# Columns that suggest time-series data
TIME_KEYWORDS = {"date", "month", "year", "week", "semester", "quarter", "day", "period", "time"}

# Columns that are likely labels/categories
LABEL_KEYWORDS = {"name", "student", "teacher", "faculty", "center", "course", "subject", "department", "branch", "batch", "section", "type", "category", "status", "gender"}

# Columns that are likely numeric values (aggregates)
VALUE_KEYWORDS = {"count", "total", "avg", "average", "sum", "min", "max", "percentage", "percent", "score", "marks", "attendance", "amount", "fee", "salary", "gpa", "cgpa", "rank", "number"}


def _is_numeric(value) -> bool:
    """Check if a value is numeric."""
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    return False


def _classify_column(col_name: str, sample_values: list) -> str:
    """Classify a column as 'numeric', 'categorical', or 'temporal'."""
    col_lower = col_name.lower()

    # Check for temporal
    for kw in TIME_KEYWORDS:
        if kw in col_lower:
            return "temporal"

    # Check if values are numeric
    non_null_values = [v for v in sample_values if v is not None]
    if non_null_values and all(_is_numeric(v) for v in non_null_values[:5]):
        return "numeric"

    return "categorical"


def _is_id_column(col_name: str) -> bool:
    """Check if a column is likely an ID column (not useful for charting)."""
    col_lower = col_name.lower()
    return col_lower.endswith("_id") or col_lower == "id" or col_lower == "roll_no" or col_lower == "enrollment_no"


def analyze_chart_data(raw_results: list[dict]) -> Optional[dict]:
    """
    Analyze raw query results and determine if/how they should be charted.

    Returns None if data is not chartable.
    Returns a dict with:
        - suggested_chart_type: 'bar' | 'line' | 'pie' | 'area'
        - chart_config: { x_key, y_keys, title }
        - raw_data: cleaned data ready for charting
    """
    if not raw_results or len(raw_results) == 0:
        return None

    # Single-value aggregates aren't chartable (e.g., COUNT(*) = 42)
    if len(raw_results) == 1 and len(raw_results[0]) == 1:
        return None

    columns = list(raw_results[0].keys())

    # Classify each column
    column_types = {}
    for col in columns:
        if _is_id_column(col):
            continue
        sample_values = [row.get(col) for row in raw_results[:10]]
        column_types[col] = _classify_column(col, sample_values)

    # Identify potential x-axis (categorical/temporal) and y-axis (numeric) columns
    numeric_cols = [col for col, t in column_types.items() if t == "numeric"]
    temporal_cols = [col for col, t in column_types.items() if t == "temporal"]
    categorical_cols = [col for col, t in column_types.items() if t == "categorical"]

    # Need at least one numeric column for a chart
    if not numeric_cols:
        return None

    # Need at least one label/x-axis column
    if not temporal_cols and not categorical_cols:
        return None

    # Only chart if we have multiple rows (at least 2)
    if len(raw_results) < 2:
        return None

    # Determine x-axis: prefer temporal, fallback to categorical
    row_count = len(raw_results)

    if temporal_cols:
        x_key = temporal_cols[0]
        # Time series → line or area chart (works well even with many rows)
        suggested_type = "line"
    else:
        x_key = categorical_cols[0]

        # Skip chart entirely for large categorical datasets — a bar chart with
        # 30+ categories is unreadable and a pie chart with many slices is worse.
        if row_count > 25:
            return None

        # Small dataset with single metric → pie chart
        if row_count <= 6 and len(numeric_cols) == 1:
            suggested_type = "pie"
        else:
            suggested_type = "bar"

    # Use up to 3 numeric columns for y-axis
    y_keys = numeric_cols[:3]

    # Build a title from column names
    y_labels = ", ".join(col.replace("_", " ").title() for col in y_keys)
    x_label = x_key.replace("_", " ").title()
    title = f"{y_labels} by {x_label}"

    # Clean the raw data: ensure numeric values are actual numbers
    cleaned_data = []
    for row in raw_results:
        cleaned_row = {}
        # Always include the x-axis value
        cleaned_row[x_key] = row.get(x_key)
        # Include numeric columns
        for col in y_keys:
            val = row.get(col)
            if val is not None:
                try:
                    cleaned_row[col] = float(val) if "." in str(val) else int(val)
                except (ValueError, TypeError):
                    cleaned_row[col] = 0
            else:
                cleaned_row[col] = 0
        cleaned_data.append(cleaned_row)

    return {
        "suggested_chart_type": suggested_type,
        "chart_config": {
            "x_key": x_key,
            "y_keys": y_keys,
            "title": title,
        },
        "raw_data": cleaned_data,
    }
