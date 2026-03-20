from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify, render_template
from calculator import (
    calculate_workers,
    calculate_materials,
    calculate_timeline,
    calculate_cost,
    calculate_accelerated_workers,
    generate_weekly_schedule
)

import os

# Groq
from groq import Groq

# IBM Granite (Ollama)
from ollama_client import ask_granite

app = Flask(__name__)


def ask_groq(prompt):

    api_key = os.getenv("GROQ_API_KEY")

    # If no Groq key, fall back to Granite
    if not api_key:
        return ask_granite(prompt)

    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional construction project manager."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Groq error:", e)
        try:
            return ask_granite(prompt)
        except Exception:
            return (
                "1. PROJECT ASSESSMENT: AI service unavailable.\n"
                "2. CRITICAL PHASES: AI service unavailable.\n"
                "3. RESOURCE OPTIMIZATION: AI service unavailable.\n"
                "4. RISK PREVENTION: AI service unavailable."
            )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/plan", methods=["POST"])
def plan():
    data = request.get_json(silent=True) or {}

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        area = float(data.get("area", 0))
        floors = int(data.get("floors", 0))
        accelerate = bool(data.get("accelerate", False))
        target_days = int(data.get("target_days", 90)) if accelerate else None
    except (TypeError, ValueError):
        return jsonify({"error": "area, floors and target_days must be numeric"}), 400

    if area <= 0 or floors <= 0:
        return jsonify({"error": "area and floors must be greater than zero"}), 400

    if accelerate and (target_days is None or target_days <= 0):
        return jsonify({"error": "target_days must be greater than zero when accelerate is true"}), 400

    # Calculate based on mode
    if accelerate and target_days:
        workers, accel_factor, normal_days = calculate_accelerated_workers(
            area, floors, target_days
        )
        timeline = {
            "days": target_days,
            "weeks": round(target_days / 7, 1),
            "months": round(target_days / 30, 1),
            "normal_days": normal_days,
            "acceleration_factor": round(accel_factor, 2)
        }
    else:
        workers = calculate_workers(area, floors)
        timeline = calculate_timeline(area, floors)

    materials = calculate_materials(area, floors)
    cost = calculate_cost(workers, timeline["days"])
    schedule = generate_weekly_schedule(timeline["weeks"])

    # Prepare AI prompt
    if accelerate:
        prompt = f"""
You are a professional construction project manager providing concise advice.

PROJECT: {area} sq yards, {floors} floors
TARGET: {target_days} days (accelerated from {timeline.get('normal_days', 'N/A')} days)

Provide EXACTLY 4 points in this format:

1. ACCELERATION RISKS: [one key risk in 15 words]

2. QUALITY CONTROL: [one critical measure in 15 words]

3. RESOURCE MANAGEMENT: [one optimization tip in 15 words]

4. SCHEDULE STRATEGY: [one timeline advice in 15 words]

Keep each point under 20 words. Be specific and actionable.
"""
    else:
        prompt = f"""
You are a professional construction project manager providing concise advice.

PROJECT: {area} sq yards, {floors} floors
TIMELINE: {timeline['days']} days

Provide EXACTLY 4 points in this format:

1. PROJECT ASSESSMENT: [feasibility verdict in 15 words]

2. CRITICAL PHASES: [top 2 phases to monitor in 15 words]

3. RESOURCE OPTIMIZATION: [one cost-saving tip in 15 words]

4. RISK PREVENTION: [one key safety measure in 15 words]

Keep each point under 20 words. Be specific and actionable.
"""

    # Groq is used here (with Granite fallback)
    ai_advice = ask_groq(prompt)

    return jsonify({
        "workers": workers,
        "materials": materials,
        "timeline": timeline,
        "cost": cost,
        "schedule": schedule,
        "ai_advice": ai_advice,
        "mode": "accelerated" if accelerate else "normal"
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
