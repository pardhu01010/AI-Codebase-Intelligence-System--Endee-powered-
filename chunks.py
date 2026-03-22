from typing import Any, Dict, List


def build_chunks(parsed_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert parsed AST items into structured chunks for the vector DB."""
    chunks = []
    for item in parsed_items:
        content_header = (
            f"File: {item['file']}\nType: {item['type']}\nName: {item['name']}\n"
        )
        if item["docstring"]:
            content_header += f"Docstring: {item['docstring']}\n"
        full_content = f"{content_header}\nCode:\n{item['code']}"
        chunk = {
            "content": full_content,
            "metadata": {
                "file": item["file"],
                "filepath": item["filepath"],
                "type": item["type"],
                "name": item["name"],
                "docstring": item["docstring"],
                "lines": f"{item['start_line']}-{item['end_line']}",
            },
        }
        chunks.append(chunk)
    return chunks
