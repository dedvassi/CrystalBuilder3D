from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pymatgen.core import Structure, Lattice
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

HERE = Path(__file__).parent
app = FastAPI(title="CrystalBuilder3D Web", docs_url=None)

@app.post("/api/structure")
async def structure(file: UploadFile = File(...)):
    try:
        raw = Structure.from_str((await file.read()).decode("utf-8", errors="replace"), fmt="cif")
        try: raw = SpacegroupAnalyzer(raw).get_conventional_standard_structure()
        except Exception: pass
        return {"filename": file.filename, "lattice": raw.lattice.matrix.tolist(), "sites": [{"e": s.specie.symbol, "f": s.frac_coords.tolist()} for s in raw]}
    except Exception as exc: raise HTTPException(422, f"Не удалось прочитать CIF: {exc}")

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
