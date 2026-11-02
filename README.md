# RescueOps: Autonomous Emergency Response and Rescue Mission Dispatcher

An autonomous multi-stage disaster response and rescue dispatch agent developed for the RescueOps Hackathon. 

RescueOps evaluates emergency crisis scenarios under severe physical and operational constraints—including adverse weather conditions, blocked roadways, restricted medical/personnel/fuel inventories, tight survival deadlines, and dynamic real-time text situation updates—to deliver safe, optimal, and auditable dispatch decisions.

---

## Team

- Akash
- Gokul
- Rohith

---

## Overview

In humanitarian and emergency rescue operations, command centers face high cognitive load when coordinating dispatch under rapidly deteriorating environments. Making sub-optimal decisions can result in stranded rescue units, depleted supplies, missed survival windows, or safety violations.

RescueOps implements a deterministic, multi-round decision agent designed to handle escalating operational complexities:
1. **Feasibility Validation**: Computing non-linear fuel requirements and weather-adjusted travel times.
2. **Dynamic Route Selection**: Navigating road blockages and evaluating alternate detour distances.
3. **Resource Allocation and Resupply Protocols**: Balancing multi-incident supply demands against warehouse stocks, triggering resupply protocols when missions are temporarily infeasible.
4. **Critical Incident Prioritization**: Multi-objective ranking across competing high-severity emergencies, urgency deadlines, and operational efficiency.
5. **Adaptive Intelligence**: Parsing unstructured real-time situation reports from field controllers, reconciling stale telemetry, and leveraging cloud LLM reasoning (via Ollama API) alongside heuristic NLP extractors.

The complete problem specification and scoring guidelines are documented in [RescueOps_PS_and_Agent_Guide_EN.pdf](file:///RescueOps_PS_and_Agent_Guide_EN.pdf).

---

## System Architecture

```
                  +-----------------------------------------+
                  |         Incoming Incident Case          |
                  |  (Weather, Resources, Missions, Report) |
                  +-----------------------------------------+
                                       |
                                       v
                          +-------------------------+
                          |   choose_rescue(case)   |
                          +-------------------------+
                                       |
             +------------+------------+------------+------------+
             |            |            |            |            |
             v            v            v            v            v
        [Round 1]    [Round 2]    [Round 3]    [Round 4]    [Round 5]
       Basic Rescue   Blocked      Resource     Critical     Adaptive
       Feasibility    Routes      Allocation   Priorities   Intelligence
             |            |            |            |            |
             |      Route Detour   Inventory    Multi-Item   NLP Report
             |      Verification   & Resupply   Ranking      Parser + LLM
             |            |            |            |            |
             +------------+------------+------------+------------+
                                       |
                                       v
                  +-----------------------------------------+
                  |            Safety & Feasibility         |
                  |     - Fuel Limit: ceil(dist / 10)       |
                  |     - Weather Time <= Deadline          |
                  |     - Medical Kits & Personnel Checks   |
                  +-----------------------------------------+
                                       |
                                       v
                  +-----------------------------------------+
                  |       Structured JSON Decision          |
                  |  action, priority, reason, mission_id,  |
                  |  uses_alternate_route, resource fields  |
                  +-----------------------------------------+
```

---

## Multi-Round Decision Logic

### Round 1: Basic Rescue Feasibility
- Evaluates a single rescue mission with clear weather and direct road access.
- **Fuel Calculation**: `fuel_needed = ceil(distance / 10)`
- **Travel Time**: `travel_time = ceil(distance * weather_factor)` where weather factors are:
  - Clear: 1.0
  - Rain: 1.25
  - Storm: 1.5
- **Feasibility Rule**: Dispatches if and only if `fuel_needed <= available_fuel`, `kits <= available_kits`, `personnel <= available_personnel`, and `travel_time <= deadline`. Otherwise, rejects.

### Round 2: Blocked Routes and Detours
- Handles incident locations where direct roads are blocked (`route_blocked: true`).
- Inspects whether an alternate route exists (`alternate_distance != null`).
- Evaluates detour travel time and fuel consumption. If feasible, executes action `reroute` with `uses_alternate_route: true`.
- If a route is blocked with no alternate available, rejects safely to prevent trapped dispatch units.

### Round 3: Constrained Resource Allocation and Resupply
- Manages 2 to 3 competing missions under severe inventory constraints.
- Identifies which missions can be serviced within current stock.
- If resources are insufficient to service any mission:
  - If `resupply_possible: true`, issues action `resupply` to request logistical replenishment.
  - If `resupply_possible: false`, issues action `reject`.

### Round 4: Emergency Prioritization
- Manages 3 to 5 simultaneous incidents with tight survival deadlines.
- Uses a multi-criteria priority sorting algorithm:
  1. **Severity Rating** (descending from 5 to 1; highest life-safety priority).
  2. **Deadline Urgency** (ascending; tightest deadline first).
  3. **Fuel Consumption** (ascending; most resource-efficient first).

### Round 5: Adaptive Intelligence and Control-Room NLP
- In later disaster stages, base telemetry becomes stale. The true situational updates arrive as free-text dispatch messages in `update_report`.
- Parses free-text updates for:
  - Weather shifts (e.g., transition to storm conditions).
  - Road conditions (e.g., newly obstructed routes and newly opened bypasses).
  - Dynamic inventory shifts (e.g., fuel down to 1, kits depleted).
- Reconciles scenario state and queries Ollama cloud models when credentials are provided.
- Re-evaluates mission feasibility against ground-truth updates to prevent hazardous dispatches.

---

## Decision Output Format

Every decision returned by the agent adheres to the following JSON specification:

```json
{
  "action": "dispatch",
  "priority": 4,
  "reason": "Mission M2 is feasible within resources and meets deadline",
  "mission_id": "M2",
  "uses_alternate_route": false,
  "fuel_needed": 1,
  "kits_needed": 1,
  "personnel_needed": 1
}
```

Allowed actions:
- `dispatch`: Deploy rescue team along the direct route.
- `reroute`: Deploy rescue team via the alternate route.
- `resupply`: Request emergency supply replenishment when inventory is depleted.
- `reject`: Safely decline an unachievable or hazardous mission.
- `wait`: Stand by when immediate execution is not viable.

---

## Repository Structure

```
Rescueops/
├── agent.py                            # Core decision agent and round solvers
├── app.py                              # Local validation runner and test harness
├── requirements.txt                    # Project Python dependencies
├── RescueOps_PS_and_Agent_Guide_EN.pdf # Official problem statement and rules
├── .env.example                        # Template for optional Ollama LLM credentials
├── .gitignore                          # Standard git ignore definitions
└── example/                            # Scenario test suites
    ├── expected_output_format.json
    ├── round_1_basic_rescue.json
    ├── round_2_blocked_routes.json
    ├── round_3_limited_resources.json
    ├── round_4_critical_priorities.json
    └── round_5_adaptive_rescueops.json
```

---

## Setup and Installation

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/gokulsanjayreddy/Rescueops.git
cd Rescueops
```

### 2. Set Up Virtual Environment

On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Optional: Configure Ollama API for Round 5
Rounds 1 through 4 run deterministically without external API dependencies. For Round 5 cloud LLM reasoning, configure your environment variables:

On Windows (PowerShell):
```powershell
$env:OLLAMA_API_KEY="your_api_key_here"
$env:OLLAMA_MODEL="your_model_name"
```

On Linux or macOS:
```bash
export OLLAMA_API_KEY="your_api_key_here"
export OLLAMA_MODEL="your_model_name"
```

To verify your Ollama API configuration:
```bash
python app.py --test-api
```

---

## Running the Verification Suite

Run the full local test suite against all 14 sample cases:

```bash
python app.py
```

Expected output:
```text
PASS r1_p1 / stage 0
PASS r1_p2 / stage 0
PASS r1_p3 / stage 0
PASS r2_p1 / stage 0
PASS r2_p2 / stage 0
PASS r2_p3 / stage 0
PASS r3_p1 / stage 0
PASS r3_p2 / stage 0
PASS r3_p3 / stage 0
PASS r4_p1 / stage 0
PASS r4_p2 / stage 0
PASS r4_p3 / stage 0
PASS r5_p1 / stage 0
PASS r5_p1 / stage 1
PASS r5_p2 / stage 0
PASS r5_p2 / stage 1

Summary: 14 case file(s), 0 failed stage(s).
```

### Testing Specific Rounds or Scenarios

Test a single round:
```bash
python app.py --round 3
```

Test a specific scenario and inspect inputs and decisions:
```bash
python app.py --case r2_p1 --show
```

Inspect all stages of Round 5:
```bash
python app.py --round 5 --show
```
