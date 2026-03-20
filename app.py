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
            "1. PROJECT FEASIBILITY:\nEnsure proper planning and realistic execution.\n\n"
            "2. CRITICAL PHASES:\nFocus on foundation and structural work.\n\n"
            "3. COST OPTIMIZATION:\nReduce wastage and optimize materials.\n\n"
            "4. RISK MANAGEMENT:\nFollow safety standards and prevent delays."
        )

    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are a highly experienced civil engineer giving real-world construction advice."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.9,
            max_tokens=800
        )

        ai_text = response.choices[0].message.content.strip()

        # ✅ FIXED: inside try block
        return ai_text.replace("\n\n", "\n").strip()

    except Exception as e:
        print("Groq error:", e)

        return (
            "1. PROJECT FEASIBILITY:\nAI unavailable.\n\n"
            "2. CRITICAL PHASES:\nMonitor key stages.\n\n"
            "3. COST OPTIMIZATION:\nControl expenses.\n\n"
            "4. RISK MANAGEMENT:\nEnsure safety."
        )


# ---------- ROUTES ----------

@app.route("/health")
def health():
    return "OK", 200


@app.route("/")
def home():
    try:
        return render_template("index.html")
    except:
        return "App is running", 200


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
Explain risks like structural issues, curing problems, and labour fatigue.

2. QUALITY CONTROL:
How to maintain structural quality under time pressure.

3. RESOURCE OPTIMIZATION:
How to manage labour shifts and material flow efficiently.

4. SCHEDULE STRATEGY:
Best practical way to meet deadlines without failure.

Rules:
- Each point must be 3-4 lines
- Use real construction terms
"""
    else:
        prompt = f"""
You are a senior construction project manager with 20+ years experience.

PROJECT DETAILS:
- Area: {area} sq yards
- Floors: {floors}
- Timeline: {timeline['days']} days

Provide professional insights.

1. PROJECT FEASIBILITY:
Evaluate whether this project plan is realistic.

2. CRITICAL PHASES:
Explain which phases need strict monitoring.

3. COST OPTIMIZATION:
Suggest real-world cost-saving methods.

4. RISK MANAGEMENT:
Identify risks and prevention strategies.

Rules:
- Each point must be 3-4 lines
- Use technical construction terms
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


# ---------- RUN APP ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
