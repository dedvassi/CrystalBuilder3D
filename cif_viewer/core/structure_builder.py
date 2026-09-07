from collections import Counter
import numpy as np

class StructureBuilder:
    INITIAL_SIZE = 1

    def __init__(self, structure):
        self.structure = structure; self.atoms = []; self.bonds = []
        # NaCl's conventional CIF cell already contains the visible 2×2 atomic
        # motif.  Repeating it twice incorrectly turns that motif into 4×4.
        # Afterwards active_cells stays a free-form set: clicks add one cell.
        self.reset()

    @property
    def elements(self): return sorted({site.specie.symbol for site in self.structure})
    def reset(self):
        size = self.INITIAL_SIZE
        self.active_cells = {(x, y, z) for x in range(size) for y in range(size) for z in range(size)}
    def add_cell(self, cell, normal):
        """Attach exactly one unit cell to one exposed face."""
        neighbour = tuple(cell[i] + normal[i] for i in range(3))
        self.active_cells.add(neighbour)
    def bounds(self):
        values = list(self.active_cells)
        return tuple(min(v[i] for v in values) for i in range(3)), tuple(max(v[i] for v in values) for i in range(3))
    def rebuild(self, cutoff):
        lattice = self.structure.lattice.matrix; atoms = {}; tol = 1e-3
        for cell in self.active_cells:
            for site in self.structure:
                # A site at fractional 0 (or 1) lives on a cell boundary.
                # Render it on both sides of this active cell, just as the
                # monolith's max_ix/max_iy/max_iz loops did for a supercell.
                frac = site.frac_coords
                offsets = [range(2) if abs(value) < tol or abs(value - 1.0) < tol else range(1)
                           for value in frac]
                for dx in offsets[0]:
                    for dy in offsets[1]:
                        for dz in offsets[2]:
                            shift = (np.asarray(cell) + (dx, dy, dz)) @ lattice
                            pos = site.coords + shift; elem = site.specie.symbol
                            key = (elem, *np.round(pos, 3))
                            atoms.setdefault(key, {"element": elem, "coords": pos})
        self.atoms = list(atoms.values()); self.bonds = []
        if len(self.atoms) < 2: return
        coords = np.array([a["coords"] for a in self.atoms]); elements = np.array([a["element"] for a in self.atoms])
        # Vectorized pair distance matrix avoids Python O(N²) loops.
        distances = np.linalg.norm(coords[:, None] - coords[None, :], axis=2)
        rows, cols = np.where(np.triu((distances > 1e-3) & (distances <= cutoff) & (elements[:, None] != elements[None, :]), 1))
        self.bonds = [(coords[i], coords[j]) for i, j in zip(rows, cols)]
    def statistics(self): return Counter(a["element"] for a in self.atoms)
    def _cell_corners(self, cell):
        lat = self.structure.lattice.matrix
        return {(x, y, z): (np.asarray(cell, float) + (x, y, z)) @ lat
                for x in (0, 1) for y in (0, 1) for z in (0, 1)}

    def exterior_faces(self):
        """Every individually selectable face not shared with another active cell."""
        faces = [((-1,0,0), [(0,0,0),(0,1,0),(0,1,1),(0,0,1)]), ((1,0,0), [(1,0,0),(1,0,1),(1,1,1),(1,1,0)]), ((0,-1,0), [(0,0,0),(0,0,1),(1,0,1),(1,0,0)]), ((0,1,0), [(0,1,0),(1,1,0),(1,1,1),(0,1,1)]), ((0,0,-1), [(0,0,0),(1,0,0),(1,1,0),(0,1,0)]), ((0,0,1), [(0,0,1),(0,1,1),(1,1,1),(1,0,1)])]
        result = []
        for cell in self.active_cells:
            corners = self._cell_corners(cell)
            for normal, indices in faces:
                neighbour = tuple(cell[i] + normal[i] for i in range(3))
                if neighbour not in self.active_cells:
                    result.append((cell, normal, [corners[index] for index in indices]))
        return result

    def cell_edges(self):
        """Unique unit-cell edges, including interior grid lines."""
        edges = {}
        pairs = [((0,0,0),(1,0,0)), ((0,0,0),(0,1,0)), ((0,0,0),(0,0,1)), ((1,1,0),(0,1,0)), ((1,1,0),(1,0,0)), ((1,1,1),(0,1,1)), ((1,1,1),(1,0,1)), ((1,1,1),(1,1,0)), ((0,0,1),(1,0,1)), ((0,0,1),(0,1,1)), ((1,0,0),(1,0,1)), ((0,1,0),(0,1,1))]
        for cell in self.active_cells:
            corners = self._cell_corners(cell)
            for a, b in pairs:
                key = tuple(sorted((tuple(np.round(corners[a], 6)), tuple(np.round(corners[b], 6)))))
                edges[key] = (corners[a], corners[b])
        return list(edges.values())

    def scene_center(self):
        lo, hi = self.bounds()
        return ((np.asarray(lo, float) + np.asarray(hi, float) + 1) / 2) @ self.structure.lattice.matrix
