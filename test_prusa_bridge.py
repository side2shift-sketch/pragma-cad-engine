
import subprocess
import re
import json
from pathlib import Path


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

PRUSA_SLICER = Path(
    r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"
)

STL_FILE = Path(
    r"C:\Freelancing\Websites\Pragma\Content"
    r"\pragma_test_washer_40x10x8mm.stl"
)

GCODE_FILE = Path(
    r"C:\Freelancing\Websites\Pragma\Content"
    r"\pragma_test_washer_python.gcode"
)


# --------------------------------------------------
# STEP 1: VALIDATE INPUT FILES
# --------------------------------------------------

def validate_files():

    if not PRUSA_SLICER.exists():
        raise FileNotFoundError(
            f"PrusaSlicer not found: {PRUSA_SLICER}"
        )

    if not STL_FILE.exists():
        raise FileNotFoundError(
            f"STL file not found: {STL_FILE}"
        )


# --------------------------------------------------
# STEP 2: RUN PRUSASLICER FROM PYTHON
# --------------------------------------------------

def run_slicer():

    command = [
        str(PRUSA_SLICER),
        "--slice",
        "--output",
        str(GCODE_FILE),
        str(STL_FILE)
    ]

    print("Launching PrusaSlicer from Python...")
    print("-" * 50)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=180
    )

    print("STDOUT:")
    print(result.stdout)

    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"PrusaSlicer failed with exit code {result.returncode}"
        )

    if not GCODE_FILE.exists():
        raise RuntimeError(
            "Slicer completed but G-code file was not created."
        )

    print("G-code successfully generated!")

    return result


# --------------------------------------------------
# STEP 3: READ G-CODE METADATA
# --------------------------------------------------

def extract_metadata():

    gcode_text = GCODE_FILE.read_text(
        encoding="utf-8",
        errors="replace"
    )

    metadata = {}

    patterns = {
        "filament_length_mm":
            r"filament used \[mm\]\s*=\s*([\d.]+)",

        "filament_volume_cm3":
            r"filament used \[cm3\]\s*=\s*([\d.]+)",

        "filament_weight_g":
            r"total filament used \[g\]\s*=\s*([\d.]+)",

        "filament_cost":
            r"total filament cost\s*=\s*([\d.]+)",

        "wipe_tower_weight_g":
            r"total filament used for wipe tower \[g\]\s*=\s*([\d.]+)",

        "print_time":
            r"estimated printing time \(normal mode\)\s*=\s*(.+)"
    }

    for key, pattern in patterns.items():

        match = re.search(pattern, gcode_text)

        if match:
            value = match.group(1).strip()

            if key == "print_time":
                metadata[key] = value
            else:
                metadata[key] = float(value)

    return metadata


# --------------------------------------------------
# STEP 4: MAIN
# --------------------------------------------------

def main():

    try:

        validate_files()

        run_slicer()

        metadata = extract_metadata()

        result = {
            "status": "success",
            "engine": "PrusaSlicer",
            "input_file": STL_FILE.name,
            "output_file": str(GCODE_FILE),
            "manufacturing_data": metadata
        }

        print("\n")
        print("=" * 50)
        print("PRAGMA - PRUSASLICER BRIDGE RESULT")
        print("=" * 50)

        print(json.dumps(result, indent=4))

        print("\nBridge test completed successfully.")

    except Exception as error:

        print("\nBRIDGE TEST FAILED")
        print("-" * 50)
        print(str(error))


if __name__ == "__main__":
    main()
