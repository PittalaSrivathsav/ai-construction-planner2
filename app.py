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
            "1. PROJECT ASSESSMENT: Ensure feasibility with proper planning.\n"
            "2. CRITICAL PHASES: Focus on foundation and structure.\n"
            "3. RESOURCE OPTIMIZATION: Use labour and materials efficiently.\n"
            "4. RISK PREVENTION: Follow safety standards."
        )

    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior construction project consultant with real-world expertise."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Groq error:", e)

        return (
            "1. PROJECT ASSESSMENT: AI unavailable.\n"
            "2. CRITICAL PHASES: Monitor key stages.\n"
            "3. RESOURCE OPTIMIZATION: Optimize usage.\n"
            "4. RISK PREVENTION: Ensure safety."
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
You are a senior construction consultant.

PROJECT DETAILS:
Area: {area} sq yards
Floors: {floors}
Target Timeline: {target_days} days

Provide detailed expert advice in this format:

1. ACCELERATION RISKS:
Explain key risks when speeding up construction.

2. QUALITY CONTROL:
How to maintain quality under time pressure.

3. RESOURCE OPTIMIZATION:
How to manage labour and materials efficiently.

4. SCHEDULE STRATEGY:
Best approach to meet deadlines without failure.

Rules:
- Each point must be 2-3 lines
- Use professional terms
- Be practical and actionable
"""
    else:
        prompt = f"""
You are a senior construction consultant.

PROJECT DETAILS:
Area: {area} sq yards
Floors: {floors}
Timeline: {timeline['days']} days

Provide detailed expert advice in this format:

1. PROJECT FEASIBILITY:
Is the timeline realistic?

2. CRITICAL PHASES:
Which phases need close monitoring?

3. COST OPTIMIZATION:
How to reduce cost effectively?

4. RISK MANAGEMENT:
Key risks and prevention methods.

Rules:
- Each point must be 2-3 lines
- Be specific and realistic
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
