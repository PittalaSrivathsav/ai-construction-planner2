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
from groq import Groq

app = Flask(__name__)


# ---------- AI FUNCTION (FIXED) ----------
def ask_groq(prompt):

    api_key = os.getenv("GROQ_API_KEY")

    # ✅ If no API key → fallback (NO Ollama)
    if not api_key:
        return (
            "1. PROJECT ASSESSMENT: Ensure feasibility with proper planning and resource allocation.\n"
            "2. CRITICAL PHASES: Focus on foundation and structural work for stability.\n"
            "3. RESOURCE OPTIMIZATION: Optimize labour and material usage to reduce costs.\n"
            "4. RISK PREVENTION: Follow safety standards and use quality materials."
        )

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

        # ✅ Safe fallback (no crash)
        return (
            "1. PROJECT ASSESSMENT: AI service temporarily unavailable.\n"
            "2. CRITICAL PHASES: Focus on planning and execution phases.\n"
            "3. RESOURCE OPTIMIZATION: Manage labour and materials efficiently.\n"
            "4. RISK PREVENTION: Ensure safety and compliance."
        )


# ---------- ROUTES ----------
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

    # ---------- CALCULATIONS ----------
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

    # ---------- AI PROMPT ----------
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

    # ---------- AI CALL ----------
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
    app.run(debug=True)
