import sys
from pathlib import Path

# --------------------------------------------------
# IMPORT PRAGMA ENGINES
# --------------------------------------------------

ENGINE_DIR = Path(__file__).parent / "venv"
sys.path.insert(0, str(ENGINE_DIR))

from slicer_engine import slice_stl
from cost_engine import estimate_cost


# --------------------------------------------------
# INPUT FILES
# --------------------------------------------------

STL_FILE = Path(
    r"C:\Freelancing\Websites\Pragma\Content"
    r"\pragma_test_washer_40x10x8mm.stl"
)

GCODE_FILE = Path(
    r"C:\Freelancing\Websites\Pragma\Content"
    r"\pragma_test_washer_cost_pipeline.gcode"
)


# --------------------------------------------------
# MANUFACTURING PIPELINE TEST
# --------------------------------------------------

def main():

    print("PRAGMA MANUFACTURING PIPELINE TEST")
    print("=" * 60)

    # STEP 1: Generate manufacturing data using PrusaSlicer
    print("\nSTEP 1: Running PrusaSlicer...")
    slicer_result = slice_stl(STL_FILE, GCODE_FILE)

    manufacturing_data = slicer_result["manufacturing_data"]

    print("Slicing completed successfully.")

    # STEP 2: Feed actual manufacturing data into cost engine
    print("\nSTEP 2: Calculating manufacturing cost...")

    cost_result = estimate_cost(manufacturing_data)

    # STEP 3: Display manufacturing information
    print("\nMANUFACTURING DATA")
    print("-" * 60)

    print(
        "Filament weight:",
        manufacturing_data["filament_weight_g"],
        "g"
    )

    print(
        "Print time:",
        manufacturing_data["print_time"]
    )

    # STEP 4: Display itemized cost breakdown
    costs = cost_result["cost_breakdown"]

    print("\nCOST BREAKDOWN")
    print("-" * 60)

    print(f"Material cost:       Rs. {costs['material_cost']:.2f}")
    print(f"Machine cost:        Rs. {costs['machine_cost']:.2f}")
    print(f"Electricity cost:    Rs. {costs['electricity_cost']:.2f}")
    print(f"Labor cost:          Rs. {costs['labor_cost']:.2f}")
    print(f"Base cost:          Rs. {costs['base_cost']:.2f}")
    print(f"Overhead:           Rs. {costs['overhead_cost']:.2f}")
    print(f"Production cost:    Rs. {costs['production_cost']:.2f}")
    print(f"Profit:             Rs. {costs['profit']:.2f}")

    # STEP 5: Final price
    print("\n" + "=" * 60)
    print(
        f"ESTIMATED SELLING PRICE: "
        f"Rs. {costs['selling_price']:.2f}"
    )
    print("=" * 60)

    # STEP 6: Basic integration validation
    assert slicer_result["gcode_generated"] is True
    assert manufacturing_data["filament_weight_g"] > 0
    assert costs["selling_price"] > 0

    print("\nPIPELINE TEST PASSED")
    print("STL -> PrusaSlicer -> Manufacturing Data -> Cost Engine")


if __name__ == "__main__":
    main()
