from tkinter import ttk
from cif_viewer.core.config import color_for

class ElementsPanel(ttk.LabelFrame):
    def __init__(self, parent, on_change):
        super().__init__(parent, text="Радиусы атомов", padding=8); self.on_change = on_change; self.vars = {}
    def set_elements(self, elements):
        for child in self.winfo_children(): child.destroy()
        self.vars = {}
        for element in elements:
            row = ttk.Frame(self); row.pack(fill="x", pady=2); ttk.Label(row, text="●", foreground=color_for(element)).pack(side="left"); ttk.Label(row, text=element, width=3).pack(side="left")
            var = ttk.Scale(row, from_=0.1, to=3.0, orient="horizontal", command=lambda _v: self.on_change()); var.set(1.0); var.pack(side="left", fill="x", expand=True, padx=3); self.vars[element] = var
    def multipliers(self): return {element: var.get() for element, var in self.vars.items()}
