import sys
from pathlib import Path

# Import Pragma's cost engine from the current source location
ENGINE_DIR = Path(__file__).parent / "venv"
sys.path.insert(0, str(ENGINE_DIR))

from cost_engine import estimate_cost, parse_print_time


def main():
    print("Testing Pragma Manufacturing Cost Engine...")
    print("-" * 50)

    # TEST 1: Print time parsing
    seconds = parse_print_time("1h 20m")

    assert seconds == 4800, f"Expected 4800 seconds, got {seconds}"

    print("TEST 1 PASSED: Print time parser")

    # TEST 2: Manufacturing cost calculation
    manufacturing_data = {
        "filament_weight_g": 10.0,
        "print_time": "1h 20m",
    }

    result = estimate_cost(manufacturing_data)

    costs = result["cost_breakdown"]

    # Expected values based on default test settings
    assert costs["material_cost"] == 15.00
    assert costs["machine_cost"] == 26.67
    assert costs["electricity_cost"] == 12.80
    assert costs["labor_cost"] == 10.00
    assert costs["base_cost"] == 64.47
    assert costs["overhead_cost"] == 6.45
    assert costs["production_cost"] == 70.91
    assert costs["profit"] == 14.18
    assert costs["selling_price"] == 85.10

    print("TEST 2 PASSED: Cost calculation")

    # TEST 3: Different print time formats
    assert parse_print_time("45m 30s") == 2730
    assert parse_print_time("2d 3h 10m") == 184200

    print("TEST 3 PASSED: Multiple time formats")

    # Display the complete cost breakdown
    print("\nCOST BREAKDOWN")
    print("-" * 50)

    print("Currency:", result["currency"])

    for key, value in costs.items():
        print(f"{key}: Rs. {value:.2f}")

    print("\n" + "=" * 50)
    print("ALL COST ENGINE TESTS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()
