import React from 'react';
import {C} from './theme';
// Original single-stroke glyph geometry, used to simulate pen input, not a font or logo.
type Point=[number,number];
const glyphs:Record<string,Point[][]>={
 'S':[[[35,7],[27,2],[12,3],[4,12],[7,22],[29,32],[35,42],[30,54],[14,59],[3,53]]],
 '0':[[[21,2],[8,6],[2,24],[3,44],[13,57],[25,58],[35,45],[37,24],[32,7],[21,2]]],
 '1':[[[8,15],[22,2],[20,58]],[[7,59],[34,59]]],
 '2':[[[3,13],[10,4],[25,2],[35,10],[35,20],[25,32],[3,57],[37,58]]],
 '3':[[[4,6],[32,3],[20,25],[30,27],[37,36],[33,51],[22,58],[8,56],[2,50]]],
 '4':[[[30,2],[2,39],[38,39]],[[30,2],[28,59]]],
 '5':[[[35,3],[7,3],[5,29],[19,24],[31,28],[36,40],[30,54],[15,59],[3,52]]],
 '6':[[[32,4],[20,2],[8,14],[2,38],[7,53],[21,59],[33,52],[36,38],[27,28],[11,29],[3,38]]],
 '7':[[[2,3],[36,3],[22,29],[13,59]]],
 '8':[[[21,2],[6,6],[4,18],[17,29],[32,38],[34,49],[23,59],[9,56],[2,46],[8,35],[29,22],[34,12],[28,3],[21,2]]],
 '9':[[[33,27],[9,29],[2,18],[6,5],[22,2],[34,9],[34,30],[28,48],[15,59]]],
 '+':[[[20,12],[19,48]],[[2,31],[38,31]]],
 '=':[[[2,22],[37,22]],[[2,39],[36,39]]],
 '×':[[[4,14],[34,48]],[[35,13],[4,49]]],
 '/':[[[36,0],[2,61]]],
 '(':[[[28,0],[16,13],[11,31],[13,49],[24,63]]],
 ')':[[[10,0],[22,15],[25,33],[20,51],[9,63]]],
 '.':[[[19,56],[20,57]]],
 'n':[[[3,23],[2,58],[6,35],[18,24],[29,25],[34,36],[32,58]]]
};
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
export const Ink:React.FC<{text:string;progress:number;x?:number;y?:number;scale?:number;color?:string;hand?:boolean}>=({text,progress,x=0,y=0,scale=1,color=C.navy,hand=false})=>{
 const strokes:{pts:Point[];length:number}[]=[];
 let cursor=0;
 for(const char of text){
  if(char===' '){cursor+=22;continue;}
  for(const pts of glyphs[char]??[]){const shifted=pts.map(([a,b])=>[a+cursor,b] as Point);strokes.push({pts:shifted,length:shifted.slice(1).reduce((n,p,i)=>n+Math.hypot(p[0]-shifted[i][0],p[1]-shifted[i][1]),0)});}
  cursor+=48;
 }
 const total=strokes.reduce((n,s)=>n+s.length,0);let remaining=clamp(progress)*total;let tip:Point=[0,0];
 const paths=strokes.map((s,i)=>{
  const amount=clamp(remaining/s.length); remaining-=s.length;
  if(amount>0){let d=amount*s.length;tip=s.pts[s.pts.length-1];for(let j=1;j<s.pts.length;j++){const a=s.pts[j-1],b=s.pts[j],len=Math.hypot(b[0]-a[0],b[1]-a[1]);if(d<=len){tip=[a[0]+(b[0]-a[0])*d/len,a[1]+(b[1]-a[1])*d/len];break;}d-=len;}}
  return <polyline key={i} opacity={amount>0?1:0} points={s.pts.map(p=>p.join(',')).join(' ')} fill="none" stroke={color} strokeWidth={2.8} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={s.length} strokeDashoffset={s.length*(1-amount)}/>;
 });
 return <g transform={`translate(${x} ${y}) scale(${scale})`}>{paths}{hand&&progress>0&&progress<1&&<g transform={`translate(${tip[0]} ${tip[1]})`}>
  <path d="M45 -49 Q77 -59 103 -24 L159 38 L110 75 L73 34 Q53 30 42 18 L12 -9 Q4 -22 14 -27 Q22 -30 38 -15 L26 -51 Q22 -64 31 -65 Q39 -65 45 -49" fill={C.soft} stroke={C.navy} strokeWidth="2"/>
  <path d="M0 0 L54 -84 Q58 -91 64 -86 Q70 -83 65 -75 L7 5Z" fill={C.navy}/><path d="M0 0 L7 5 L-4 9Z" fill={C.blue}/>
  <path d="M46 -44 Q29 -61 20 -51 Q15 -46 26 -33 L43 -16" fill={C.soft} stroke={C.navy} strokeWidth="2"/>
 </g>}</g>;
};
