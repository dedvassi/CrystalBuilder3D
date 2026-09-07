import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import math
import numpy as np
from pathlib import Path

try:
    from pymatgen.core import Structure
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
except ImportError:
    Structure = None
    SpacegroupAnalyzer = None


class CIFViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CIF Visualizer (VESTA Style)")
        self.root.geometry("1200x800")

        self.base_structure = None
        self.supercell_structure = None
        self.rendered_atoms = []
        self.rendered_bonds = []
        self.filename = "Файл не выбран"

        # Параметры камеры (вращение и зум)
        self.rot_x = 25.0
        self.rot_y = -35.0
        self.scale = 90.0
        self.offset_x = 0.0
        self.offset_y = 0.0

        self.mouse_down = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.setup_ui()

    def setup_ui(self):
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        btn_open = ttk.Button(control_frame, text="📁 Открыть CIF", command=self.open_cif)
        btn_open.pack(side=tk.LEFT, padx=5)

        self.file_label = ttk.Label(control_frame, text=self.filename, font=("Arial", 10, "bold"))
        self.file_label.pack(side=tk.LEFT, padx=10)

        ttk.Label(control_frame, text="Supercell X:").pack(side=tk.LEFT, padx=(20, 2))
        self.nx_var = tk.IntVar(value=1)
        ttk.Spinbox(control_frame, from_=1, to=5, width=3, textvariable=self.nx_var, command=self.rebuild).pack(side=tk.LEFT)

        ttk.Label(control_frame, text="Y:").pack(side=tk.LEFT, padx=(5, 2))
        self.ny_var = tk.IntVar(value=1)
        ttk.Spinbox(control_frame, from_=1, to=5, width=3, textvariable=self.ny_var, command=self.rebuild).pack(side=tk.LEFT)

        ttk.Label(control_frame, text="Z:").pack(side=tk.LEFT, padx=(5, 2))
        self.nz_var = tk.IntVar(value=1)
        ttk.Spinbox(control_frame, from_=1, to=5, width=3, textvariable=self.nz_var, command=self.rebuild).pack(side=tk.LEFT)

        ttk.Label(control_frame, text="R_связи (Å):").pack(side=tk.LEFT, padx=(20, 2))
        self.cutoff_var = tk.DoubleVar(value=3.2)
        ttk.Spinbox(control_frame, from_=1.0, to=6.0, increment=0.1, width=5, textvariable=self.cutoff_var, command=self.rebuild).pack(side=tk.LEFT)

        btn_reset = ttk.Button(control_frame, text="Сбросить вид", command=self.reset_camera)
        btn_reset.pack(side=tk.LEFT, padx=15)

        self.canvas = tk.Canvas(self.root, bg="#1E1E1E", highlightthickness=0)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)
        self.root.bind("<Configure>", lambda e: self.redraw())

        self.status_var = tk.StringVar(value="Готов. Откройте CIF файл.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def open_cif(self):
        if Structure is None:
            messagebox.showerror("Ошибка", "Библиотека pymatgen не установлена!\nУстановите: pip install pymatgen")
            return

        filename = filedialog.askopenfilename(
            title="Выберите CIF файл",
            filetypes=[("CIF files", "*.cif"), ("Все файлы", "*.*")]
        )

        if not filename:
            return

        try:
            raw_struct = Structure.from_file(filename)
            try:
                sga = SpacegroupAnalyzer(raw_struct)
                self.base_structure = sga.get_conventional_standard_structure()
                sg_symbol = sga.get_space_group_symbol()
                sg_num = sga.get_space_group_number()
                info_msg = f"Пространственная группа: {sg_symbol} (#{sg_num})"
            except Exception:
                self.base_structure = raw_struct
                info_msg = "Симметрия не определена, используется исходный файл."

            self.filename = Path(filename).name
            self.file_label.config(text=self.filename)
            self.status_var.set(f"Загружено: {self.filename} | {info_msg}")

            self.rebuild(reset_view=True)

        except Exception as exc:
            messagebox.showerror("Ошибка чтения CIF", str(exc))

    def rebuild(self, reset_view=False):
        if self.base_structure is None:
            return

        nx = self.nx_var.get()
        ny = self.ny_var.get()
        nz = self.nz_var.get()
        cutoff = self.cutoff_var.get()

        self.supercell_structure = self.base_structure * (nx, ny, nz)

        # 1. Генерация атомов (VESTA-style)
        unique_atoms = {}
        lat = self.base_structure.lattice
        a_vec, b_vec, c_vec = lat.matrix
        tol = 1e-3

        for site in self.base_structure:
            fx, fy, fz = site.frac_coords
            
            max_ix = nx if abs(fx) < tol or abs(fx - 1.0) < tol else nx - 1
            max_iy = ny if abs(fy) < tol or abs(fy - 1.0) < tol else ny - 1
            max_iz = nz if abs(fz) < tol or abs(fz - 1.0) < tol else nz - 1

            for ix in range(max_ix + 1):
                for iy in range(max_iy + 1):
                    for iz in range(max_iz + 1):
                        cart_pos = site.coords + ix * a_vec + iy * b_vec + iz * c_vec
                        elem = site.specie.symbol if hasattr(site.specie, 'symbol') else str(site.specie)
                        
                        key = (elem, round(cart_pos[0], 3), round(cart_pos[1], 3), round(cart_pos[2], 3))
                        if key not in unique_atoms:
                            unique_atoms[key] = {
                                "element": elem,
                                "coords": cart_pos
                            }

        self.rendered_atoms = list(unique_atoms.values())

        # 2. Поиск связей напрямую между всеми отрисованными атомами по расстоянию
        self.rendered_bonds = []
        n_atoms = len(self.rendered_atoms)
        
        for i in range(n_atoms):
            for j in range(i + 1, n_atoms):
                atom1 = self.rendered_atoms[i]
                atom2 = self.rendered_atoms[j]
                
                # Не рисуем связи между атомами одного типа
                if atom1["element"] == atom2["element"]:
                    continue
                
                p1 = atom1["coords"]
                p2 = atom2["coords"]
                
                dist = np.linalg.norm(p1 - p2)
                if 1e-3 < dist <= cutoff:
                    self.rendered_bonds.append((p1, p2))

        if reset_view:
            self.reset_camera()

        self.redraw()

    def reset_camera(self):
        self.rot_x = 25.0
        self.rot_y = -35.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        
        if self.base_structure is not None:
            lat = self.base_structure.lattice
            max_dim = max(lat.a, lat.b, lat.c) * max(self.nx_var.get(), self.ny_var.get(), self.nz_var.get())
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            if w > 10 and h > 10:
                self.scale = min(w, h) / (max_dim * 1.6)
            else:
                self.scale = 90.0
        self.redraw()

    def project(self, x, y, z):
        rad_x = math.radians(self.rot_x)
        rad_y = math.radians(self.rot_y)

        x1 = x * math.cos(rad_y) + z * math.sin(rad_y)
        y1 = y
        z1 = -x * math.sin(rad_y) + z * math.cos(rad_y)

        x2 = x1
        y2 = y1 * math.cos(rad_x) - z1 * math.sin(rad_x)
        z2 = y1 * math.sin(rad_x) + z1 * math.cos(rad_x)

        cx = self.canvas.winfo_width() / 2 + self.offset_x
        cy = self.canvas.winfo_height() / 2 + self.offset_y

        px = cx + x2 * self.scale
        py = cy - y2 * self.scale
        return px, py, z2

    def redraw(self):
        self.canvas.delete("all")
        if self.base_structure is None:
            return

        nx, ny, nz = self.nx_var.get(), self.ny_var.get(), self.nz_var.get()
        lat = self.base_structure.lattice
        a, b, c = lat.matrix[0], lat.matrix[1], lat.matrix[2]

        total_a = a * nx
        total_b = b * ny
        total_c = c * nz

        cell_edges = []
        for ix in range(nx + 1):
            for iy in range(ny + 1):
                p_start = ix * a + iy * b
                cell_edges.append((p_start, p_start + total_c))
        for ix in range(nx + 1):
            for iz in range(nz + 1):
                p_start = ix * a + iz * c
                cell_edges.append((p_start, p_start + total_b))
        for iy in range(ny + 1):
            for iz in range(nz + 1):
                p_start = iy * b + iz * c
                cell_edges.append((p_start, p_start + total_a))

        for p1, p2 in cell_edges:
            x1, y1, _ = self.project(p1[0], p1[1], p1[2])
            x2, y2, _ = self.project(p2[0], p2[1], p2[2])
            self.canvas.create_line(x1, y1, x2, y2, fill="#555555", width=1, dash=(3, 3))

        drawn_bonds = []
        for p1, p2 in self.rendered_bonds:
            sx1, sy1, sz1 = self.project(p1[0], p1[1], p1[2])
            sx2, sy2, sz2 = self.project(p2[0], p2[1], p2[2])
            drawn_bonds.append(((sz1 + sz2) / 2.0, sx1, sy1, sx2, sy2))

        drawn_bonds.sort(key=lambda item: item[0])
        for _, sx1, sy1, sx2, sy2 in drawn_bonds:
            self.canvas.create_line(sx1, sy1, sx2, sy2, fill="#AAAAAA", width=2)

        atom_list = []
        for atom in self.rendered_atoms:
            pos = atom["coords"]
            sx, sy, sz = self.project(pos[0], pos[1], pos[2])
            elem = atom["element"]
            radius = self.get_atom_radius(elem) * (self.scale / 35.0)
            radius = max(3.5, radius)
            color = self.get_atom_color(elem)
            atom_list.append((sz, sx, sy, radius, color, elem))

        atom_list.sort(key=lambda item: item[0])

        for sz, sx, sy, r, color, elem in atom_list:
            self.canvas.create_oval(
                sx - r, sy - r, sx + r, sy + r,
                fill=color, outline="#000000", width=1
            )
            if r > 7:
                self.canvas.create_text(sx, sy, text=elem, fill="#000000", font=("Arial", int(max(8, r * 0.6)), "bold"))

    @staticmethod
    def get_atom_radius(element):
        return {
            "H": 0.35, "C": 0.55, "N": 0.55, "O": 0.55, "F": 0.50,
            "Na": 0.70, "Mg": 0.65, "Al": 0.65, "Si": 0.60, "U": 0.95, "Th": 0.95
        }.get(element, 0.65)

    @staticmethod
    def get_atom_color(element):
        return {
            "H": "#FFFFFF", "C": "#444444", "N": "#3050F8", "O": "#FF0D0D",
            "F": "#90E050", "Na": "#AB5CF2", "Mg": "#8AFF00", "U": "#008B8B", "Th": "#006666"
        }.get(element, "#CCCCCC")

    def on_mouse_down(self, event):
        self.mouse_down = True
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y

    def on_mouse_drag(self, event):
        if not self.mouse_down:
            return
        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y

        if event.state & 0x0001:
            self.offset_x += dx
            self.offset_y += dy
        else:
            self.rot_y += dx * 0.5
            self.rot_x += dy * 0.5

        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.redraw()

    def on_mouse_up(self, event):
        self.mouse_down = False

    def on_mouse_wheel(self, event):
        if event.delta > 0 or event.num == 4:
            self.scale *= 1.15
        elif event.delta < 0 or event.num == 5:
            self.scale /= 1.15
        self.redraw()


if __name__ == "__main__":
    root = tk.Tk()
    app = CIFViewerApp(root)
    root.mainloop()