import tkinter as tk
from cif_viewer.core.config import color_for, radius_for
from cif_viewer.core.math_utils import point_in_polygon, project

class Canvas3D(tk.Canvas):
    def __init__(self, parent, on_add_cell, **kwargs):
        super().__init__(parent, bg="#1E1E1E", highlightthickness=0, **kwargs)
        self.builder = None; self.on_add_cell = on_add_cell; self.rot_x, self.rot_y, self.scale = 25., -35., 90.; self.offset = [0., 0.]; self.multipliers = {}; self.hover_face = None; self.drag = None
        self.bind("<Motion>", self._motion); self.bind("<ButtonPress-1>", self._down); self.bind("<B1-Motion>", self._drag); self.bind("<ButtonRelease-1>", self._up); self.bind("<MouseWheel>", self._wheel); self.bind("<Configure>", lambda e: self.redraw())
    def reset_view(self):
        self.rot_x, self.rot_y, self.offset = 25., -35., [0., 0.]
        if self.builder:
            lo, hi = self.builder.bounds(); lengths = [(hi[i]-lo[i]+1) * self.builder.structure.lattice.abc[i] for i in range(3)]; self.scale = min(max(30, self.winfo_width()), max(30, self.winfo_height())) / max(1., max(lengths)*1.7)
        self.redraw()
    def p(self, point):
        origin = self.builder.scene_center() if self.builder else 0
        return project(point - origin, self.rot_x, self.rot_y, self.scale, (self.winfo_width()/2, self.winfo_height()/2), self.offset)
    def set_scene(self, builder, multipliers=None): self.builder, self.multipliers = builder, multipliers or {}; self.redraw()
    def _faces_at(self, x, y):
        candidates=[]
        for cell, normal, verts in self.builder.exterior_faces():
            projected=[self.p(v) for v in verts]; polygon=[p[:2] for p in projected]
            if point_in_polygon((x,y), polygon): candidates.append((sum(p[2] for p in projected)/4, cell, normal, polygon))
        return min(candidates, key=lambda v:v[0]) if candidates else None
    def _motion(self,e):
        if self.drag: return
        found = self._faces_at(e.x,e.y) if self.builder else None; face = (found[1], found[2]) if found else None
        if face != self.hover_face: self.hover_face=face; self.redraw()
    def _down(self,e):
        self.drag=(e.x,e.y,e.state)
        found = self._faces_at(e.x,e.y) if self.builder else None
        self.hover_face = (found[1], found[2]) if found else None
    def _drag(self,e):
        if not self.drag:return
        x,y,state=self.drag; dx,dy=e.x-x,e.y-y
        if state & 0x0001: self.offset[0]+=dx; self.offset[1]+=dy
        else: self.rot_y+=dx*.5; self.rot_x+=dy*.5
        self.drag=(e.x,e.y,state); self.hover_face=None; self.redraw()
    def _up(self,e):
        x,y,state=self.drag or (e.x,e.y,0); moved=abs(e.x-x)+abs(e.y-y)>4; self.drag=None
        if not moved and self.hover_face: self.on_add_cell(self.hover_face); self.hover_face=None
    def _wheel(self,e): self.scale*=1.15 if e.delta>0 else 1/1.15; self.redraw()
    def redraw(self):
        self.delete("all")
        if not self.builder:return
        # Draw the complete cell grid, not a single enclosing parallelepiped.
        for a, b in self.builder.cell_edges():
            p1, p2 = self.p(a), self.p(b)
            self.create_line(p1[0], p1[1], p2[0], p2[1], fill="#777777", width=1, dash=(3,3))
        # Only unoccupied faces are selectable and can receive a neighbour.
        for cell, normal, verts in self.builder.exterior_faces():
            pts=[self.p(v) for v in verts]; flat=[q for p in pts for q in p[:2]]
            selected = (cell, normal) == self.hover_face
            self.create_polygon(*flat, fill="#D22" if selected else "", stipple="gray50" if selected else "", outline="", tags="face")
        bonds=[]
        for a,b in self.builder.bonds:
            p1,p2=self.p(a),self.p(b); bonds.append(((p1[2]+p2[2])/2,p1,p2))
        for _,a,b in sorted(bonds): self.create_line(a[0],a[1],b[0],b[1],fill="#AAAAAA",width=2)
        atoms=[]
        for atom in self.builder.atoms:
            x,y,z=self.p(atom['coords']); element=atom['element']; r=max(3.5,radius_for(element)*self.multipliers.get(element,1)*self.scale/35); atoms.append((z,x,y,r,element))
        for _,x,y,r,el in sorted(atoms):
            self.create_oval(x-r,y-r,x+r,y+r,fill=color_for(el),outline="#000")
            if r>7:self.create_text(x,y,text=el,fill="#000",font=("Arial",max(8,int(r*.6)),"bold"))
