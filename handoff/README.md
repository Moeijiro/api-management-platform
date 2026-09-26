# StudyRaid + portfolio redesign: publishing

This session could not create `Moeijiro/studyraid` or push to `Moeijiro/portfolio`
(GitHub returned 403: the Claude GitHub App isn't installed on those repositories).
The finished work is in this folder as git bundles, which keep the exact commits,
authors and IDs. The StudyRaid code excerpt on the portfolio links to commit
`a894589`, so publish the bundle as-is rather than re-committing the files.

| File | Contents |
|---|---|
| `studyraid.bundle` | The complete `studyraid` repository (branch `main`, commit `a894589`) |
| `portfolio-redesign.bundle` | One commit (`c57da41`) on top of `portfolio` `main` (`d740548`) |
| `portfolio-redesign.patch` | The same portfolio commit as a readable patch (`git am`-compatible) |

## 1. Publish StudyRaid (do this first; the portfolio links to it)

Create an **empty public** repository named `studyraid` on GitHub (no README, licence or
.gitignore), then:

```bash
git clone studyraid.bundle studyraid
cd studyraid
git remote set-url origin https://github.com/Moeijiro/studyraid.git
git push -u origin main
```

Suggested repository description: *Gamified study platform: homework becomes quests with
XP, levels, streaks, focus sessions and party challenges. FastAPI + Next.js.*
Suggested topics: `fastapi`, `nextjs`, `python`, `typescript`, `websockets`, `gamification`,
`sqlalchemy`, `postgresql`. To use the social image, upload
`portfolio/public/og/studyraid.png` under Settings → Social preview.

## 2. Publish the portfolio redesign

```bash
cd portfolio            # your existing clone, on an up-to-date main
git fetch /path/to/portfolio-redesign.bundle claude/studyraid-portfolio-project-5d49eh:redesign
git checkout redesign   # review it, or open a PR from this branch
git checkout main && git merge --ff-only redesign && git push
```

Pushing to `main` runs the existing workflow (lint → static export → GitHub Pages).

## Alternative: let Claude push

Install the Claude GitHub App on `Moeijiro/portfolio` and the new `Moeijiro/studyraid`
(https://github.com/apps/claude/installations/select_target) and ask again. Both
branches are ready to push unchanged.

## What was verified before handing off

- StudyRaid backend: 115 tests pass on SQLite and on PostgreSQL 16; Ruff lint and format clean;
  `alembic upgrade head` + `alembic check` report no drift on both databases.
- StudyRaid frontend: ESLint, `tsc --noEmit` and `next build` clean; every page checked for
  horizontal overflow at 375, 768 and 1440 px; browser flows exercised (complete a quest,
  level-up, create a quest, focus session, notifications, live party update from a second user).
- `docker compose up` (PostgreSQL) built and ran; the API migrated and seeded, and the web app
  served the same demo.
- Portfolio: `npm run lint`, `tsc` and `npm run build` clean (static export, `BASE_PATH=/portfolio`);
  the export served under `/portfolio/` with all 204 internal URLs and assets resolving; the 22
  pages have no horizontal overflow at 375, 768 and 1440 px; filters, deep links, the mobile menu
  and the skip link all work; every pinned code-excerpt commit exists in its repository.
