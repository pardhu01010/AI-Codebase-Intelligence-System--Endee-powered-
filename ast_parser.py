import ast
import os
import json
try:
    import pypdf
except ImportError:
    pypdf = None

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


def parse_generic_file(file_path: str, max_chars: int = 1500) -> List[Dict[str, Any]]:
    """Fallback text parsing for non-python files. Splits densely packed text by character bounds."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
    except OSError:
        return []
        
    if not source.strip():
        return []
        
    lines = source.splitlines()
    items = []
    
    current_chunk = []
    current_len = 0
    start_line = 1
    
    for i, line in enumerate(lines):
        line_len = len(line)
        
        # Extreme safeguard: if a single line is more than 3000 characters, it's likely 
        # minified garbage or Base64 data. We completely drop it to save tokens.
        if line_len > max_chars * 2:
            continue
            
        if current_len + line_len > max_chars and current_chunk:
            chunk_code = "\n".join(current_chunk).strip()
            if chunk_code:
                items.append({
                    "file": os.path.basename(file_path),
                    "filepath": file_path,
                    "type": "file_chunk",
                    "name": f"{os.path.basename(file_path)} (Lines {start_line}-{i})",
                    "docstring": "",
                    "start_line": start_line,
                    "end_line": i,
                    "code": chunk_code,
                })
            current_chunk = [line]
            current_len = line_len
            start_line = i + 1
        else:
            current_chunk.append(line)
            current_len += line_len
            
    if current_chunk:
        chunk_code = "\n".join(current_chunk).strip()
        if chunk_code:
            items.append({
                "file": os.path.basename(file_path),
                "filepath": file_path,
                "type": "file_chunk",
                "name": f"{os.path.basename(file_path)} (Lines {start_line}-{len(lines)})",
                "docstring": "",
                "start_line": start_line,
                "end_line": len(lines),
                "code": chunk_code,
            })
            
    return items


def parse_jupyter_notebook(file_path: str) -> List[Dict[str, Any]]:
    """Native parser for .ipynb files extracting explicitly code/markdown cells."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []

    items = []
    cells = data.get("cells", [])
    
    for idx, cell in enumerate(cells):
        cell_type = cell.get("cell_type")
        if cell_type in {"code", "markdown"}:
            source_lines = cell.get("source", [])
            if isinstance(source_lines, str):
                source_code = source_lines.strip()
            else:
                source_code = "".join(source_lines).strip()
                
            if source_code:
                items.append({
                    "file": os.path.basename(file_path),
                    "filepath": file_path,
                    "type": f"notebook_{cell_type}",
                    "name": f"{os.path.basename(file_path)} (Cell {idx+1})",
                    "docstring": "",
                    "start_line": idx + 1,
                    "end_line": idx + 1,
                    "code": source_code,
                })
                
    return items


def parse_pdf_file(file_path: str) -> List[Dict[str, Any]]:
    """Linguistic parser for PDFs extracting page-by-page text."""
    if pypdf is None:
        return []
        
    items = []
    try:
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                if text and text.strip():
                    items.append({
                        "file": os.path.basename(file_path),
                        "filepath": file_path,
                        "type": "pdf_page",
                        "name": f"{os.path.basename(file_path)} (Page {page_num+1})",
                        "docstring": "",
                        "start_line": page_num + 1,
                        "end_line": page_num + 1,
                        "code": text.strip(),
                    })
    except Exception:
        pass
        
    return items
