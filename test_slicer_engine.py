
import sys
from pathlib import Path

# Import the engine from our current venv folder
ENGINE_DIR = Path(__file__).parent / "venv"
sys.path.insert(0, str(ENGINE_DIR))

from slicer_engine import slice_stl


STL_FILE = Path(
    r"C:\Freelancing\Websites\Pragma\Content"
    r"\pragma_test_washer_40x10x8mm.stl"
)

GCODE_FILE = Path(
    r"C:\Freelancing\Websites\Pragma\Content"
    r"\pragma_test_washer_engine_test.gcode"
)


def main():
    print("Testing Pragma Slicer Engine...")
    print("-" * 50)

    result = slice_stl(STL_FILE, GCODE_FILE)

    print("\nRESULT:")
    print("-" * 50)

    print("Engine:", result["engine"])
    print("G-code generated:", result["gcode_generated"])
    print("G-code path:", result["gcode_path"])

    print("\nManufacturing data:")
    for key, value in result["manufacturing_data"].items():
        print(f"{key}: {value}")

    print("\n" + "=" * 50)
    print("SLICER ENGINE TEST PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()
