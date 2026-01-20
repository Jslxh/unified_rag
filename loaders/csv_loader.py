from pathlib import Path
import csv
import pandas as pd

def load_csv_file(file_path: str) -> list:
    """
    Load and convert CSV data to readable text format.
    Preserves table structure and handles large datasets intelligently.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    try:
        df = pd.read_csv(path, encoding="utf-8")
    except Exception as e:
        raise ValueError(f"Error reading CSV file {file_path}: {e}")

    # Create readable table format
    content_parts = []

    # Add header info
    content_parts.append(f"CSV File: {path.name}")
    content_parts.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    content_parts.append(f"Columns: {', '.join(df.columns)}")
    content_parts.append("-" * 80)

    # Add table preview (first 50 rows or all if smaller)
    preview_rows = min(50, len(df))
    content_parts.append("TABLE DATA:")

    for idx, row in df.head(preview_rows).iterrows():
        row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
        content_parts.append(f"Row {idx + 1}: {row_text}")

    # Add statistics for large files
    if len(df) > preview_rows:
        content_parts.append(f"\n... and {len(df) - preview_rows} more rows")
        content_parts.append("\nDATASET SUMMARY:")
        for col in df.columns:
            content_parts.append(f"\n{col}:")
            if df[col].dtype in ['int64', 'float64']:
                content_parts.append(f"  Min: {df[col].min()}, Max: {df[col].max()}, Mean: {df[col].mean():.2f}")
            else:
                unique_vals = df[col].nunique()
                content_parts.append(f"  Unique values: {unique_vals}")
                if unique_vals <= 10:
                    content_parts.append(f"  Values: {', '.join(map(str, df[col].unique()[:10]))}")

    content = "\n".join(content_parts)

    docs = [{
        "content": content,
        "metadata": {
            "source": path.name,
            "type": "csv",
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns)
        }
    }]

    return docs
