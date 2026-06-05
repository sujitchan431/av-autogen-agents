import asyncio
import os
import sys

# Force UTF-8 output on Windows to handle Unicode in LLM responses
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core.tools import FunctionTool
from autogen_ext.models.anthropic import AnthropicChatCompletionClient


# ── BMI Tool ──────────────────────────────────────────────────────────────────

def calculate_bmi(weight_kg: float, height_cm: float) -> str:
    """Calculate BMI from weight in kg and height in cm."""
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25.0:
        category = "Normal weight"
    elif bmi < 30.0:
        category = "Overweight"
    else:
        category = "Obese"

    return (
        f"BMI Result:\n"
        f"  BMI Score  : {bmi:.2f}\n"
        f"  Category   : {category}\n"
        f"  Weight     : {weight_kg} kg\n"
        f"  Height     : {height_cm} cm ({height_m:.2f} m)"
    )


bmi_tool = FunctionTool(
    calculate_bmi,
    description="Calculates BMI from weight (kg) and height (cm). Returns BMI score and category.",
)


# ── User Data Collection (User Proxy Agent role) ──────────────────────────────

def collect_user_data() -> dict:
    print("\n" + "=" * 60)
    print("  SMART HEALTH ASSISTANT — User Proxy Agent")
    print("=" * 60)
    print("Collecting your health profile. Please answer the following:\n")

    while True:
        try:
            weight = float(input("  Weight (kg): ").strip())
            break
        except ValueError:
            print("  Invalid input. Enter a number (e.g. 70).")

    while True:
        try:
            height = float(input("  Height (cm): ").strip())
            break
        except ValueError:
            print("  Invalid input. Enter a number (e.g. 175).")

    while True:
        try:
            age = int(input("  Age         : ").strip())
            break
        except ValueError:
            print("  Invalid input. Enter a whole number.")

    gender = ""
    while gender not in ("male", "female", "other"):
        gender = input("  Gender (male/female/other): ").strip().lower()
        if gender not in ("male", "female", "other"):
            print("  Enter: male, female, or other.")

    diet = ""
    while diet not in ("veg", "non-veg", "vegan"):
        diet = input("  Dietary Preference (Veg/Non-Veg/Vegan): ").strip().lower()
        if diet not in ("veg", "non-veg", "vegan"):
            print("  Enter: Veg, Non-Veg, or Vegan.")

    return {
        "weight": weight,
        "height": height,
        "age": age,
        "gender": gender,
        "diet": diet,
    }


def format_user_data(data: dict) -> str:
    return (
        f"Weight: {data['weight']} kg\n"
        f"Height: {data['height']} cm\n"
        f"Age: {data['age']}\n"
        f"Gender: {data['gender']}\n"
        f"Dietary Preference: {data['diet']}"
    )


def get_last_text(result) -> str:
    for msg in reversed(result.messages):
        content = getattr(msg, "content", None)
        if content and isinstance(content, str):
            return content
    return ""


# ── Main Sequential Pipeline ──────────────────────────────────────────────────

async def run_health_assistant():

    # ── Model Client ──────────────────────────────────────────────────────────
    model_client = AnthropicChatCompletionClient(
        model="claude-sonnet-4-6",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # ── Step 1: User Proxy Agent — collect user data ──────────────────────────
    user_data = collect_user_data()
    user_summary = format_user_data(user_data)

    print("\n" + "=" * 60)
    print("  Confirmed User Profile:")
    print(user_summary)

    # ── Step 2 & 3: BMI Agent ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  BMI Agent — Calculating BMI & Health Recommendations")
    print("=" * 60 + "\n")

    bmi_agent = AssistantAgent(
        name="BMIAgent",
        model_client=model_client,
        tools=[bmi_tool],
        system_message=(
            "You are the BMI Analysis Agent. "
            "When given user health data, call the calculate_bmi tool with the provided weight and height. "
            "Then analyze the result and provide:\n"
            "1. The BMI score and category\n"
            "2. Health implications of that category\n"
            "3. Recommended daily calorie intake\n"
            "4. Key health recommendations tailored to the BMI category\n\n"
            "Be concise but thorough. End your response with 'ANALYSIS COMPLETE'."
        ),
        reflect_on_tool_use=True,
    )

    bmi_task = (
        f"Calculate the BMI and provide health recommendations for this user:\n\n"
        f"{user_summary}"
    )

    bmi_result = await Console(bmi_agent.run_stream(task=bmi_task))
    bmi_output = get_last_text(bmi_result)

    # ── Step 4: Diet Planner Agent ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Diet Planner Agent — Creating Personalized Meal Plan")
    print("=" * 60 + "\n")

    diet_agent = AssistantAgent(
        name="DietPlannerAgent",
        model_client=model_client,
        system_message=(
            "You are the Diet Planner Agent. "
            "Using BMI insights and the user's dietary preference, create a detailed 7-day meal plan. "
            "Include:\n"
            "- Daily calorie target aligned with the BMI category\n"
            "- Breakfast, Lunch, Dinner, and Snack for each day\n"
            "- Nutritional tips (protein, fiber, hydration)\n"
            "- Strictly respect dietary preference (Veg / Non-Veg / Vegan)\n\n"
            "Be specific with food items. End with 'MEAL PLAN COMPLETE'."
        ),
    )

    diet_task = (
        f"Create a 7-day meal plan for this user:\n\n"
        f"USER DATA:\n{user_summary}\n\n"
        f"BMI INSIGHTS:\n{bmi_output}"
    )

    diet_result = await Console(diet_agent.run_stream(task=diet_task))
    diet_output = get_last_text(diet_result)

    # ── Step 5: Workout Scheduler Agent ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Workout Scheduler Agent — Building Weekly Fitness Plan")
    print("=" * 60 + "\n")

    workout_agent = AssistantAgent(
        name="WorkoutSchedulerAgent",
        model_client=model_client,
        system_message=(
            "You are the Workout Scheduler Agent. "
            "Using BMI insights, diet plan context, and the user's age and gender, "
            "create a personalized weekly workout schedule. Include:\n"
            "- 7-day schedule with specific exercises for each day\n"
            "- Duration and intensity per session\n"
            "- Exercise types appropriate for the BMI category\n"
            "- Rest and active recovery days\n"
            "- Safety tips adjusted for age and gender\n\n"
            "End with a section titled 'HEALTH PLAN SUMMARY' that recaps:\n"
            "- BMI score and category\n"
            "- Diet plan highlights\n"
            "- Weekly fitness highlights\n\n"
            "Then write: 'YOUR COMPLETE HEALTH PLAN IS READY'"
        ),
    )

    workout_task = (
        f"Create a personalized weekly workout plan for this user:\n\n"
        f"USER DATA:\n{user_summary}\n\n"
        f"BMI INSIGHTS:\n{bmi_output}\n\n"
        f"DIET PLAN:\n{diet_output}"
    )

    await Console(workout_agent.run_stream(task=workout_task))

    print("\n" + "=" * 60)
    print("  Smart Health Assistant — Session Complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it with:  $env:ANTHROPIC_API_KEY='your-key-here'  (PowerShell)")
        sys.exit(1)
    asyncio.run(run_health_assistant())
