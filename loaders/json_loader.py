from pathlib import Path
import json
from typing import Union

def load_json_file(file_path: str) -> list:
    """
    Parse and extract text from JSON files.
    Handles nested structures by converting to readable format.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")

    def flatten_json(obj, parent_key="", depth=0, max_depth=5):
        """Recursively flatten JSON to readable text"""
        if depth > max_depth:
            return ""
        
        items = []
        
        if isinstance(obj, dict):
            for k, v in obj.items():
                key_str = f"{parent_key}.{k}" if parent_key else k
                if isinstance(v, (dict, list)):
                    items.append(f"{key_str}:")
                    items.append(flatten_json(v, key_str, depth + 1, max_depth))
                else:
                    items.append(f"{key_str}: {v}")
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:10]):  # Limit to first 10 items
                if isinstance(item, (dict, list)):
                    items.append(f"[{i}]:")
                    items.append(flatten_json(item, f"{parent_key}[{i}]", depth + 1, max_depth))
                else:
                    items.append(f"[{i}]: {item}")
            if len(obj) > 10:
                items.append(f"... and {len(obj) - 10} more items")
        
        return "\n".join(items)

    content = flatten_json(data)
    
    docs = [{
        "content": content,
        "metadata": {
            "source": path.name,
            "type": "json",
            "size": len(str(data))
        }
    }]

    return docs
