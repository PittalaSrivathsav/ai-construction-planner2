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


# ---------- AI FUNCTION ----------
def ask_groq(prompt):

    api_key = os.getenv("GROQ_API_KEY")

    # Fallback if no API key
    if not api_key:
        return (
            "1. PROJECT FEASIBILITY:\nEnsure proper planning, realistic timelines, and structured execution.\n\n"
            "2. CRITICAL PHASES:\nFocus on foundation, structural work, and finishing quality.\n\n"
            "3. COST OPTIMIZATION:\nOptimize labour, reduce material wastage, and plan procurement smartly.\n\n"
            "4. RISK MANAGEMENT:\nFollow safety standards and monitor execution to avoid delays."
        )

    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are a highly experienced civil engineer and construction project manager who gives practical, real-world site advice."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.9,
            max_tokens=800
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Groq error:", e)

        return (
            "1. PROJECT FEASIBILITY:\nAI temporarily unavailable.\n\n"
            "2. CRITICAL PHASES:\nMonitor key construction stages carefully.\n\n"
            "3. COST OPTIMIZATION:\nControl expenses and manage materials.\n\n"
            "4. RISK MANAGEMENT:\nEnsure safety and proper execution."
        )


# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/plan", methods=["POST"])
def plan():
    data = request.get_json(silent=True) or {}

    try:
        area = float(data.get("area", 0))
        floors = int(data.get("floors", 0))
        accelerate = bool(data.get("accelerate", False))
        target_days = int(data.get("target_days", 90)) if accelerate else None
    except:
        return jsonify({"error": "Invalid input"}), 400

    if area <= 0 or floors <= 0:
        return jsonify({"error": "Invalid values"}), 400

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
You are a senior construction consultant specializing in fast-track projects.

PROJECT DETAILS:
- Area: {area} sq yards
- Floors: {floors}
- Target Timeline: {target_days} days
- Normal Timeline: {timeline.get('normal_days', 'N/A')} days

Provide expert-level analysis.

1. ACCELERATION RISKS:
Explain risks like structural issues, improper curing, or labour fatigue.

2. QUALITY CONTROL STRATEGY:
How to maintain construction quality under time pressure.

3. RESOURCE & LABOUR OPTIMIZATION:
How to manage workforce shifts, parallel work, and material supply.

4. SCHEDULE STRATEGY:
Best practical approach to meet deadlines without compromising quality.

Rules:
- Each point must be 3-4 lines
- Use real construction terms (RCC, curing, load, etc.)
- Be practical and realistic
"""
    else:
        prompt = f"""
You are a senior construction project manager with 20+ years of experience.

PROJECT DETAILS:
- Area: {area} sq yards
- Floors: {floors}
- Timeline: {timeline['days']} days

Provide professional construction insights.

1. PROJECT FEASIBILITY:
Evaluate whether the project plan is realistic and highlight challenges.

2. CRITICAL EXECUTION PHASES:
Explain key phases requiring strict supervision and why.

3. COST OPTIMIZATION STRATEGY:
Suggest practical methods to reduce cost without affecting quality.

4. RISK & SAFETY MANAGEMENT:
Identify major risks and prevention strategies.

Rules:
- Each point must be 3-4 lines
- Use technical construction terminology
- Avoid generic advice
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


# ---------- RUN APP (RENDER FIX) ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
