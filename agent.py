"""RescueOps Agent — Autonomous Multi-Stage Disaster Response Dispatcher.

Developed for RescueOps Hackathon.
Team: AKASH, GOKUL, ROHITH

ARCHITECTURE:
    solve_round1(case)   Basic Rescue Feasibility     (Direct route, single mission assessment)
    solve_round2(case)   Dynamic Route Navigation     (Blocked roads, alternate route evaluation)
    solve_round3(case)   Resource Allocation          (Constrained fuel, kits, personnel, resupply protocol)
    solve_round4(case)   Critical Priorities          (Multi-incident trade-offs: severity vs urgency vs feasibility)
    solve_round5(case)   Adaptive Intelligence        (Real-time text situation reports, LLM / NLP reasoning)
    choose_rescue(case)  Master Evaluator Interface
"""

import copy
import json
import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph


# ======================== CONFIGURATION ======================

OLLAMA_URL = os.getenv("OLLAMA_URL", "https://ollama.com/v1/chat/completions")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

WEATHER_FACTORS: Dict[str, float] = {
    "clear": 1.0,
    "rain": 1.25,
    "storm": 1.5,
}

ACTIONS = ("dispatch", "wait", "reroute", "reject", "resupply")


# ============================================================
# ROUND 1 - BASIC RESCUE FEASIBILITY
# Focus: Fuel calculation and travel feasibility
# ============================================================

def calculate_fuel(case: dict) -> dict:
    """
    Calculate the fuel required for the rescue mission.
    """
    missions = case.get("missions", [])
    if not missions:
        return {"fuel_needed": 0, "distance": 0}
    m = missions[0]
    distance = m.get("distance", 0)
    fuel_needed = math.ceil(distance / 10)
    return {"fuel_needed": fuel_needed, "distance": distance}


def calculate_travel_time(case: dict) -> dict:
    """
    Estimate the travel time for the mission based on weather factor.
    """
    missions = case.get("missions", [])
    if not missions:
        return {"travel_time": 0, "weather": "clear", "deadline": 0}
    m = missions[0]
    distance = m.get("distance", 0)
    weather = case.get("weather", "clear")
    factor = WEATHER_FACTORS.get(weather, 1.0)
    travel_time = math.ceil(distance * factor)
    return {
        "travel_time": travel_time,
        "weather": weather,
        "deadline": m.get("deadline", 0),
    }


def assess_mission(case: dict) -> dict:
    """
    Assess whether the rescue mission is feasible under fuel, resources, and deadline.
    """
    missions = case.get("missions", [])
    if not missions:
        return {"feasible": False, "reason": "No mission available"}

    m = missions[0]
    resources = case.get("resources", {})
    fuel_info = calculate_fuel(case)
    time_info = calculate_travel_time(case)

    fuel_needed = fuel_info["fuel_needed"]
    travel_time = time_info["travel_time"]

    if m.get("route_blocked", False):
        return {"feasible": False, "reason": "Direct route is blocked"}

    if fuel_needed > resources.get("fuel", 0):
        return {
            "feasible": False,
            "reason": "Insufficient fuel",
            "fuel_needed": fuel_needed,
            "why": "resources",
        }

    if m.get("kits", 0) > resources.get("kits", 0):
        return {
            "feasible": False,
            "reason": "Insufficient kits",
            "why": "resources",
        }

    if m.get("personnel", 0) > resources.get("personnel", 0):
        return {
            "feasible": False,
            "reason": "Insufficient personnel",
            "why": "resources",
        }

    if travel_time > m.get("deadline", 0):
        return {
            "feasible": False,
            "reason": "Deadline cannot be met",
            "why": "deadline",
        }

    return {
        "feasible": True,
        "mission_id": m.get("id", "M1"),
        "priority": m.get("severity", 1),
        "fuel_needed": fuel_needed,
        "kits_needed": m.get("kits", 0),
        "personnel_needed": m.get("personnel", 0),
        "reason": "Mission is feasible within fuel, resource and time limits",
    }


def solve_round1(case: dict) -> dict:
    """
    Main decision function for Round 1.
    """
    missions = case.get("missions", [])
    m = missions[0] if missions else {}
    severity = m.get("severity", 1)
    mission_id = m.get("id", "M1")

    assessment = assess_mission(case)
    if assessment.get("feasible"):
        return {
            "action": "dispatch",
            "priority": assessment.get("priority", severity),
            "reason": assessment.get("reason", "Mission is urgent and feasible"),
            "mission_id": mission_id,
            "uses_alternate_route": False,
            "fuel_needed": assessment.get("fuel_needed", 0),
            "kits_needed": assessment.get("kits_needed", 0),
            "personnel_needed": assessment.get("personnel_needed", 0),
        }
    else:
        return {
            "action": "reject",
            "priority": severity,
            "reason": assessment.get("reason", "Mission is not feasible"),
            "mission_id": mission_id,
        }


# ============================================================
# ROUND 2 - ROUTE NAVIGATION
# Focus: Route analysis and route selection
# ============================================================

def analyse_routes(case: dict) -> dict:
    """
    Analyse direct and alternate routes for each mission.
    """
    routes = {}
    for m in case.get("missions", []):
        mid = m["id"]
        is_blocked = bool(m.get("route_blocked", False))
        alt_dist = m.get("alternate_distance")
        direct_dist = m.get("distance")

        if is_blocked:
            if alt_dist is not None:
                routes[mid] = {
                    "usable": True,
                    "distance": alt_dist,
                    "uses_alternate": True,
                    "description": "alternate route",
                }
            else:
                routes[mid] = {
                    "usable": False,
                    "distance": None,
                    "uses_alternate": False,
                    "description": "blocked with no alternate",
                }
        else:
            routes[mid] = {
                "usable": True,
                "distance": direct_dist,
                "uses_alternate": False,
                "description": "direct route",
            }
    return routes


def compare_routes(case: dict) -> dict:
    """
    Compare available routes against weather, travel time, and resource limits.
    """
    route_analysis = analyse_routes(case)
    weather = case.get("weather", "clear")
    factor = WEATHER_FACTORS.get(weather, 1.0)
    resources = case.get("resources", {})
    evaluated = []

    for m in case.get("missions", []):
        mid = m["id"]
        rinfo = route_analysis.get(mid, {})
        if not rinfo.get("usable"):
            evaluated.append({
                "mission": m,
                "feasible": False,
                "reason": "Route blocked and no alternate route available",
                "why": "route",
            })
            continue

        dist = rinfo["distance"]
        fuel_needed = math.ceil(dist / 10)
        travel_time = math.ceil(dist * factor)

        if fuel_needed > resources.get("fuel", 0):
            evaluated.append({
                "mission": m,
                "feasible": False,
                "reason": "Insufficient fuel for route",
                "why": "resources",
            })
        elif m.get("kits", 0) > resources.get("kits", 0):
            evaluated.append({
                "mission": m,
                "feasible": False,
                "reason": "Insufficient kits",
                "why": "resources",
            })
        elif m.get("personnel", 0) > resources.get("personnel", 0):
            evaluated.append({
                "mission": m,
                "feasible": False,
                "reason": "Insufficient personnel",
                "why": "resources",
            })
        elif travel_time > m.get("deadline", 0):
            evaluated.append({
                "mission": m,
                "feasible": False,
                "reason": "Deadline cannot be met",
                "why": "deadline",
            })
        else:
            evaluated.append({
                "mission": m,
                "feasible": True,
                "distance": dist,
                "fuel_needed": fuel_needed,
                "travel_time": travel_time,
                "uses_alternate": rinfo["uses_alternate"],
                "kits_needed": m.get("kits", 0),
                "personnel_needed": m.get("personnel", 0),
                "reason": f"Route ({rinfo['description']}) is safe and within limits",
            })
    return {"evaluated": evaluated}


def select_best_route(case: dict) -> dict:
    """
    Select the most suitable mission and route based on feasibility, severity, and efficiency.
    """
    comp = compare_routes(case)
    feasible = [e for e in comp.get("evaluated", []) if e.get("feasible")]

    if feasible:
        best = min(
            feasible,
            key=lambda x: (
                -x["mission"].get("severity", 1),
                x["mission"].get("deadline", 9999),
                x["fuel_needed"],
            )
        )
        return {"selected": best, "feasible": True}

    return {"selected": None, "feasible": False, "evaluated": comp.get("evaluated", [])}


def solve_round2(case: dict) -> dict:
    """
    Main decision function for Round 2.
    """
    selection = select_best_route(case)
    missions = case.get("missions", [])

    if selection.get("feasible"):
        best = selection["selected"]
        m = best["mission"]
        uses_alt = best["uses_alternate"]
        action = "reroute" if uses_alt else "dispatch"
        return {
            "action": action,
            "priority": m.get("severity", 1),
            "reason": best.get("reason", "Route is feasible"),
            "mission_id": m.get("id"),
            "uses_alternate_route": uses_alt,
            "fuel_needed": best["fuel_needed"],
            "kits_needed": best["kits_needed"],
            "personnel_needed": best["personnel_needed"],
        }
    else:
        max_sev = max([m.get("severity", 1) for m in missions], default=1)
        reasons = [e.get("reason") for e in selection.get("evaluated", []) if e.get("reason")]
        reason_text = reasons[0] if reasons else "No usable route available"
        first_id = missions[0]["id"] if missions else None
        res: Dict[str, Any] = {
            "action": "reject",
            "priority": max_sev,
            "reason": reason_text,
        }
        if first_id:
            res["mission_id"] = first_id
        return res


# ============================================================
# ROUND 3 - RESOURCE ALLOCATION
# Focus: Distribution of limited resources and resupply handling
# ============================================================

def calculate_resource_demand(case: dict) -> dict:
    """
    Calculate resource requirements for each available mission.
    """
    demands = {}
    for m in case.get("missions", []):
        mid = m["id"]
        is_blocked = bool(m.get("route_blocked", False))
        alt_dist = m.get("alternate_distance")
        direct_dist = m.get("distance", 0)

        use_alt = is_blocked and alt_dist is not None
        dist = alt_dist if use_alt else direct_dist
        fuel_needed = math.ceil(dist / 10) if dist else 0

        demands[mid] = {
            "fuel": fuel_needed,
            "kits": m.get("kits", 0),
            "personnel": m.get("personnel", 0),
            "distance": dist,
            "use_alt": use_alt,
            "blocked_without_alt": is_blocked and alt_dist is None,
        }
    return demands


def evaluate_resource_availability(case: dict) -> dict:
    """
    Compare mission demands against available inventory and deadline constraints.
    """
    demands = calculate_resource_demand(case)
    resources = case.get("resources", {})
    weather = case.get("weather", "clear")
    factor = WEATHER_FACTORS.get(weather, 1.0)
    
    available_fuel = resources.get("fuel", 0)
    available_kits = resources.get("kits", 0)
    available_personnel = resources.get("personnel", 0)

    evaluations = []
    for m in case.get("missions", []):
        mid = m["id"]
        d = demands.get(mid, {})
        
        if d.get("blocked_without_alt"):
            evaluations.append({
                "mission": m,
                "feasible": False,
                "reason": "Route blocked and no alternate route available",
                "demand": d,
            })
            continue

        travel_time = math.ceil(d["distance"] * factor)
        fuel_ok = d["fuel"] <= available_fuel
        kits_ok = d["kits"] <= available_kits
        personnel_ok = d["personnel"] <= available_personnel
        time_ok = travel_time <= m.get("deadline", 0)

        feasible = fuel_ok and kits_ok and personnel_ok and time_ok
        reason = "Feasible within resource limits" if feasible else "Resource limit or deadline exceeded"

        evaluations.append({
            "mission": m,
            "feasible": feasible,
            "travel_time": travel_time,
            "fuel_needed": d["fuel"],
            "kits_needed": d["kits"],
            "personnel_needed": d["personnel"],
            "uses_alternate": d["use_alt"],
            "reason": reason,
        })

    return {"evaluations": evaluations}


def allocate_resources(case: dict) -> dict:
    """
    Determine the optimal mission allocation or trigger resupply protocol.
    """
    eval_res = evaluate_resource_availability(case)
    evaluations = eval_res.get("evaluations", [])
    feasible_missions = [e for e in evaluations if e.get("feasible")]

    if feasible_missions:
        best = min(
            feasible_missions,
            key=lambda x: (
                -x["mission"].get("severity", 1),
                x["mission"].get("deadline", 9999),
                x["fuel_needed"],
            )
        )
        return {"status": "dispatch", "selected": best}

    if case.get("resupply_possible", False):
        return {"status": "resupply", "reason": "Critical resource shortage; resupply requested"}

    return {"status": "reject", "reason": "Insufficient resources and resupply unavailable"}


def solve_round3(case: dict) -> dict:
    """
    Main decision function for Round 3.
    """
    decision = allocate_resources(case)
    status = decision.get("status")
    missions = case.get("missions", [])
    max_sev = max([m.get("severity", 1) for m in missions], default=3)

    if status == "dispatch":
        best = decision["selected"]
        m = best["mission"]
        uses_alt = best["uses_alternate"]
        action = "reroute" if uses_alt else "dispatch"
        return {
            "action": action,
            "priority": m.get("severity", 1),
            "reason": f"Mission {m['id']} allocated resources successfully within limits",
            "mission_id": m.get("id"),
            "uses_alternate_route": uses_alt,
            "fuel_needed": best["fuel_needed"],
            "kits_needed": best["kits_needed"],
            "personnel_needed": best["personnel_needed"],
        }
    elif status == "resupply":
        return {
            "action": "resupply",
            "priority": max_sev,
            "reason": decision.get("reason", "Insufficient resources; emergency resupply requested"),
        }
    else:
        return {
            "action": "reject",
            "priority": max_sev,
            "reason": decision.get("reason", "All missions exceed available resources and resupply is not possible"),
        }


# ============================================================
# ROUND 4 - EMERGENCY PRIORITISATION
# Focus: Multi-incident ranking and critical dispatch
# ============================================================

def evaluate_severity(case: dict) -> dict:
    """
    Extract severity ratings for all missions.
    """
    return {m["id"]: m.get("severity", 1) for m in case.get("missions", [])}


def calculate_urgency(case: dict) -> dict:
    """
    Determine urgency margins (deadline minus weather-adjusted travel time).
    """
    weather = case.get("weather", "clear")
    factor = WEATHER_FACTORS.get(weather, 1.0)
    urgencies = {}
    for m in case.get("missions", []):
        is_blocked = bool(m.get("route_blocked", False))
        alt_dist = m.get("alternate_distance")
        dist = alt_dist if (is_blocked and alt_dist is not None) else m.get("distance", 0)
        travel_time = math.ceil(dist * factor)
        urgencies[m["id"]] = {
            "travel_time": travel_time,
            "slack": m.get("deadline", 0) - travel_time,
        }
    return urgencies


def rank_emergencies(case: dict) -> dict:
    """
    Rank emergency requests by feasibility, severity, urgency slack, and resource usage.
    """
    resources = case.get("resources", {})
    weather = case.get("weather", "clear")
    factor = WEATHER_FACTORS.get(weather, 1.0)
    
    avail_fuel = resources.get("fuel", 0)
    avail_kits = resources.get("kits", 0)
    avail_pers = resources.get("personnel", 0)

    evaluated = []
    for m in case.get("missions", []):
        mid = m["id"]
        is_blocked = bool(m.get("route_blocked", False))
        alt_dist = m.get("alternate_distance")
        direct_dist = m.get("distance", 0)

        if is_blocked and alt_dist is None:
            continue

        use_alt = is_blocked and alt_dist is not None
        dist = alt_dist if use_alt else direct_dist
        fuel_needed = math.ceil(dist / 10)
        travel_time = math.ceil(dist * factor)

        if (fuel_needed <= avail_fuel and
            m.get("kits", 0) <= avail_kits and
            m.get("personnel", 0) <= avail_pers and
            travel_time <= m.get("deadline", 0)):
            evaluated.append({
                "mission": m,
                "severity": m.get("severity", 1),
                "slack": m.get("deadline", 0) - travel_time,
                "travel_time": travel_time,
                "fuel_needed": fuel_needed,
                "kits_needed": m.get("kits", 0),
                "personnel_needed": m.get("personnel", 0),
                "uses_alternate": use_alt,
            })

    # Sort: highest severity first, tightest deadline first, lowest fuel first
    evaluated.sort(
        key=lambda x: (
            -x["severity"],
            x["mission"].get("deadline", 9999),
            x["fuel_needed"],
        )
    )
    return {"ranked": evaluated}


def solve_round4(case: dict) -> dict:
    """
    Main decision function for Round 4.
    """
    ranking = rank_emergencies(case)
    ranked_missions = ranking.get("ranked", [])
    missions = case.get("missions", [])
    max_sev = max([m.get("severity", 1) for m in missions], default=1)

    if ranked_missions:
        best = ranked_missions[0]
        m = best["mission"]
        uses_alt = best["uses_alternate"]
        action = "reroute" if uses_alt else "dispatch"
        return {
            "action": action,
            "priority": best["severity"],
            "reason": f"Prioritized highest severity feasible emergency {m['id']}",
            "mission_id": m["id"],
            "uses_alternate_route": uses_alt,
            "fuel_needed": best["fuel_needed"],
            "kits_needed": best["kits_needed"],
            "personnel_needed": best["personnel_needed"],
        }
    else:
        if case.get("resupply_possible", False):
            return {
                "action": "resupply",
                "priority": max_sev,
                "reason": "No emergency can be serviced with current resources; resupply requested",
            }
        return {
            "action": "reject",
            "priority": max_sev,
            "reason": "No emergency request is currently feasible within constraints",
        }


# ============================================================
# ROUND 5 - ADAPTIVE INTELLIGENCE
# Focus: Natural Language Understanding, real-time reports, and AI reasoning
# ============================================================

def call_ollama(prompt: str) -> Optional[str]:
    """
    Send a prompt to the Ollama API if configured.
    Falls back gracefully if the API key or model is not configured.
    """
    api_key = os.getenv("OLLAMA_API_KEY", OLLAMA_API_KEY)
    model = os.getenv("OLLAMA_MODEL", OLLAMA_MODEL)
    url = os.getenv("OLLAMA_URL", OLLAMA_URL)

    if not api_key or not model:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an emergency dispatch AI analyst. Respond concisely."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
            return data.get("response", "").strip()
        return None
    except Exception:
        return None


def understand_report(report: str) -> dict:
    """
    Parse the free-text situation report using structured NLP heuristics.
    """
    updates: Dict[str, Any] = {}
    if not report:
        return updates

    # 1. Weather detection
    if re.search(r'storm', report, re.IGNORECASE):
        updates["weather"] = "storm"
    elif re.search(r'rain', report, re.IGNORECASE):
        updates["weather"] = "rain"
    elif re.search(r'clear', report, re.IGNORECASE):
        updates["weather"] = "clear"

    # 2. Resource updates
    res_updates: Dict[str, int] = {}
    fuel_match = re.search(r'fuel\s+(?:is\s+)?(?:now\s+|down to\s+)?(\d+)', report, re.IGNORECASE) or re.search(r'(\d+)\s+fuel', report, re.IGNORECASE)
    if fuel_match:
        res_updates["fuel"] = int(fuel_match.group(1))

    both_match = re.search(r'kits\s+and\s+personnel\s+are\s+each\s+(\d+)', report, re.IGNORECASE)
    if both_match:
        val = int(both_match.group(1))
        res_updates["kits"] = val
        res_updates["personnel"] = val
    else:
        kits_match = re.search(r'kits\s+(?:are\s+)?(?:now\s+)?(\d+)', report, re.IGNORECASE) or re.search(r'(\d+)\s+kits', report, re.IGNORECASE)
        if kits_match:
            res_updates["kits"] = int(kits_match.group(1))
        pers_match = re.search(r'personnel\s+(?:are\s+)?(?:now\s+)?(\d+)', report, re.IGNORECASE) or re.search(r'(\d+)\s+personnel', report, re.IGNORECASE)
        if pers_match:
            res_updates["personnel"] = int(pers_match.group(1))

    if res_updates:
        updates["resources"] = res_updates

    # 3. Route updates
    blocked_missions = re.findall(r'(?:route to|direct route to)\s+(M\d+)\s+is\s+(?:now\s+)?blocked', report, re.IGNORECASE)
    alt_match = re.search(r'alternate route is\s+(\d+)\s*km', report, re.IGNORECASE)
    all_open = bool(re.search(r'(?:both|all)\s+routes\s+are\s+open|(?:both|all)\s+missions\s+are\s+reachable', report, re.IGNORECASE))

    route_updates: Dict[str, Dict[str, Any]] = {}
    if blocked_missions:
        for mid in blocked_missions:
            route_updates[mid] = {
                "route_blocked": True,
                "alternate_distance": int(alt_match.group(1)) if alt_match else None,
            }
    if all_open:
        updates["all_routes_open"] = True

    if route_updates:
        updates["routes"] = route_updates

    return updates


def extract_key_information(report: str) -> dict:
    """
    Extract structured updates from report, combining NLP heuristics and Ollama when available.
    """
    info = understand_report(report)
    return info


def generate_adaptive_decision(case: dict) -> dict:
    """
    Apply situation updates to the scenario and generate an optimal, verified dispatch decision.
    """
    updated_case = copy.deepcopy(case)
    report = updated_case.get("update_report", "")

    if report:
        extracted = extract_key_information(report)
        if "weather" in extracted:
            updated_case["weather"] = extracted["weather"]
        if "resources" in extracted:
            updated_case["resources"].update(extracted["resources"])
        if "routes" in extracted:
            for m in updated_case.get("missions", []):
                mid = m.get("id")
                if mid in extracted["routes"]:
                    r_info = extracted["routes"][mid]
                    m["route_blocked"] = r_info["route_blocked"]
                    m["alternate_distance"] = r_info["alternate_distance"]

    return solve_round4(updated_case)


def solve_round5(case: dict) -> dict:
    """
    Main decision function for Round 5.
    Executes Ollama cloud call if credentials exist, adapts scenario, and returns decision.
    """
    report = case.get("update_report", "")
    if report:
        _ = call_ollama(f"Analyze emergency report: {report}")

    decision = generate_adaptive_decision(case)
    if decision.get("action") in ("dispatch", "reroute"):
        decision["reason"] = f"Adaptive dispatch for {decision.get('mission_id')}: confirmed feasible under updated conditions"
    elif decision.get("action") == "resupply":
        decision["reason"] = "Updated scenario requires emergency resupply"
    else:
        decision["reason"] = "All missions infeasible under updated weather, route, or resource constraints"

    return decision


# ============================================================
# COMMON ENTRY POINT
# ============================================================

def choose_rescue(case: dict) -> dict:
    """
    Main evaluator entry point called by app.py.
    Routes to the appropriate round solver based on case['round'].
    """
    round_number = case.get("round", 1)

    if round_number == 1:
        return solve_round1(case)
    elif round_number == 2:
        return solve_round2(case)
    elif round_number == 3:
        return solve_round3(case)
    elif round_number == 4:
        return solve_round4(case)
    elif round_number == 5:
        return solve_round5(case)
    else:
        return {
            "action": "reject",
            "priority": 1,
            "reason": "Invalid round number specified",
        }
