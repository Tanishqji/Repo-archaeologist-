import os
import re
from typing import Dict, List
from pydantic import BaseModel

class CodeChunk(BaseModel):
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str

def chunk_file(path: str, content: str, chunk_lines: int = 60, overlap: int = 15) -> List[CodeChunk]:
    chunks: List[CodeChunk] = []
    lines = content.splitlines()
    if not lines:
        return chunks

    total_lines = len(lines)
    start = 0

    while start < total_lines:
        end = min(start + chunk_lines, total_lines)
        chunk_text = "\n".join(lines[start:end])
        chunk_id = f"{path}:{start + 1}-{end}"
        chunks.append(
            CodeChunk(
                chunk_id=chunk_id,
                file_path=path,
                start_line=start + 1,
                end_line=end,
                content=chunk_text,
            )
        )
        if end >= total_lines:
            break
        start += chunk_lines - overlap

    return chunks

def chunk_repository(files: Dict[str, str]) -> List[CodeChunk]:
    all_chunks: List[CodeChunk] = []
    for path, content in files.items():
        # Skip binary, minified, or lock files
        if path.endswith((".min.js", ".min.css", ".map", ".lock", "package-lock.json")):
            continue
        all_chunks.extend(chunk_file(path, content))
    return all_chunks
