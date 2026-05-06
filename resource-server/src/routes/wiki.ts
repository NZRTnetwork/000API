import { Router } from "express";
import { readNote, searchVault } from "../lib/vault.js";

const router = Router();

// GET /wiki/:section/:file
// section may contain subdirectories — encoded as URL segments
router.get("/:section/:file", (req, res) => {
  try {
    const section = decodeURIComponent(req.params.section);
    const file = decodeURIComponent(req.params.file);
    const content = readNote(section, file);
    res.json({ section, file, content });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unknown error";
    const status = message.includes("not found") ? 404 : 400;
    res.status(status).json({ error: message });
  }
});

// GET /wiki/search?q=<query>
router.get("/search", (req, res) => {
  const q = req.query.q as string;
  if (!q || q.trim().length === 0) {
    res.status(400).json({ error: "Missing query param: q" });
    return;
  }
  try {
    const results = searchVault(q.trim());
    res.json({ query: q, results });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unknown error";
    res.status(500).json({ error: message });
  }
});

export default router;
