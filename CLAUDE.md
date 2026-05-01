# Agent Instructions

You're working inside the **WAT framework** (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team

**Layer 2: Agents (The Decision-Maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself
- Example: If you need to pull data from a website, don't attempt it directly. Read `workflows/scrape_website.md`, figure out the required inputs, then execute `tools/scrape_single_site.py`

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` that do the actual work
- API calls, data transformations, file operations, database queries
- Credentials and API keys are stored in `.env`
- These scripts are consistent, testable, and fast

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

## How to Operate

**1. Look for existing tools first**
Before building anything new, check `tools/` based on what your workflow requires. Only create new scripts when nothing exists for that task.

**2. Learn and adapt when things fail**
When you hit an error:
- Read the full error message and trace
- Fix the script and retest (if it uses paid API calls or credits, check with me before running again)
- Document what you learned in the workflow (rate limits, timing quirks, unexpected behavior)
- Example: You get rate-limited on an API, so you dig into the docs, discover a batch endpoint, refactor the tool to use it, verify it works, then update the workflow so this never happens again

**3. Keep workflows current**
Workflows should evolve as you learn. When you find better methods, discover constraints, or encounter recurring issues, update the workflow. That said, don't create or overwrite workflows without asking unless I explicitly tell you to. These are your instructions and need to be preserved and refined, not tossed after one use.

## The Self-Improvement Loop

Every failure is a chance to make the system stronger:
1. Identify what broke
2. Fix the tool
3. Verify the fix works
4. Update the workflow with the new approach
5. Move on with a more robust system

This loop is how the framework improves over time.

## File Structure

**Directory layout:**
```
run.py                  # Flask entry point: python run.py
requirements.txt        # Flask, PyYAML, gunicorn
Containerfile           # Podman-compatible container build

tools/                  # Layer 3 — deterministic execution
  cluster_version.py    # Parse version.yaml → OCP version
  omc_runner.py         # OMC validation runner
  mustgather.py         # .tar.gz extraction, payload discovery
  reference_repo.py     # Git clone/cache telco-reference branches
  kube_compare.py       # Run kubectl cluster_compare subprocess
  dashboard_core.py     # Shared dashboard data processing + profile configs (RAN/CORE/HUB)
  html_renderer.py      # HTML report generation (self-contained, dark/light mode)
  md_renderer.py        # Markdown report generation

webapp/                 # Flask web application
  app.py                # App factory
  config.py             # Paths, defaults, env vars
  routes.py             # HTTP endpoints (upload, status, results, downloads)
  tasks.py              # Background pipeline execution (threading)
  models.py             # Job state tracking (in-memory, thread-safe)
  templates/            # Jinja2 templates (base, upload, status, results, error)
  static/style.css      # Upload/status page styles (dark/light theme)

workflows/              # Layer 1 — SOPs
  upload_and_analyze.md # Web upload flow SOP

CU/                     # Legacy vCU dashboard builder
DU/                     # Legacy vDU dashboard builder

.tmp/                   # Gitignored working directory
  uploads/              # Uploaded .tar.gz (deleted after extraction)
  jobs/<job-id>/        # Per-job workspace (extracted, reports, dashboards)
  reference-cache/      # Cached git clones (release-4.20/, etc.)

.env                    # API keys and environment variables
```

## Web Application

The webapp provides a browser-based interface for must-gather analysis:

1. User uploads a must-gather `.tar.gz` and selects a profile (RAN / CORE / HUB)
2. Pipeline auto-detects the OpenShift cluster version from `clusterversions/version.yaml`
3. Fetches the matching `release-{minor}` branch from `openshift-kni/telco-reference`
4. Runs `kubectl cluster_compare` against the profile-specific metadata.yaml
5. Runs OMC validation (if omc binary is available)
6. Generates HTML + Markdown compliance dashboards

**Run locally:** `pip install -r requirements.txt && python run.py` (port 5001)
**Container:** `podman build -t rds-webapp . && podman run -p 5001:5001 rds-webapp`

## Profile Metadata Paths

| Profile | Path within telco-reference |
|---------|----------------------------|
| RAN     | `telco-ran/configuration/kube-compare-reference/metadata.yaml` |
| CORE    | `telco-core/configuration/reference-crs-kube-compare/metadata.yaml` |
| HUB     | `telco-hub/configuration/reference-crs-kube-compare/metadata.yaml` |

Branch convention: `release-{minor_version}` (e.g., `release-4.20` for OCP 4.20.x)

## Bottom Line

You sit between what I want (workflows) and what actually gets done (tools). Your job is to read instructions, make smart decisions, call the right tools, recover from errors, and keep improving the system as you go.

Stay pragmatic. Stay reliable. Keep learning.
