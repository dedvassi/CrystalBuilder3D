import tkinter as tk
from tkinter import ttk
from cif_viewer.core.config import color_for

class StatsPanel(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Статистика", padding=8); self.total = ttk.Label(self, text="Всего атомов: 0"); self.total.pack(anchor="w"); self.rows = ttk.Frame(self); self.rows.pack(fill="x", pady=(6,0))
    def update_stats(self, counts):
        self.total.config(text=f"Всего атомов: {sum(counts.values())}")
        for child in self.rows.winfo_children(): child.destroy()
        for element, count in sorted(counts.items()):
            row = ttk.Frame(self.rows); row.pack(fill="x", pady=1); tk.Label(row, bg=color_for(element), width=2, relief="solid").pack(side="left", padx=(0,5)); ttk.Label(row, text=f"{element}: {count}").pack(side="left")
