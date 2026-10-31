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
    pass


def calculate_travel_time(case: dict) -> dict:
    """
    Estimate the travel time for the mission.

    TODO:
    - Read weather conditions.
    - Consider the given travel conditions.
    - Calculate estimated travel time.
    """
    pass


def assess_mission(case: dict) -> dict:
    """
    Assess whether the rescue mission is feasible.

    TODO:
    - Analyse fuel requirement.
    - Analyse travel time.
    - Compare with the given constraints.
    """
    pass


def solve_round1(case: dict) -> dict:
    """
    Main decision function for Round 1.

    TODO:
    - Use your helper functions.
    - Decide whether to dispatch or reject.
    - Return the required output format.
    """
    pass


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
    pass


def compare_routes(case: dict) -> dict:
    """
    Compare the available routes.

    TODO:
    - Compare route characteristics.
    - Evaluate route suitability.
    """
    pass


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








      
 


      
