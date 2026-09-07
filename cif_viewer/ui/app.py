import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from cif_viewer.core.cif_loader import load_cif
from cif_viewer.core.structure_builder import StructureBuilder
from .canvas_3d import Canvas3D
from .stats_panel import StatsPanel
from .elements_panel import ElementsPanel

class CIFViewerApp:
    def __init__(self, root):
        self.root=root; root.title("CrystalBuilder3D — CIF Visualizer"); root.geometry("1280x820"); self.builder=None
        top=ttk.Frame(root,padding=8); top.pack(fill="x"); ttk.Button(top,text="📁 Открыть CIF",command=self.open_cif).pack(side="left"); ttk.Button(top,text="Сбросить вид",command=lambda:self.canvas.reset_view()).pack(side="left",padx=7); ttk.Label(top,text="Cutoff связей (Å):").pack(side="left",padx=(15,2)); self.cutoff=tk.DoubleVar(value=3.2); ttk.Spinbox(top,from_=1,to=6,increment=.1,width=5,textvariable=self.cutoff,command=self.rebuild).pack(side="left"); self.file=tk.StringVar(value="Файл не выбран"); ttk.Label(top,textvariable=self.file).pack(side="left",padx=12)
        body=ttk.Frame(root); body.pack(fill="both",expand=True); side=ttk.Frame(body,padding=8,width=240); side.pack(side="left",fill="y"); side.pack_propagate(False); self.stats=StatsPanel(side); self.stats.pack(fill="x"); self.elements=ElementsPanel(side,self.redraw); self.elements.pack(fill="x",pady=10); self.canvas=Canvas3D(body,self.add_cell); self.canvas.pack(side="left",fill="both",expand=True)
        self.status=tk.StringVar(value="Готов. Откройте CIF файл."); ttk.Label(root,textvariable=self.status,relief="sunken",anchor="w",padding=4).pack(fill="x",side="bottom")
    def open_cif(self):
        name=filedialog.askopenfilename(title="Выберите CIF",filetypes=[("CIF", "*.cif"),("Все файлы","*.*")])
        if not name:return
        try:
            structure, filename, symmetry=load_cif(name); self.builder=StructureBuilder(structure); self.file.set(filename); self.elements.set_elements(self.builder.elements); self.rebuild(); self.canvas.reset_view(); self.status.set(f"Загружено: {filename} | Пространственная группа: {symmetry}")
        except Exception as exc: messagebox.showerror("Ошибка чтения CIF",str(exc))
    def rebuild(self):
        if self.builder: self.builder.rebuild(self.cutoff.get()); self.redraw()
    def redraw(self):
        if self.builder: self.canvas.set_scene(self.builder,self.elements.multipliers()); self.stats.update_stats(self.builder.statistics())
    def add_cell(self,face):
        cell, normal = face
        self.builder.add_cell(cell, normal); self.rebuild()
        self.status.set(f"Добавлена ячейка рядом с {cell} по нормали {normal}")
