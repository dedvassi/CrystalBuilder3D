from pathlib import Path
try:
    from pymatgen.core import Structure
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
except ImportError:
    Structure = SpacegroupAnalyzer = None

def load_cif(filename):
    if Structure is None: raise RuntimeError("pymatgen не установлен. Выполните: pip install pymatgen")
    raw = Structure.from_file(filename)
    try:
        analyzer = SpacegroupAnalyzer(raw)
        structure = analyzer.get_conventional_standard_structure()
        symmetry = f"{analyzer.get_space_group_symbol()} (#{analyzer.get_space_group_number()})"
    except Exception:
        structure, symmetry = raw, "не определена — используется исходная ячейка"
    return structure, Path(filename).name, symmetry
