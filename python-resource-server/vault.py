from __future__ import annotations
import os
import re

VAULT_PATH = os.getenv("VAULT_PATH", "/home/nzrtnetw/vault")


def strip_frontmatter(content: str) -> str:
    content = content.lstrip("﻿")
    parts = re.split(r"^---\s*$", content, flags=re.MULTILINE)
    body = "".join(parts[2:]) if len(parts) >= 3 else content
    return re.sub(r"^(\[#[^\]]+\]\s*)+\r?\n?", "", body, flags=re.MULTILINE).strip()


def read_note(section: str, file: str) -> str:
    vault = os.path.realpath(VAULT_PATH)
    target = os.path.realpath(os.path.join(vault, section, f"{file}.md"))
    if not target.startswith(vault + os.sep) and target != vault:
        raise ValueError("Path traversal not allowed")
    if not os.path.isfile(target):
        raise FileNotFoundError(f"Note not found: {section}/{file}")
    with open(target, encoding="utf-8") as f:
        return f.read()


def search_vault(query: str, subfolder: str = "") -> list[dict]:
    if subfolder:
        search_root = os.path.realpath(os.path.join(VAULT_PATH, subfolder))
        vault = os.path.realpath(VAULT_PATH)
        if not search_root.startswith(vault + os.sep):
            raise ValueError("Path traversal not allowed")
    else:
        search_root = VAULT_PATH
    results: list[dict] = []
    lower = query.lower()
    for root, _, files in os.walk(search_root):
        if len(results) >= 10:
            break
        for name in files:
            if not name.endswith(".md") or len(results) >= 10:
                continue
            path = os.path.join(root, name)
            try:
                with open(path, encoding="utf-8") as f:
                    raw = f.read()
            except OSError:
                continue
            content = strip_frontmatter(raw)
            idx = content.lower().find(lower)
            if idx == -1:
                continue
            start = max(0, idx - 80)
            end = min(len(content), idx + 300)
            rel = os.path.relpath(path, VAULT_PATH)
            results.append({"file": rel, "excerpt": content[start:end].strip()})
    return results
