# RescueOps — Participant Pack

> **Submission page:** http://10.50.20.214:5000
> (Open it in your browser. Your laptop must be on the **same network/WiFi** as the organizer. Submit **Round 1 first**, then Round 2, and so on.)

Build an agent that reads a rescue scenario and returns a safe, smart decision. You write the strategy in **`agent.py`**; the starter only shows the interface.

## Quick start (clone and run) 

You need **Git** and **Python 3.10+** installed.

```powershell
# 1. Get the project
cd $HOME\Downloads
git clone https://github.com/AdhiAgrawal0205/Rescueops.git

cd Rescueops
code .

# 2. Create and activate a virtual environment (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Check that everything works (runs all sample cases)
python app.py
```

macOS/Linux:
```bash
git clone https://github.com/AdhiAgrawal0205/Rescueops.git
cd Rescueops
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

If PowerShell blocks the activate script, run `Set-ExecutionPolicy -Scope Process Bypass` once in that window and try again.
If you pull updates later (the organizers may fix files), run `git pull` inside the `Rescueops` folder. Keep your own work in `agent.py`; if `git pull` complains about local changes, copy your `agent.py` somewhere safe first.

### What is in the repo

| File / folder | Purpose |
|---|---|
| `agent.py` | **Your work goes here.** The five round solvers and `choose_rescue(case)` |
| `app.py` | Local checker: runs the sample cases and prints ok/FAIL |
| `example/` | Example / sample data used for local testing |
| `requirements.txt` | Python dependencies |
| `RescueOps_Problem_Statement.pdf` | The official problem statement |
| `SUBMISSION_CHECKLIST.md` | Check this before you submit |

## The 5 rounds (100 points)
The competition has five rounds. **One `agent.py` is used for all of them**: the evaluator feeds your `choose_rescue(case)` cases from every round (the case has a `round` field), so build one agent that handles everything up to Round 5.

| Round | Points | What the scenario looks like | What your agent must handle |
|---|---|---|---|
| 1. Basic Rescue | 10 | One mission, clear weather, no blocked road | Is it feasible (fuel and deadline)? Dispatch or not |
| 2. Blocked Routes | 15 | 1-2 missions, `route_blocked` and `alternate_distance` appear | Never use a blocked road; consider the alternate route (it may not exist) |
| 3. Limited Resources | 20 | 2-3 missions, fuel / kits / personnel are limited, `resupply_possible` may be true | Resource checks; what to do when nothing fits |
| 4. Critical Priorities | 25 | 3-5 missions with tight deadlines | Choose well between competing missions (severity vs feasibility) |
| 5. Adaptive RescueOps | 30 | Everything combined. Weather can change and later stages bring a free-text `update_report` | Read the report, update the scenario, decide again. **Needs an Ollama call** (see section 6b) |

Each later round **includes everything from the earlier ones**, so Round 1 logic must still work in Round 5.

## Where to start (step by step)
1. Do the **Quick start** above (clone, venv, install).
2. Read sections 3 and 4 below (the scenario and the decision you return).
3. Open `agent.py`, write the 3 tools (`check_route`, `check_resources`, `check_deadline`) as LangChain `@tool`s.
4. Build a small LangGraph in `build_graph()` that calls the tools and returns a decision. Get **Round 1** passing first, then add blocked routes (R2), resources and many missions (R3-R4).
5. Test with the sample cases. They are named by round: `r1_p1, r1_p2, ... r5_p1, r5_p2`.
   `python app.py --case r2_p1 --show` runs one case and prints the scenario and your decision.
6. Last: Round 5. Add `parse_update_report`, set your Ollama key, run `python app.py --test-api`, then test `r5_p1`.
7. Submit on the page the organizers give you (section 7). No key? Submit R1-R4 and skip R5.

## 2. Where to write code
`agent.py` has **five independent round solvers**: `solve_round1` ... `solve_round5`. Each one has its own tools, its own LangGraph and its own decision logic, and none of them calls another round's code, so changing one round can never break another. `choose_rescue(case)` only reads `case["round"]` and calls the matching solver. (Tool names stay exactly `check_route`, `check_resources`, `check_deadline`, `parse_update_report`: each round defines its own copy inside its `_buildN()` function.)

Rework a round by editing only its block (`_build_round3()` / `solve_round3()` etc.). The starter only contains function definitions. **You** write the agent with LangGraph + LangChain: make the 4 `@tool` functions (`check_route`, `check_resources`, `check_deadline`, `parse_update_report`), build your own graph in `build_graph()` and return its decision from `choose_rescue`. `call_ollama()` (via `requests`) is provided; the key/model are read from environment variables only, never from code.

## 3. The scenario (`case`)
```
case_id, round, stage, weather ("clear"|"rain"|"storm"), resupply_possible (bool),
resources: {fuel, kits, personnel},
missions: [{id, severity 1-5, distance, deadline, kits, personnel, route_blocked, alternate_distance|null}]
update_notice (round 5, stage > 0)
```
Rules: one mission per decision. fuel needed = ceil(route km ÷ 10). Travel time = ceil(km × weather factor: clear 1.0, rain 1.25, storm 1.5) and must be ≤ `deadline`. A blocked direct route can't be used; use the alternate route (`alternate_distance`, if not null) by returning `uses_alternate_route: true` (or action `reroute`). Round 5 calls your agent once per stage; each call must reflect the *current* state.

## 4. The decision you return
```json
{"action": "dispatch", "priority": 4, "reason": "Mission is urgent and feasible",
 "mission_id": "M1", "uses_alternate_route": false,
 "fuel_needed": 2, "kits_needed": 1, "personnel_needed": 1}
```
- **Required:** `action` (`dispatch`, `wait`, `reroute`, `reject`, `resupply`), `priority` (int 1–5), `reason` (non-empty text).
- **Optional:** `mission_id` (required for dispatch/reroute if the case has more than one mission), `uses_alternate_route` (bool), `fuel_needed`, `kits_needed`, `personnel_needed` (non-negative ints).
- Resource numbers you claim are **checked, not trusted**.
- **Tool usage:** the evaluator sees which of your LangChain tools are actually *invoked* (`check_route`, `check_resources`, `check_deadline`, plus `parse_update_report` when an `update_report` exists).
- **How the decision part is scored (summary):** malformed output, crashes and timeouts earn 0 for that case. Unsafe dispatches (blocked route, not enough resources, missed deadline) earn 0 and count as safety violations — fewer violations break ties. Safe, feasible, high-severity choices earn the most; doing nothing when a feasible rescue exists earns little; correctly refusing/waiting/resupplying when nothing is feasible earns well. Pretty prose is worth nothing. Rounds are worth 10 / 15 / 20 / 25 / 30 = 100 points. Hidden test cases differ from the samples, so hard-coded answers will fail.

## 5. Test locally
```powershell
python app.py              # all sample cases, prints ok/FAIL
python app.py --case r2_p1 --show
```
The checker verifies format and hard safety rules only; it does not give your competition score.

## 6. Optional: Ollama cloud LLM
1. Create an API key in your Ollama account and look at the cloud models your account can use (account page / model list). Don't assume a model name is available.
2. Set variables in the same PowerShell window (never in code):
```powershell
$env:OLLAMA_API_KEY="your_key_here"
$env:OLLAMA_MODEL="your_available_model"
```
macOS/Linux: `export OLLAMA_API_KEY="..."` and `export OLLAMA_MODEL="..."`.
3. Check the setup: `python app.py --test-api`
4. Use `ask_ollama(case)` inside `choose_rescue`. It calls `https://ollama.com/v1/chat/completions`, never prints your key, returns `None` on missing key/model, HTTP 401/403/404/429, timeouts, network errors or malformed replies, and returns only a structurally valid decision. **You must still verify the answer against the case** (blocked route? resources? deadline?) and fall back to your own logic.
Rounds 1-4 run without your key; your agent must work without the LLM there. For Round 5 see 6b.

## 6b. ROUND 5 needs Ollama (mandatory for Round 5)
- Round 5 is worth 30 points. In its later stages the scenario fields are **stale**; the real changes come only as free text in `case["update_report"]`, e.g. `"Weather is now storm. Route to M2 is now blocked. Fuel is now 4."`. Your decision is scored against the updated truth.
- **Each Round 5 case scores 0 unless your agent makes at least one successful Ollama call** (HTTP 200 to `ollama.com`) while handling that case. Use `ask_ollama` from `agent.py` or the `requests` library (other libraries are not counted). Failed calls (bad key, wrong model, rate limit) don't count, so test with `python app.py --test-api` first.
- You enter your own Ollama API key and model name in the submit form for Round 5. It is used only for that run and is not stored. Your code must **never** contain the key. Use a limited or throwaway key and revoke it afterwards.
- Rounds 1-4 can be submitted without any key.
- Use the LLM to read the report, then double-check its answer yourself (blocked route? resources? deadline?). An invalid LLM answer scores 0 for that stage.

## 7. Package and submit (round by round)
Submissions go **one round at a time, in order**: submit **Round 1** first, then **Round 2**, then 3, 4 and 5. A round unlocks after the previous one is submitted. The page shows which round is next once you type your team name. You can resubmit any round; the organizers keep your best result for each round, and your total is the sum of your best rounds. Round 5 asks for your Ollama key + model; Rounds 1-4 need no key.

Open the submission page (**http://10.50.20.214:5000**), enter your team name, upload the file, pick the round and press **Submit**. **Scores are not shown to participants**; the organizers will announce the results. You cannot  submit again.

Submit `.py` format , or a ZIP (`Compress-Archive -Path agent.py -DestinationPath my_team.zip`; add helper files if you import them). See `SUBMISSION_CHECKLIST.md`.

**Never include:** API keys, `.env`, tokens, `.venv`, `__pycache__`, big data files, or anything copied from another team. Submissions containing key files or hard-coded keys are rejected.
