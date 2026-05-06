import fs from "fs";
import path from "path";

/**
 * Resolves and reads a single .md note from the vault.
 * section = subfolder path (e.g. "Blockchain/00 - Overview")
 * file    = filename without .md (e.g. "NZRT Blockchain Architecture")
 */
export function readNote(section: string, file: string): string {
  const VAULT_PATH = process.env.VAULT_PATH || "C:\\Users\\Natha\\Nextcloud2\\Documents\\Obsidian";
  const filePath = path.resolve(VAULT_PATH, section, `${file}.md`);

  // Prevent path traversal outside vault
  if (!filePath.startsWith(path.resolve(VAULT_PATH))) {
    throw new Error("Path traversal not allowed");
  }

  if (!fs.existsSync(filePath)) {
    throw new Error(`Note not found: ${section}/${file}`);
  }

  return fs.readFileSync(filePath, "utf-8");
}

/**
 * Simple grep-style search across all .md files in vault.
 * Returns up to 10 matches: { file, excerpt }.
 */
/** Strip YAML frontmatter and inline tag lines from content */
function stripFrontmatter(content: string): string {
  // Split on --- lines (handles CRLF + LF + BOM)
  const parts = content.replace(/^﻿/, "").split(/^-{3}\s*$/m);
  const body = parts.length >= 3 ? parts.slice(2).join("---") : content;
  // Strip [#"tag"] inline lines
  return body.replace(/^(\[#[^\]]+\]\s*)+\r?\n?/gm, "").trim();
}

export function searchVault(query: string): { file: string; excerpt: string }[] {
  const VAULT_PATH = process.env.VAULT_PATH || "C:\\Users\\Natha\\Nextcloud2\\Documents\\Obsidian";
  const results: { file: string; excerpt: string }[] = [];
  const lowerQuery = query.toLowerCase();

  function walk(dir: string): void {
    if (results.length >= 10) return;
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      if (results.length >= 10) break;
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
      } else if (entry.name.endsWith(".md")) {
        const raw = fs.readFileSync(fullPath, "utf-8");
        const content = stripFrontmatter(raw);
        const idx = content.toLowerCase().indexOf(lowerQuery);
        if (idx !== -1) {
          const start = Math.max(0, idx - 80);
          const end = Math.min(content.length, idx + 300);
          const relative = path.relative(VAULT_PATH, fullPath);
          results.push({ file: relative, excerpt: content.slice(start, end).trim() });
        }
      }
    }
  }

  walk(VAULT_PATH);
  return results;
}
