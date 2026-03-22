import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List


def clone_repo(repo_url: str) -> str:
    """Clones a GitHub repository to a temporary directory."""
    temp_dir = tempfile.mkdtemp(prefix="endee_repo_")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            check=True,
            capture_output=True,
        )
        return temp_dir
    except subprocess.CalledProcessError as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to clone repository: {e.stderr.decode()}") from e


def get_code_files(
    repo_path: str, extensions: set = {".py", ".md", ".js", ".ts", ".html"}
) -> List[str]:
    """Filters code files by extension, ignoring .git, venv, etc."""
    code_files = []
    ignore_dirs = {".git", "node_modules", "venv", ".venv", "__pycache__", "build", "dist"}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if Path(file).suffix in extensions:
                code_files.append(os.path.join(root, file))

    return code_files


def cleanup_repo(repo_path: str) -> None:
    """Removes the cloned repository directory."""
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path, ignore_errors=True)
