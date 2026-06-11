# Social research for daily_single (last30days)

Use **[last30days-skill](https://github.com/mvanhorn/last30days-skill)** before script edits when you need viral angles, quotes, and gap analysis from X, Reddit, HN, YouTube — not stale LinkedIn profiles.

Local clone: `/Users/praison/last30days-skill`  
Engine: `skills/last30days/scripts/last30days.py`

## Platform coverage

| Platform | last30days | Notes |
|----------|------------|--------|
| **Reddit** | Yes (always on) | `--subreddits=ClaudeAI,LocalLLaMA,singularity,vibecoding` |
| **X / Twitter** | Yes | Browser cookies (`FROM_BROWSER=firefox`) or `XAI_API_KEY` or `AUTH_TOKEN`+`CT0` |
| **LinkedIn** | **No** | Use WebSearch / manual roundup links; cite posts in script only when URL verified |
| **Hacker News** | Yes | Strong for launch threads (e.g. 2,543 pts on Fable announcement) |
| **YouTube** | Yes | `yt-dlp` or ScrapeCreators |
| **GitHub** | Yes | `--github-repo=anthropics/claude-code` |

## Install (Cursor)

```bash
npx skills add mvanhorn/last30days-skill -g -a cursor
# or symlink dev clone:
ln -sfn /Users/praison/last30days-skill/skills/last30days ~/.agents/skills/last30days
```

Project-local keys (optional): `praisonaippt/.claude/last30days.env`

## Fable 5 query (recommended)

```bash
SKILL=/Users/praison/last30days-skill/skills/last30days

python3 "$SKILL/scripts/last30days.py" \
  "Anthropic Claude Fable 5 launch reaction" \
  --emit=compact \
  --days=30 \
  --deep \
  --x-handle=AnthropicAI \
  --subreddits=ClaudeAI,LocalLLaMA,singularity,vibecoding,ClaudeCode \
  --github-repo=anthropics/claude-code \
  --save-dir="$HOME/Documents/Last30Days" \
  --save-suffix=fable5
```

Slash command in Cursor (after skill install):

```
/last30days Anthropic Claude Fable 5 launch --deep
/last30days Claude Fable 5 vs Mythos 5 Reddit reaction
```

## Enable X on this Mac

```bash
python3 .../last30days.py --diagnose
```

If `bird_authenticated: false`:

1. Log into x.com in **Firefox** (or Safari with Full Disk Access for Terminal), re-run; or  
2. Add `XAI_API_KEY` to `~/.config/last30days/.env`; or  
3. Export `AUTH_TOKEN` + `CT0` from browser dev tools.

Without X, Reddit + HN still work (verified on Fable pilot).

## LinkedIn workaround

1. WebSearch: `Charly Wargnier Claude Fable 5 LinkedIn roundup` (verify URL before script).  
2. Manual: open target profile → copy post URL + engagement into `research/<slug>/social-notes.md`.  
3. Do **not** invent “26M views” or roundup titles without a primary link.

## Multi-agent workflow (gap analysis)

| Step | Agent | Task |
|------|-------|------|
| 1 | `explore` | Read `last30days` SKILL + `--diagnose`; list enabled sources |
| 2 | Parent | Run `last30days.py` with `--deep`; save raw to `~/Documents/Last30Days/` |
| 3 | `generalPurpose` | WebSearch: press + Latent Space + Simon Willison + controversy angles |
| 4 | `explore` | Read `segments/*/script.md`; table theme vs covered (Y/partial/N) |
| 5 | Parent | Pick top 3–5 lines for beats; re-run `synthesise-vo` only for changed segments |

## Map findings → video beats (Fable pilot)

| Viral theme | Beat | Hook line (example) |
|-------------|------|---------------------|
| r/ClaudeAI “AI inequality” (5k+ score) | 02-mythos-tier | “Same weights — not the same access.” |
| RSI essay 4 Jun → ship 9 Jun | 00-hook or 06 | “Five days after the pause essay, Fable went public.” |
| Simon Willison $110 on $100 Max | 09-pricing | “One power user burned a month’s plan in a day.” |
| Karpathy / Cherny coding quotes | 03-engineers-care | “Major-version-bump tasks — not chat prompts.” |
| Guardrail memes (heart / cancer false positives) | 06-safeguards | “When biology checks misfire on homework questions.” |
| Mythos-only drug-design headlines | 02 or 08 | “The Science headlines are Mythos — not your Pro seat.” |
| Andon Vending-Bench scepticism | 10-alignment | “Leaderboard wins vs real-world profit — check both.” |
| Microsoft internal block (retention) | 07-api-integration | “Even partners debate the thirty-day prompt log.” |

## After script changes

Follow [spoken-visual-sync.md](spoken-visual-sync.md): `build-captions` → `assemble-beats` → `validate-spoken-visual`.

## Raw output location

Default: `~/Documents/Last30Days/<slug>-raw*.md`  
Engagement in clusters: `[2,543pts, 2,073cmt]`, Reddit `(score:N)`.

Filter for viral: use `--deep`, `FUN_LEVEL=high` in `.env`, prioritise cross-source clusters (Reddit + X + HN same story).

## Pilot projects

| Project | Role |
|---------|------|
| `examples/videos/anthropic-claude-fable-5-mythos-5/` | Video 1 — official explainer (published) |
| `examples/videos/anthropic-claude-fable-5-trust-audit/` | Video 2 — gap report, comparison cards, X formats (`research/GAP-REPORT.md`) |
