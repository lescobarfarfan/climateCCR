---
description: Package the canon to return to the claude.ai project workflow (rollback)
disable-model-invocation: true
---

Generate a return-to-claude.ai handoff bundle. This is the rollback path if I
decide Claude Code isn't for me. Because the canon is plain markdown in git, the
return is non-destructive — this command just packages it and writes instructions.

1. **Pre-flight.** Confirm the working tree is clean (`git status`) and suggest I
   run `/link-check` first so the exported canon is consistent. If there are
   uncommitted changes, tell me to `/digest` (or commit) before exporting.

2. **Build the bundle.** Create `handoff/claude_ai_project_knowledge/` and copy
   into it the exact files a fresh claude.ai Project needs as knowledge:
   - all of `context/*.md`
   - the vault hubs: `_INDEX.md`, `CCR_MOC.md`, `MKT_MOC.md`, `HAZ_MOC.md`
   - the repo docs: `README.md`, `REPO_STRUCTURE.md`, `ASSET_MAP.md`,
     `OBSIDIAN_SETUP.md`, `CONSOLIDATION_PLAN.md`
   Then zip it to `handoff/climateCCR_canon_<YYYY-MM-DD>.zip`.

3. **Write `handoff/RETURN_TO_CLAUDE_AI.md`** with step-by-step instructions:
   - Create a new claude.ai Project (one project — chat search is project-scoped).
   - Upload the bundle files to Project knowledge (or connect the GitHub repo so
     the canon is read directly; the repo is the source of truth either way).
   - Resume the original workflow: warm-start by pointing Claude at `context/`,
     and run the end-of-chat ritual from `WORKFLOW.md` §2 — noting that in the
     claude.ai project the canon is **read-only**, so the ritual ends with
     download-and-replace of the `context/` files (the friction Claude Code
     removed). The `/warmstart` and `/digest` slash commands do not exist there;
     ask for the recap and the digest in prose instead.
   - Keep the repo on GitHub; nothing is lost — you can switch back to Claude Code
     anytime by reopening the repo and running `/warmstart`.

4. Add `handoff/` to `.gitignore` (it's a generated export), or commit it if I
   want the bundle versioned — ask me which.

Show me the file list and `RETURN_TO_CLAUDE_AI.md` before writing. Then create them.
