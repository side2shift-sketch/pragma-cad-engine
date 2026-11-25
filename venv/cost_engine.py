import re


# --------------------------------------------------
# PRAGMA MANUFACTURING COST ENGINE
# --------------------------------------------------

DEFAULT_SETTINGS = {
    "filament_price_per_gram": 1.50,
    "machine_rate_per_hour": 20.00,
    "machine_power_kw": 1.20,
    "electricity_rate_per_kwh": 8.00,
    "labor_cost": 10.00,
    "overhead_percent": 10.00,
    "profit_margin_percent": 20.00,
}


def parse_print_time(time_string):
    """
    Convert PrusaSlicer time text into total seconds.

    Examples:
        '1h 20m' -> 4800
        '45m 30s' -> 2730
        '2d 3h 10m' -> 184200
    """

    if not isinstance(time_string, str):
        raise ValueError("Print time must be a string.")

    units = {
        "d": 86400,
        "h": 3600,
        "m": 60,
        "s": 1,
    }

    matches = re.findall(r"(\d+)\s*([dhms])", time_string.lower())

    if not matches:
        raise ValueError(
            f"Unable to parse print time: {time_string}"
        )

    total_seconds = sum(
        int(value) * units[unit]
        for value, unit in matches
    )

    return total_seconds


def estimate_cost(manufacturing_data, settings=None):
    """
    Calculate manufacturing cost from PrusaSlicer metadata.

    Returns an itemized cost breakdown.
    """

    # 1. Load settings
    config = DEFAULT_SETTINGS.copy()

    if settings:
        config.update(settings)

    # 2. Validate required manufacturing data
    required_fields = [
        "filament_weight_g",
        "print_time",
    ]

    for field in required_fields:
        if field not in manufacturing_data:
            raise ValueError(
                f"Missing manufacturing data: {field}"
            )

    filament_weight = float(
        manufacturing_data["filament_weight_g"]
    )

    if filament_weight < 0:
        raise ValueError("Filament weight cannot be negative.")

    # 3. Convert print time into hours
    print_seconds = parse_print_time(
        manufacturing_data["print_time"]
    )

    print_hours = print_seconds / 3600

    # 4. Calculate material cost
    material_cost = (
        filament_weight
        * config["filament_price_per_gram"]
    )

    # 5. Calculate machine operating cost
    machine_cost = (
        print_hours
        * config["machine_rate_per_hour"]
    )

    # 6. Calculate electricity cost
    electricity_kwh = (
        print_hours
        * config["machine_power_kw"]
    )

    electricity_cost = (
        electricity_kwh
        * config["electricity_rate_per_kwh"]
    )

    # 7. Labor cost
    labor_cost = float(config["labor_cost"])

    # 8. Calculate base cost
    base_cost = (
        material_cost
        + machine_cost
        + electricity_cost
        + labor_cost
    )

    # 9. Apply overhead
    overhead_cost = (
        base_cost
        * config["overhead_percent"]
        / 100
    )

    cost_with_overhead = base_cost + overhead_cost

    # 10. Apply profit margin
    profit = (
        cost_with_overhead
        * config["profit_margin_percent"]
        / 100
    )

    selling_price = cost_with_overhead + profit

    # 11. Return structured result
    return {
        "currency": "INR",
        "manufacturing": {
            "filament_weight_g": round(filament_weight, 3),
            "print_time_seconds": print_seconds,
            "print_time_hours": round(print_hours, 4),
        },
        "cost_breakdown": {
            "material_cost": round(material_cost, 2),
            "machine_cost": round(machine_cost, 2),
            "electricity_cost": round(electricity_cost, 2),
            "labor_cost": round(labor_cost, 2),
            "base_cost": round(base_cost, 2),
            "overhead_cost": round(overhead_cost, 2),
            "production_cost": round(cost_with_overhead, 2),
            "profit": round(profit, 2),
            "selling_price": round(selling_price, 2),
        },
        "settings_used": config,
    }
