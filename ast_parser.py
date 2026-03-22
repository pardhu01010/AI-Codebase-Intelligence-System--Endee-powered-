import ast
import os
from typing import Any, Dict, List


def parse_python_file(file_path: str) -> List[Dict[str, Any]]:
    """Parse a Python file and return extracted functions and classes."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError:
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    items = []
    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            docstring = ast.get_docstring(node)
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            code_snippet = "\n".join(lines[start_line - 1 : end_line]) if end_line else ""
            item_type = (
                "function"
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                else "class"
            )
            items.append(
                {
                    "file": os.path.basename(file_path),
                    "filepath": file_path,
                    "type": item_type,
                    "name": name,
                    "docstring": docstring or "",
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": code_snippet,
                }
            )

    items.append(
        {
            "file": os.path.basename(file_path),
            "filepath": file_path,
            "type": "module",
            "name": os.path.basename(file_path),
            "docstring": ast.get_docstring(tree) or "",
            "start_line": 1,
            "end_line": len(lines),
            "code": source,
        }
    )

    return items


def parse_generic_file(file_path: str) -> List[Dict[str, Any]]:
    """Fallback text parsing for non-python files."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError:
        return []
        
    if not source.strip():
        return []
        
    lines = source.splitlines()
    return [{
        "file": os.path.basename(file_path),
        "filepath": file_path,
        "type": "file",
        "name": os.path.basename(file_path),
        "docstring": "",
        "start_line": 1,
        "end_line": len(lines),
        "code": source,
    }]
