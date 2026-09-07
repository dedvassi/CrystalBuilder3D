"use strict";
// UI extensions kept separate from the renderer core.
const tooltip = document.querySelector('#tooltip');
Object.assign(tooltip.style,{position:'absolute',zIndex:5,padding:'7px 9px',background:'#111e',border:'1px solid #666',borderRadius:'4px',color:'#fff',fontSize:'12px',whiteSpace:'pre-line',pointerEvents:'none'});
const basePanels = panels;
panels = function(){
  basePanels(); if(!S)return;
  for(const row of document.querySelectorAll('#radii .r')){
    const element=row.querySelector('label').textContent; const old=row.querySelector('input[type=range]'); const output=row.querySelector('output');
    const percent=Math.round((S.mul[element] ?? 1)*100);
    old.min=20; old.max=100; old.step=1; old.value=percent; output.value=percent+'%';
    old.oninput=()=>{S.mul[element]=+old.value/100;output.value=old.value+'%';draw()};
    const color=document.createElement('input'); color.type='color'; color.value=cl(element); color.oninput=()=>{C[element]=color.value;draw()}; row.prepend(color);
  }
};
can.addEventListener('pointermove',event=>{
  if(!S||drag){tooltip.hidden=true;return} let closest=null;
  for(const atom of S.atoms){const p=pr(atom.p),radius=Math.max(5,ra(atom.e)*(S.mul[atom.e]||1)*cam.z/35),d=Math.hypot(event.offsetX-p[0],event.offsetY-p[1]);if(d<=radius&&(!closest||d<closest.d))closest={atom,p,d}}
  if(!closest){tooltip.hidden=true;return} tooltip.hidden=false;tooltip.style.left=(event.offsetX+14)+'px';tooltip.style.top=(event.offsetY+14)+'px';const p=closest.atom.p;tooltip.textContent=`${closest.atom.e}\nx: ${p[0].toFixed(4)} Å\ny: ${p[1].toFixed(4)} Å\nz: ${p[2].toFixed(4)} Å`;
});
document.querySelector('#grow').onclick=async()=>{
  if(!S)return; const button=document.querySelector('#grow'); const steps=Math.max(1,Math.min(30,+document.querySelector('#growth-steps').value||1));
  button.disabled=true;
  for(let i=0;i<steps;i++){
    const available=faces(); if(!available.length)break;
    const face=available[Math.floor(Math.random()*available.length)],next=ad(face.c,face.n); S.cells.set(K(next),next);
    rebuild(); ui.status.textContent=`Рост кристалла: ${i+1} / ${steps}`;
    await new Promise(resolve=>setTimeout(resolve,180));
  }
  button.disabled=false; ui.status.textContent=`Случайный рост завершён: ${steps} шагов`;
};
