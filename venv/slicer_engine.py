
import subprocess
import re
from pathlib import Path


PRUSA_SLICER = Path(
    r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"
)

# PrusaSlicer preset configuration
PRINTER_PROFILE = "Pragma Generic FFF"
PRINT_PROFILE = "Pragma Generic FFF"
MATERIAL_PROFILE = "Pragma Generic FFF"


def slice_stl(input_path, output_path):
    """
    Slice an STL file using PrusaSlicer CLI.

    Uses named PrusaSlicer presets for:
    - Printer configuration
    - Print configuration
    - Material configuration

    Returns manufacturing metadata extracted from generated G-code.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    # 1. Validate PrusaSlicer installation
    if not PRUSA_SLICER.exists():
        raise FileNotFoundError(
            f"PrusaSlicer executable not found: {PRUSA_SLICER}"
        )

    # 2. Validate input STL
    if not input_path.exists():
        raise FileNotFoundError(
            f"STL file not found: {input_path}"
        )

    if input_path.suffix.lower() != ".stl":
        raise ValueError("Only STL files are supported.")

    if input_path.stat().st_size == 0:
        raise ValueError("STL file is empty.")

    # 3. Prepare output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove previous G-code to prevent false success
    if output_path.exists():
        output_path.unlink()

    # 4. Build PrusaSlicer CLI command
    command = [
        str(PRUSA_SLICER),

        "--printer-profile",
        PRINTER_PROFILE,

        "--print-profile",
        PRINT_PROFILE,

        "--material-profile",
        MATERIAL_PROFILE,

        "--slice",

        "--output",
        str(output_path),

        str(input_path)
    ]

    # 5. Execute PrusaSlicer
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=180
    )

    # 6. Validate execution result
    if result.returncode != 0:
        raise RuntimeError(
            f"PrusaSlicer failed: "
            f"{result.stderr or result.stdout}"
        )

    # 7. Confirm G-code generation
    if not output_path.exists():
        raise RuntimeError(
            "PrusaSlicer finished but G-code was not generated."
        )

    if output_path.stat().st_size == 0:
        raise RuntimeError(
            "PrusaSlicer generated an empty G-code file."
        )

    # 8. Read G-code metadata
    gcode_text = output_path.read_text(
        encoding="utf-8",
        errors="replace"
    )

    # 9. Metadata extraction patterns
    patterns = {
        "filament_length_mm": (
            r"filament used \[mm\]\s*=\s*([\d.]+)"
        ),

        "filament_volume_cm3": (
            r"filament used \[cm3\]\s*=\s*([\d.]+)"
        ),

        "filament_weight_g": (
            r"total filament used \[g\]\s*=\s*([\d.]+)"
        ),

        "filament_cost": (
            r"total filament cost\s*=\s*([\d.]+)"
        ),

        "wipe_tower_weight_g": (
            r"total filament used for wipe tower \[g\]\s*=\s*([\d.]+)"
        ),

        "print_time": (
            r"estimated printing time \(normal mode\)\s*=\s*(.+)"
        )
    }

    # 10. Extract manufacturing metadata
    metadata = {}

    for key, pattern in patterns.items():
        match = re.search(pattern, gcode_text)

        if match:
            value = match.group(1).strip()

            if key == "print_time":
                metadata[key] = value
            else:
                metadata[key] = float(value)

    # 11. Return structured result
    return {
        "engine": "PrusaSlicer",
        "gcode_generated": True,
        "gcode_path": str(output_path),
        "manufacturing_data": metadata,
        "stdout": result.stdout.strip()
    }
