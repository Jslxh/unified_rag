from pathlib import Path

def load_text_file(file_path: str) -> dict:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "content": content,
        "metadata": {
            "source": path.name,
            "type": "text"
        }
    }
