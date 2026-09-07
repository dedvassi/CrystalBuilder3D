from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pymatgen.core import Structure, Lattice
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
import math
import re

HERE = Path(__file__).parent
app = FastAPI(title="CrystalBuilder3D Web", docs_url=None)

def scene_cif_fallback(text: str, name: str) -> dict:
    """Read exported scene CIFs whose repeated boundary atoms exceed occupancy."""
    def field(label):
        match = re.search(rf"^{label}\s+([^\s]+)", text, re.MULTILINE)
        return float(match.group(1).split("(")[0]) if match else None
    a, b, c = (field(x) for x in ("_cell_length_a", "_cell_length_b", "_cell_length_c"))
    alpha, beta, gamma = (field(x) or 90.0 for x in ("_cell_angle_alpha", "_cell_angle_beta", "_cell_angle_gamma"))
    if not all((a, b, c)):
        raise ValueError("В CIF отсутствуют параметры решётки")
    al, be, ga = map(math.radians, (alpha, beta, gamma))
    va = [a, 0, 0]; vb = [b * math.cos(ga), b * math.sin(ga), 0]
    cx = c * math.cos(be); cy = c * (math.cos(al) - math.cos(be) * math.cos(ga)) / math.sin(ga)
    vc = [cx, cy, math.sqrt(max(0, c * c - cx * cx - cy * cy))]
    lines = [line.strip() for line in text.splitlines()]; sites = []
    for index, line in enumerate(lines):
        if line.lower() != "loop_": continue
        headers = []; pos = index + 1
        while pos < len(lines) and lines[pos].startswith("_"):
            headers.append(lines[pos].split()[0]); pos += 1
        required = ["_atom_site_type_symbol", "_atom_site_fract_x", "_atom_site_fract_y", "_atom_site_fract_z"]
        if not all(key in headers for key in required): continue
        indexes = [headers.index(key) for key in required]
        while pos < len(lines) and lines[pos] and not lines[pos].startswith(("_", "loop_", "data_")):
            values = lines[pos].split(); pos += 1
            if len(values) >= len(headers):
                sites.append({"e": values[indexes[0]], "f": [float(values[i].split("(")[0]) for i in indexes[1:]]})
        break
    if not sites: raise ValueError("В CIF нет атомных координат")
    return {"filename": name, "lattice": [va, vb, vc], "sites": sites, "preserve_sites": True}

@app.post("/api/structure")
async def structure(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8", errors="replace")
    try:
        raw = Structure.from_str(content, fmt="cif")
        try: raw = SpacegroupAnalyzer(raw).get_conventional_standard_structure()
        except Exception: pass
        return {"filename": file.filename, "lattice": raw.lattice.matrix.tolist(), "sites": [{"e": s.specie.symbol, "f": s.frac_coords.tolist()} for s in raw]}
    except Exception:
        try:
            return scene_cif_fallback(content, file.filename)
        except Exception as exc:
            raise HTTPException(422, f"Не удалось прочитать CIF: {exc}")

@app.post("/api/export/{format}")
async def export(format: str, payload: dict):
    atoms = payload.get("atoms", []); stem = "".join(x for x in payload.get("filename", "scene") if x.isalnum() or x in "-_") or "scene"
    if not atoms: raise HTTPException(400, "В сцене нет атомов")
    if format == "xyz":
        text = f"{len(atoms)}\nCrystalBuilder3D\n" + "\n".join(f"{a['e']} {a['p'][0]:.8f} {a['p'][1]:.8f} {a['p'][2]:.8f}" for a in atoms) + "\n"
        return StreamingResponse(BytesIO(text.encode()), media_type="chemical/x-xyz", headers={"Content-Disposition":f'attachment; filename="{stem}.xyz"'})
    if format == "cif":
        try: text = Structure(Lattice(payload["lattice"]), [a["e"] for a in atoms], [a["p"] for a in atoms], coords_are_cartesian=True).to(fmt="cif")
        except Exception as exc: raise HTTPException(422, str(exc))
        return StreamingResponse(BytesIO(text.encode()), media_type="chemical/x-cif", headers={"Content-Disposition":f'attachment; filename="{stem}.cif"'})
    raise HTTPException(404, "Поддерживаются cif и xyz")

app.mount("/", StaticFiles(directory=HERE, html=True), name="web")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
