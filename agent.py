"""RescueOps participant agent  (LangGraph + LangChain tools + Ollama for Round 5).

STRUCTURE
---------

    solve_round1(case)   Basic Rescue          (direct route, 1 mission)
    solve_round2(case)   Blocked Routes        (blocked road + alternate route)
    solve_round3(case)   Limited Resources     (fuel / kits / personnel, resupply)
    solve_round4(case)   Critical Priorities   (many missions, best severity wins)
    solve_round5(case)   Adaptive RescueOps    (update_report + Ollama call)

"""
# ======================== IMPORTS ============================
#akash naik
import json
import math
import os
import re
import requests

from typing import Any, Dict, List, TypedDict

from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda

from langgraph.graph import END, StateGraph


# ======================== CONFIGURATION ======================

OLLAMA_URL = "https://ollama.com/v1/chat/completions"

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
WEATHER_FACTORS: Dict[str, float] = {
    "clear": 1.0,
    "rain": 1.25,
    "storm": 1.5,
}

# ============================================================
# ROUND 1 - BASIC RESCUE FEASIBILITY
# Focus: Fuel calculation and travel feasibility
# ============================================================

def calculate_fuel(case: dict) -> dict:
    """
    Calculate the fuel required for the rescue mission.

    TODO:
    - Read the mission distance.
    - Calculate required fuel.
    - Return the calculated fuel requirement.
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
    Estimate the travel time for the mission.

    TODO:
    - Read weather conditions.
    - Consider the given travel conditions.
    - Calculate estimated travel time.
    """
    missions = case.get("missions", [])
    if not missions:
        return {"travel_time": 0, "weather": "clear"}
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
    Assess whether the rescue mission is feasible.

    TODO:
    - Analyse fuel requirement.
    - Analyse travel time.
    - Compare with the given constraints.
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

    TODO:
    - Use your helper functions.
    - Decide whether to dispatch or reject.
    - Return the required output format.
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
    Analyse the available routes.

    TODO:
    - Read the available route information.
    - Identify route conditions.
    - Analyse route suitability.
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
    Compare the available routes.

    TODO:
    - Compare route characteristics.
    - Evaluate route suitability.
    """
    
    
    


def select_best_route(case: dict) -> dict:
    """
    Select the most suitable route.

    TODO:
    - Select an appropriate route.
    - Return the selected route information.
    """
    pass


def solve_round2(case: dict) -> dict:
    """
    Main decision function for Round 2.

    TODO:
    - Use your route analysis functions.
    - Generate the final route decision.
    """
    pass


# ============================================================
# ROUND 3 - RESOURCE ALLOCATION
# Focus: Distribution of limited resources
# ============================================================

def calculate_resource_demand(case: dict) -> dict:
    """
    Calculate resource requirements.

    TODO:
    - Analyse the resource requirements.
    - Calculate demand for each mission.
    """
    pass


def evaluate_resource_availability(case: dict) -> dict:
    """
    Evaluate available resources.

    TODO:
    - Read available resources.
    - Compare demand and availability.
    """
    pass


def allocate_resources(case: dict) -> dict:
    """
    Allocate available resources.

    TODO:
    - Decide how resources should be distributed.
    - Avoid exceeding available resource limits.
    """
    pass


def solve_round3(case: dict) -> dict:
    """
    Main decision function for Round 3.

    TODO:
    - Use your resource allocation functions.
    - Generate the final allocation decision.
    """
    pass


# ============================================================
# ROUND 4 - EMERGENCY PRIORITISATION
# Focus: Ranking emergency requests
# ============================================================

def evaluate_severity(case: dict) -> dict:
    """
    Evaluate the severity of emergency requests.

    TODO:
    - Analyse the severity information.
    - Identify critical emergency cases.
    """
    pass


def calculate_urgency(case: dict) -> dict:
    """
    Determine the urgency of each emergency.

    TODO:
    - Analyse urgency-related information.
    - Estimate which emergency needs attention first.
    """
    pass


def rank_emergencies(case: dict) -> dict:
    """
    Rank emergency requests.

    TODO:
    - Compare emergency cases.
    - Generate an appropriate ranking.
    """
    pass


def solve_round4(case: dict) -> dict:
    """
    Main decision function for Round 4.

    TODO:
    - Use your ranking functions.
    - Select the emergency that should receive priority.
    """
    pass


# ============================================================
# ROUND 5 - ADAPTIVE INTELLIGENCE
# Focus: Natural Language Understanding and AI reasoning
# ============================================================

def call_ollama(prompt: str) -> str:
    """
    Send a prompt to the Ollama API.

    TODO:
    - Use OLLAMA_API_KEY and OLLAMA_MODEL.
    - Send the request using requests.
    - Handle API errors.
    - Return the model response.
    """
    pass


def understand_report(report: str) -> dict:
    """
    Understand the free-text situation report.

    TODO:
    - Analyse the report using an LLM.
    - Identify important information.
    """
    pass


def extract_key_information(report: str) -> dict:
    """
    Extract relevant information from the report.

    TODO:
    - Extract important updates.
    - Structure the extracted information.
    """
    pass


def generate_adaptive_decision(case: dict) -> dict:
    """
    Generate a decision based on the updated situation.

    TODO:
    - Use the extracted information.
    - Analyse the new situation.
    - Generate an appropriate decision.
    """
    pass


def solve_round5(case: dict) -> dict:
    """
    Main decision function for Round 5.

    TODO:
    - Read the update report.
    - Use Ollama for AI-based understanding.
    - Generate the final adaptive decision.

    IMPORTANT:
    At least one successful Ollama API call is mandatory
    for every Round 5 test case.
    """
    pass


# ============================================================
# COMMON ENTRY POINT
# ============================================================

def choose_rescue(case: dict) -> dict:
    """
    Main function called by the evaluator.

    Select the appropriate round solver based on case["round"].
    """

    round_number = case.get("round")

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
            "reason": "Invalid round"
        }








      
 


      
