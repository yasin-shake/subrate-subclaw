# subclaw

A hybrid Instagram automation toolkit built on top of [OpenClaw](https://openclaw.dev) and [ClawPaw](https://clawpaw.dev). It drives a real Android device deterministically and falls back to an LLM agent for recovery whenever a UI checkpoint fails — a self-healing scrape loop.

## How it works

```
scrape_reels.py
  │
  ├── OpenClawClient  →  openclaw nodes invoke  →  Android device
  │        (click, swipe, get_layout, screenshot, input_text_direct…)
  │
  ├── checkpoints.py  →  verify-after-act assertions
  │        (assert_present, wait_for)
  │
  └── escalation.py  →  openclaw agent (LLM, thinking=high)
           on failure: snapshot layout + screenshot,
           ask the agent to recover the live UI and
           patch the relevant skill guide for future runs
```

**Happy path** runs purely deterministically — fast and cheap.  
**On checkpoint failure** the escalation agent takes over, inspects the live screen, drives the UI back to the expected state, and optionally patches the skill guide so the same failure doesn't happen again (self-healing).

## Project layout

```
subclaw/
├── automation/
│   ├── config.py             # All tuneable knobs (env-var overridable)
│   ├── openclaw_client.py    # Python wrapper around `openclaw nodes invoke`
│   ├── checkpoints.py        # verify-after-act helpers
│   ├── escalation.py         # LLM recovery hook
│   ├── scrape_reels.py       # Main reels scraper (CLI entry point)
│   └── runs/                 # Per-run artifacts: layouts, screenshots, CSVs
├── skill-guides/             # ClawPaw skill guide markdown files
│   ├── instagram-open.md
│   ├── instagram-search-keyword.md
│   ├── instagram-extract-reel-stats.md
│   ├── instagram-extract-post-stats.md
│   ├── instagram-scroll-feed.md
│   ├── instagram-like.md
│   ├── instagram-like-post.md
│   ├── instagram-comment-post.md
│   ├── instagram-follow-account.md
│   └── instagram-search-account.md
└── artifacts/                # Exploratory / reference captures
```

## Requirements

- Python 3.10+
- [`openclaw`](https://openclaw.dev) CLI available on `PATH`
- A ClawPaw Android node already registered with OpenClaw
- Instagram installed on the connected Android device

## Configuration

All settings live in `automation/config.py` and can be overridden with environment variables — no secrets in source.

| Env var | Default | Description |
|---|---|---|
| `OPENCLAW_NODE_ID` | *(see config.py)* | ClawPaw node identifier |
| `OPENCLAW_BIN` | `openclaw` | Path to the openclaw executable |
| `CLAWPAW_GUIDES_DIR` | `~/.openclaw/workspace/…/guides` | Where skill guides are read/patched |
| `OC_INVOKE_TIMEOUT_S` | `30` | Per-command timeout (seconds) |
| `OC_AGENT_TIMEOUT_S` | `600` | LLM escalation agent timeout (seconds) |
| `OC_AGENT_SESSION_ID` | `subclaw-recovery` | Persistent session id for the recovery agent |
| `OC_ESCALATE` | `1` | Set to `0` to disable LLM escalation (capture-only) |

## Usage

### Scrape Instagram Reels

```bash
cd automation
python scrape_reels.py --query "real estate uae" --count 10
```

Output is written to `automation/runs/<query>_<timestamp>/summary.csv`.

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--query` | *(required)* | Search term (spaces are fine — passed verbatim) |
| `--count` | `10` | Number of reels to scrape |
| `--out` | `runs/<query>_<ts>/summary.csv` | Custom CSV output path |

**CSV columns:** `post`, `username`, `likes`, `comments`, `caption`

### Exit codes

| Code | Meaning |
|---|---|
| `0` | All reels scraped successfully |
| `2` | Unrecovered checkpoint failure (see `fatal.xml` in the run dir) |

## Skill guides

The `skill-guides/` directory contains plain-markdown operating instructions for each Instagram action (element resource-ids, reliable tap strategies, known edge-cases). The LLM escalation agent reads and, when necessary, patches these guides in-place so that future deterministic runs incorporate the fix automatically.

## Architecture notes

- **No hard-coded coordinates.** Every tap target is computed from live element bounds returned by `get_layout`. This is the most important rule for avoiding drift across app updates.
- **Verify-after-act.** Every meaningful action is followed by a checkpoint (`wait_for` / `assert_present`). A failure surfaces immediately rather than silently corrupting data.
- **Python over PowerShell for subprocess.** `shell=False` with a list of args guarantees that `input_text_direct` payloads containing spaces reach the CLI verbatim, bypassing PowerShell argument mangling.
