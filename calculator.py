def calculate_workers(area, floors):
    """Calculate required workers based on area and floors"""
    total = int(area * floors * 0.04)
    
    return {
        "masons": int(total * 0.30),
        "helpers": int(total * 0.40),
        "carpenters": int(total * 0.15),
        "steel_workers": int(total * 0.10),
        "supervisors": max(1, int(total * 0.05))
    }


def calculate_materials(area, floors):
    """Calculate required construction materials"""
    total_area = area * floors
    
    return {
        "cement_bags": int(total_area * 0.45),
        "steel_tons": round(total_area * 0.004, 2),
        "sand_tons": round(total_area * 0.03, 2),
        "water_liters": int(total_area * 180)
    }


def calculate_timeline(area, floors):
    """Calculate project timeline"""
    days = int((area * floors) / 20)
    
    return {
        "days": days,
        "weeks": round(days / 7, 1),
        "months": round(days / 30, 1)
    }


def calculate_cost(workers, days):
    """Calculate labour cost"""
    wage_per_day = 700
    
    total_workers = sum(workers.values())
    labour_cost = total_workers * wage_per_day * days
    
    return {
        "labour_cost": labour_cost,
        "total_workers": total_workers
    }


def calculate_accelerated_workers(area, floors, target_days):
    """Calculate workers needed for accelerated timeline"""
    # Normal timeline
    normal_timeline = calculate_timeline(area, floors)
    normal_days = normal_timeline["days"]
    
    # If target is same or more than normal, use normal workers
    if target_days >= normal_days:
        return calculate_workers(area, floors), 1.0, normal_days
    
    # Calculate acceleration factor
    acceleration_factor = normal_days / target_days
    
    # Get normal workers
    normal_workers = calculate_workers(area, floors)
    
    # Scale up workers (with diminishing returns)
    scaling = acceleration_factor ** 0.8
    
    accelerated_workers = {
        "masons": int(normal_workers["masons"] * scaling),
        "helpers": int(normal_workers["helpers"] * scaling),
        "carpenters": int(normal_workers["carpenters"] * scaling),
        "steel_workers": int(normal_workers["steel_workers"] * scaling),
        "supervisors": max(2, int(normal_workers["supervisors"] * scaling))
    }
    
    return accelerated_workers, acceleration_factor, normal_days


def generate_weekly_schedule(total_weeks):
    """Generate weekly construction schedule"""
    base_schedule = [
        {"week": 1, "activity": "Site preparation and layout"},
        {"week": 2, "activity": "Foundation and footing"},
        {"week": 3, "activity": "Ground floor columns and slab"},
        {"week": 4, "activity": "First floor structure"},
        {"week": 5, "activity": "Second floor structure"},
        {"week": 6, "activity": "Brick work and plastering"},
        {"week": 7, "activity": "Electrical and plumbing"},
        {"week": 8, "activity": "Flooring and painting"},
        {"week": 9, "activity": "Doors, windows and finishing"},
        {"week": 10, "activity": "Final inspection and handover"}
    ]
    
    weeks = max(1, int(total_weeks))
    if weeks <= 10:
        return base_schedule[:weeks]

    # Extend plan beyond week 10 by repeating core execution phases.
    extended_schedule = list(base_schedule)
    repeating_activities = [
        "Structural and masonry progression",
        "MEP installation and testing",
        "Interior finishing and QA"
    ]

    for week in range(11, weeks + 1):
        activity = repeating_activities[(week - 11) % len(repeating_activities)]
        extended_schedule.append({"week": week, "activity": activity})

    return extended_schedule