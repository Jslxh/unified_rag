from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

def load_xml_file(file_path: str) -> list:
    """
    Parse and extract text from XML files.
    Converts XML structure to readable text format.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"{file_path} not found")

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML in {file_path}: {e}")

    def extract_text(element, level=0):
        """Recursively extract text from XML elements"""
        lines = []
        indent = "  " * level

        # Add element tag and attributes
        attrs = " ".join([f'{k}="{v}"' for k, v in element.attrib.items()])
        tag_line = f"{indent}<{element.tag} {attrs}>" if attrs else f"{indent}<{element.tag}>"
        lines.append(tag_line)

        # Add text content if exists
        if element.text and element.text.strip():
            lines.append(f"{indent}  {element.text.strip()}")

        # Process child elements
        for child in element:
            lines.extend(extract_text(child, level + 1))

        # Add closing tag
        lines.append(f"{indent}</{element.tag}>")

        return lines

    content = "\n".join(extract_text(root))

    docs = [{
        "content": content,
        "metadata": {
            "source": path.name,
            "type": "xml",
            "root_tag": root.tag,
            "element_count": len(list(root.iter()))
        }
    }]

    return docs
