
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import trimesh

from fastapi import FastAPI, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from slicer_engine import slice_stl
from cost_engine import estimate_cost


app = FastAPI(
    title="Pragma CAD Engine",
    description="CAD file processing and analysis service for Pragma Engineering Solutions",
    version="0.3.0"
)


@app.get("/")
def home():
    return {
        "message": "Pragma CAD Engine is running",
        "status": "online",
        "version": "0.3.0"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "pragma-cad-engine"
    }


def analyze_topology(mesh):
    """
    Analyze mesh topology using a welded copy of the mesh.

    STL files frequently contain duplicated vertices.
    We merge vertices in the topology copy so shared edges
    can be detected correctly.
    """

    topology_mesh = mesh.copy()

    # Merge duplicate/coincident vertices for topology analysis
    topology_mesh.merge_vertices()

    faces = topology_mesh.faces

    # Create all triangle edges
    edges = np.vstack([
        faces[:, [0, 1]],
        faces[:, [1, 2]],
        faces[:, [2, 0]]
    ])

    # Make edge direction irrelevant for counting
    edges = np.sort(edges, axis=1)

    # Count unique edges and their face occurrences
    unique_edges, edge_counts = np.unique(
        edges,
        axis=0,
        return_counts=True
    )

    # Boundary edges: connected to only one face
    boundary_edges = int(np.count_nonzero(edge_counts == 1))

    # Non-manifold edges: connected to more than two faces
    non_manifold_edges = int(np.count_nonzero(edge_counts > 2))

    # Consistent face orientation
    winding_consistent = bool(
        topology_mesh.is_winding_consistent
    )

    # Closed surface check
    watertight = bool(topology_mesh.is_watertight)

    # Connected components using Union-Find
    face_count = len(faces)

    parent = list(range(face_count))
    rank = [0] * face_count

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        root_a = find(a)
        root_b = find(b)

        if root_a == root_b:
            return

        if rank[root_a] < rank[root_b]:
            parent[root_a] = root_b
        elif rank[root_a] > rank[root_b]:
            parent[root_b] = root_a
        else:
            parent[root_b] = root_a
            rank[root_a] += 1

    edge_to_faces = {}

    for face_index, face in enumerate(faces):
        face_edges = [
            tuple(sorted((int(face[0]), int(face[1])))),
            tuple(sorted((int(face[1]), int(face[2])))),
            tuple(sorted((int(face[2]), int(face[0]))))
        ]

        for edge in face_edges:
            edge_to_faces.setdefault(edge, []).append(face_index)

    for adjacent_faces in edge_to_faces.values():
        if len(adjacent_faces) >= 2:
            first_face = adjacent_faces[0]
            for other_face in adjacent_faces[1:]:
                union(first_face, other_face)

    connected_components = len({
        find(i) for i in range(face_count)
    })

    # Euler characteristic
    euler_number = int(topology_mesh.euler_number)

    # Degenerate triangle detection
    face_areas = topology_mesh.area_faces

    degenerate_faces = int(
        np.count_nonzero(face_areas <= 1e-12)
    )

    return {
        "topology_vertices": len(topology_mesh.vertices),
        "unique_edges": len(unique_edges),
        "boundary_edges": boundary_edges,
        "non_manifold_edges": non_manifold_edges,
        "is_watertight": watertight,
        "is_winding_consistent": winding_consistent,
        "connected_components": connected_components,
        "euler_number": euler_number,
        "degenerate_faces": degenerate_faces
    }


def assess_mesh_quality(topology):
    """
    Provide a preliminary mesh quality assessment.

    This is a diagnostic classification, not a guarantee
    that the model is printable.
    """

    issues = []

    if topology["boundary_edges"] > 0:
        issues.append("Mesh contains open boundaries")

    if topology["non_manifold_edges"] > 0:
        issues.append("Mesh contains non-manifold edges")

    if not topology["is_winding_consistent"]:
        issues.append("Face winding is inconsistent")

    if topology["degenerate_faces"] > 0:
        issues.append("Mesh contains degenerate faces")

    if topology["connected_components"] > 1:
        issues.append("Mesh contains multiple disconnected components")

    if topology["is_watertight"] and len(issues) == 0:
        quality = "good"
        message = "No basic topology issues detected"

    elif (
        topology["boundary_edges"] == 0
        and topology["non_manifold_edges"] == 0
        and topology["degenerate_faces"] == 0
        and topology["is_winding_consistent"]
    ):
        quality = "acceptable"
        message = "No major topology problems detected"

    else:
        quality = "needs_review"
        message = "Mesh topology requires inspection"

    return {
        "quality": quality,
        "message": message,
        "issues": issues
    }


@app.post("/analyze/stl")
async def analyze_stl(file: UploadFile = File(...)):

    # 1. Validate file extension
    filename = file.filename or "unknown"

    if not filename.lower().endswith(".stl"):
        raise HTTPException(
            status_code=400,
            detail="Only STL files are supported currently."
        )

    # 2. Read file
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    # 3. File size limit
    max_size = 25 * 1024 * 1024

    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the 25 MB limit."
        )

    # 4. Load STL
    try:
        mesh = trimesh.load(
            BytesIO(file_bytes),
            file_type="stl",
            force="mesh",
            process=False
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read STL file: {str(exc)}"
        )

    # 5. Validate mesh type
    if not isinstance(mesh, trimesh.Trimesh):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file does not contain a valid 3D mesh."
        )

    # 6. Validate geometry
    if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        raise HTTPException(
            status_code=400,
            detail="The STL mesh contains no geometry."
        )

    if not np.isfinite(mesh.vertices).all():
        raise HTTPException(
            status_code=400,
            detail="Mesh contains invalid coordinates."
        )

    # 7. Dimensions
    dimensions = mesh.extents

    dimensions_mm = {
        "x": round(float(dimensions[0]), 3),
        "y": round(float(dimensions[1]), 3),
        "z": round(float(dimensions[2]), 3)
    }

    # 8. Geometry measurements
    volume = abs(float(mesh.volume))
    surface_area = float(mesh.area)

    # 9. Topology analysis
    topology = analyze_topology(mesh)

    # 10. Mesh quality assessment
    quality_assessment = assess_mesh_quality(topology)

    # 11. Final response
    return {
        "status": "success",
        "filename": filename,
        "file_size_bytes": len(file_bytes),
        "file_size_mb": round(
            len(file_bytes) / (1024 * 1024), 3
        ),
        "format": "STL",
        "units_assumption": "millimeters",

        "geometry": {
            "dimensions_mm": dimensions_mm,
            "volume_mm3": round(volume, 3),
            "surface_area_mm2": round(surface_area, 3),
            "vertices_original": len(mesh.vertices),
            "faces": len(mesh.faces)
        },

        "topology": topology,

        "quality_assessment": quality_assessment
    }


@app.post("/analyze/print")
async def analyze_print(file: UploadFile = File(...)):

    # 1. Validate filename and format
    filename = file.filename or "unknown"

    if not filename.lower().endswith(".stl"):
        raise HTTPException(
            status_code=400,
            detail="Only STL files are supported currently."
        )

    # 2. Read uploaded file
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    # 3. Validate file size
    max_size = 25 * 1024 * 1024

    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the 25 MB limit."
        )

    # 4. Create temporary workspace
    try:
        with TemporaryDirectory(prefix="pragma_print_") as temp_dir:

            temp_path = Path(temp_dir)

            stl_path = temp_path / "input.stl"
            gcode_path = temp_path / "output.gcode"

            # Save uploaded STL temporarily
            stl_path.write_bytes(file_bytes)

            # 5. Run PrusaSlicer in a worker thread
            slicer_result = await run_in_threadpool(
                slice_stl,
                stl_path,
                gcode_path
            )

            # 6. Calculate manufacturing cost
            cost_estimate = estimate_cost(
                slicer_result["manufacturing_data"]
            )

            # 7. Return manufacturing results
            return {
                "status": "success",
                "filename": filename,
                "file_size_bytes": len(file_bytes),
                "file_size_mb": round(
                    len(file_bytes) / (1024 * 1024), 3
                ),
                "format": "STL",
                "engine": slicer_result["engine"],
                "gcode_generated": slicer_result["gcode_generated"],
                "manufacturing_data": slicer_result["manufacturing_data"],
                "cost_estimate": cost_estimate
            }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Print analysis failed: {str(exc)}"
        )
