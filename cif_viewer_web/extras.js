"use strict";
// UI extensions kept separate from the renderer core.
const tooltip = document.querySelector('#tooltip');
Object.assign(tooltip.style,{position:'absolute',zIndex:5,padding:'7px 9px',background:'#111e',border:'1px solid #666',borderRadius:'4px',color:'#fff',fontSize:'12px',whiteSpace:'pre-line',pointerEvents:'none'});
const baseDraw = draw;
draw = function(){
  if(S && S.pixelRadii) for(const [element, radius] of Object.entries(S.pixelRadii)) S.mul[element] = radius * 35 / (ra(element) * cam.z);
  baseDraw();
};
const basePanels = panels;
panels = function(){
  basePanels(); if(!S)return; S.pixelRadii ??= {};
  for(const row of document.querySelectorAll('#radii .r')){
    const element=row.querySelector('label').textContent; const old=row.querySelector('input[type=range]'); const output=row.querySelector('output');
    const radius=S.pixelRadii[element] ?? 45; S.pixelRadii[element]=radius;
    old.min=1; old.max=100; old.step=1; old.value=radius; output.value=radius;
    old.oninput=()=>{S.pixelRadii[element]=+old.value;output.value=old.value;draw()};
    const color=document.createElement('input'); color.type='color'; color.value=cl(element); color.oninput=()=>{C[element]=color.value;draw()}; row.prepend(color);
  }
};
can.addEventListener('pointermove',event=>{
  if(!S||drag){tooltip.hidden=true;return} let closest=null;
  for(const atom of S.atoms){const p=pr(atom.p),radius=S.pixelRadii?.[atom.e]??45,d=Math.hypot(event.offsetX-p[0],event.offsetY-p[1]);if(d<=radius&&(!closest||d<closest.d))closest={atom,p,d}}
  if(!closest){tooltip.hidden=true;return} tooltip.hidden=false;tooltip.style.left=(event.offsetX+14)+'px';tooltip.style.top=(event.offsetY+14)+'px';const p=closest.atom.p;tooltip.textContent=`${closest.atom.e}\nx: ${p[0].toFixed(4)} Å\ny: ${p[1].toFixed(4)} Å\nz: ${p[2].toFixed(4)} Å`;
});
document.querySelector('#grow').onclick=()=>{
  if(!S)return;const steps=Math.max(1,Math.min(30,+document.querySelector('#growth-steps').value||1));
  for(let i=0;i<steps;i++){const available=faces();if(!available.length)break;const face=available[Math.floor(Math.random()*available.length)],next=ad(face.c,face.n);S.cells.set(K(next),next)}
  rebuild(); ui.status.textContent=`Случайный рост: ${steps} шагов`;
};
