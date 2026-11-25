import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame, interpolate, Easing, staticFile, Img} from 'remotion';
import {Audio} from '@remotion/media';
import timeline from './timeline.json';
import cues from './narration.json';
import {C,font,mathFont} from './theme';
import {Ink} from './Ink';
import './style.css';

export const FPS=30;
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const ease=(t:number,start:number,dur=.8)=>Easing.bezier(.2,.7,.2,1)(clamp((t-start)/dur));
const linear=(t:number,start:number,dur:number)=>clamp((t-start)/dur);
const mix=(a:number,b:number,p:number)=>a+(b-a)*p;
const Fade:React.FC<React.PropsWithChildren<{t:number;at?:number;style?:React.CSSProperties}>>=({t,at=0,children,style})=><div style={{opacity:ease(t,at),transform:`translateY(${(1-ease(t,at))*28}px)`,...style}}>{children}</div>;
const Eyebrow:React.FC<React.PropsWithChildren>=({children})=><div className="eyebrow">{children}</div>;
// Matches the brand-mark / brand-name HTML/CSS in the application (no invented logo).
export const Brand:React.FC<{size?:number;light?:boolean}>=({size=1,light=false})=><div className="brand" style={{transform:`scale(${size})`,transformOrigin:'left center',color:light?C.paper:C.navy}}><div className="brand-mark">C<span>IA</span></div><div className="brand-name">ConfIA</div></div>;
const Badge:React.FC<React.PropsWithChildren<{tone?:'blue'|'green'|'warning'|'red'}>>=({tone='blue',children})=><span className={`badge ${tone}`}>{children}</span>;
const Icon:React.FC<{kind:string;size?:number}>=({kind,size=40})=>{
 const paths:Record<string,React.ReactNode>={
 student:<><circle cx="12" cy="7" r="3"/><path d="M5 22v-3a7 7 0 0 1 14 0v3"/></>,
 teacher:<><path d="M3 4h18v12H3zM8 22l4-6 4 6M7 8h10M7 12h6"/></>,
 management:<><path d="M3 21h19M7 17V9M12 17V3M17 17v-5"/></>,
 pen:<><path d="m4 20 1-6L17 2l5 5L10 19zM14 5l5 5M4 20l6-1"/></>,
 check:<path d="m4 12 5 5L21 5"/>,
 document:<><path d="M14 3H5v19h14V8zM14 3v5h5M8 13h8M8 17h6"/></>,
 arrow:<path d="M3 12h17m-6-6 6 6-6 6"/>,
 shield:<><path d="m12 2 9 4v6q0 7-9 11Q3 19 3 12V6z"/><path d="m7 12 3 3 7-7"/></>
 };
 return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">{paths[kind]??paths.document}</svg>;
};
const Backdrop:React.FC<{t:number}>=({t})=><AbsoluteFill className="backdrop"><svg width="1920" height="1080"><defs><pattern id="dots" width="36" height="36" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill={C.border}/></pattern><radialGradient id="glow"><stop stopColor={C.soft}/><stop offset="1" stopColor={C.bg} stopOpacity="0"/></radialGradient></defs><rect width="1920" height="1080" fill="url(#dots)"/><ellipse cx={1350+80*Math.sin(t*.04)} cy="480" rx="850" ry="610" fill="url(#glow)"/>
 <g fill="none" stroke={C.blue} opacity=".09" transform={`translate(1510 490) rotate(${t*.4})`}><ellipse rx="590" ry="360"/><ellipse rx="540" ry="400" transform="rotate(32)"/><ellipse rx="500" ry="440" transform="rotate(68)"/></g></svg></AbsoluteFill>;
const Notebook:React.FC<{t:number;origin?:boolean;submitted?:boolean}>=({t,origin=false,submitted=false})=>{
 const p1=linear(t,origin?2:4,4.5),p2=linear(t,origin?8:10.5,3.5),p3=linear(t,origin?13:15,2.8);
 return <div className="notebook"><div className="notebook-top"><span><Icon kind="pen" size={23}/> Caderno de Resolução ConfIA</span><span className="paper-tag">ESCRITA DIGITAL</span></div><div className="notebook-question">Calcule a soma dos 20 primeiros<br/>números naturais positivos.</div><svg width="940" height="590" viewBox="0 0 940 590"><g stroke={C.border} opacity=".6">{Array.from({length:6},(_,i)=><path key={i} d={`M60 ${85+i*82}H880`}/>)}</g>
  <Ink text="S = 20(20 + 1)/2" x={76} y={60} scale={1.05} progress={p1} hand={p1<1}/>
  <Ink text="S = 20 × 21" x={76} y={220} scale={1.15} progress={p2} hand={p1===1&&p2<1}/>
  <Ink text="S = 420" x={76} y={380} scale={1.2} progress={p3} hand={p2===1&&p3<1}/>
 </svg><div className="notebook-bottom"><span>Solução do aluno · exemplo</span><span style={{color:submitted?C.green:C.muted}}>{submitted?'Enviada para análise →':'Página 1 de 1'}</span></div></div>;
};
const Challenge:React.FC<{t:number}>=({t})=>{
 const shift=ease(t,18,3);
 return <AbsoluteFill><div className="left-copy" style={{transform:`translateX(${-shift*12}px)`}}><Fade t={t} at={.5}><Eyebrow>01 / O DESAFIO</Eyebrow><h1>Por trás<br/>da resposta,<br/><span>um raciocínio.</span></h1></Fade><Fade t={t} at={8}><p>Cada linha conta uma parte<br/>do caminho do estudante.</p></Fade><Fade t={t} at={18}><div className="question-line">Como compreender<br/>esse percurso?</div></Fade></div>
 <div className="notebook-placement" style={{transform:`perspective(1800px) rotateY(${-9+shift*5}deg) rotateZ(${-3+shift*2}deg) scale(${.87+t*.0015}) translateY(${12*Math.sin(t*.2)}px)`}}><Notebook t={t} origin/></div>
 <Fade t={t} at={1.5} style={{position:'absolute',left:740,top:795}}><div className="student-tag"><Icon kind="student"/><div>ESTUDANTE<span>Escrever. Relacionar. Resolver.</span></div></div></Fade></AbsoluteFill>;
};
const DataParticles:React.FC<{t:number}>=({t})=><svg width="1920" height="1080" style={{position:'absolute'}}>{Array.from({length:26},(_,i)=>{const p=linear(t,1+i*.07,5),a=i*.9;const x=mix(380+i%5*40,960+Math.cos(a)*250,p),y=mix(270+i%6*65,480+Math.sin(a)*180,p);return <g key={i} opacity={Math.sin(p*Math.PI)*.7}><path d={`M${x-35} ${y}h70`} stroke={C.blue} strokeWidth="2"/><circle cx={x} cy={y} r={4} fill={C.blue}/></g>;})}</svg>;
const Solution:React.FC<{t:number}>=({t})=>{
 const p=ease(t,2,4);
 return <AbsoluteFill><DataParticles t={t}/><div style={{position:'absolute',left:170,top:240,opacity:1-p,transform:`translateX(${p*380}px) scale(${1-p*.5})`}}><svg width="800" height="400"><Ink text="S = 20(20 + 1)/2" progress={1} y={40}/><Ink text="S = 420" progress={1} y={210}/></svg></div>
 <div style={{position:'absolute',left:710,top:255,opacity:ease(t,1.5,2),transform:`scale(${mix(.88,1,p)})`}}><Brand size={2.35}/></div>
 <Fade t={t} at={6} style={{position:'absolute',top:440,width:'100%',textAlign:'center'}}><Eyebrow>CONFIABILIDADE E EXPLICABILIDADE</Eyebrow><h1 style={{fontSize:64,marginTop:30}}>Compreender. Analisar. Explicar.</h1></Fade>
 <div className="solution-track">{['Escrita preservada','Raciocínio estruturado','Avaliação explicável'].map((label,i)=><Fade key={label} t={t} at={8+i*2.1}><div className="track-node"><span className="node-number">0{i+1}</span><strong>{label}</strong>{i<2&&<span className="connector"><Icon kind="arrow"/></span>}</div></Fade>)}</div>
 <Fade t={t} at={14} style={{position:'absolute',top:800,width:'100%',textAlign:'center',fontSize:27,color:C.muted}}>Inteligência artificial e métodos formais em etapas distintas.</Fade></AbsoluteFill>;
};
const Resolution:React.FC<{t:number}>=({t})=>{
 const sent=ease(t,20,1.5);
 return <AbsoluteFill><div className="left-copy"><Fade t={t}><Eyebrow>03 / A RESOLUÇÃO</Eyebrow><h1>Um problema.<br/>Três linhas.<br/><span>Um desvio.</span></h1></Fade><Fade t={t} at={5}><p>O ponto de partida<br/>está correto.</p></Fade><Fade t={t} at={13}><div className="question-line">O que mudou<br/>na simplificação?</div></Fade><Fade t={t} at={20}><Badge>Envio ilustrativo</Badge></Fade></div>
 <div className="notebook-placement" style={{transform:`perspective(1800px) rotateY(${-4+sent*4}deg) rotateZ(-1deg) scale(${.88-sent*.035}) translateY(${-sent*14}px)`}}><Notebook t={t} submitted={t>21}/></div>
 <div style={{position:'absolute',left:1020,top:835,width:620,height:7,borderRadius:8,background:C.border,opacity:linear(t,19,.4)}}><div style={{height:'100%',width:`${sent*100}%`,background:C.blue,borderRadius:8}}/></div></AbsoluteFill>;
};
const auditPhases=[{at:0,label:'Identificação dos argumentos',kind:'IA / EXTRAÇÃO',note:'Organizar o que o estudante afirmou.'},{at:7,label:'Estruturação dos passos',kind:'IA / ESTRUTURA',note:'Preservar a sequência e suas relações.'},{at:13,label:'Análise matemática',kind:'ANÁLISE',note:'Examinar a passagem entre duas expressões.'},{at:17,label:'Formalização de proposições',kind:'LINGUAGEM FORMAL',note:'Tornar hipóteses e objetivos explícitos.'},{at:23,label:'Verificação formal com Lean 4',kind:'QUANDO APLICÁVEL',note:'Verificar provas de proposições formalizadas.'}];
const Audit:React.FC<{t:number}>=({t})=>{
 let phase=0; auditPhases.forEach((p,i)=>{if(t>=p.at)phase=i;}); const split=ease(t,16,1.5);
 return <AbsoluteFill><div style={{position:'absolute',left:104,top:145}}><Eyebrow>04 / A AUDITORIA</Eyebrow><h1 style={{fontSize:61,marginTop:22}}>Cada etapa tem uma função.</h1></div>
 <div className="audit-rail">{auditPhases.map((p,i)=><div key={p.label} className={`audit-step ${phase===i?'active':''}`} style={{opacity:t>=p.at?1:.35}}><div className="audit-dot">{i+1}</div><div><small>{p.kind}</small><strong>{p.label}</strong></div></div>)}</div>
 <div className="audit-stage" style={{transform:`translateY(${Math.sin(t*.16)*5}px)`}}>
 {t<17?<><div className="stage-heading"><Badge>{phase<2?'Análise por IA · simulação':'Análise matemática · simulação'}</Badge><span className="tiny">FONTE PRESERVADA</span></div>
  {['S = 20(20 + 1) / 2','S = 20 × 21','S = 420'].map((formula,i)=><div key={formula} className="claim" style={{opacity:ease(t,.8+i*1.3),transform:`translateX(${(1-ease(t,.8+i*1.3))*80}px)`,borderColor:i===1&&t>9?C.yellow:C.border,background:i===1&&t>9?C.warningSoft:C.paper}}><span className="claim-index">A{i+1}</span><span className="math" style={{fontSize:45}}>{formula}</span><span className="claim-label">{['Fórmula inicial','Simplificação','Conclusão'][i]}</span></div>)}
  <Fade t={t} at={9}><div className="warning-callout"><span>!</span><div><strong>A divisão por 2 não foi preservada.</strong><p>O produto está correto. A passagem entre as linhas precisa de revisão.</p></div></div></Fade>
 </>:<><div className="stage-heading"><Badge tone="blue">{phase===3?'Formalização · exemplo':'Lean 4 · verificação ilustrada'}</Badge></div>
  <div className="formal-flow"><span>Proposição selecionada</span><Icon kind="arrow" size={30}/><span>Enunciado formal</span><Icon kind="arrow" size={30}/><span>Prova</span></div>
  <div className="code-panel" style={{opacity:split}}><div className="code-caption">EXEMPLO DE PROPOSIÇÃO • NÃO EXECUTADO</div><code><span>example</span> : (20 * 21 : ℚ) / 2 = 210 := <span>by</span><br/>&nbsp;&nbsp;norm_num</code></div>
  <Fade t={t} at={23}><div className="formal-status"><Icon kind="shield" size={44}/><div><strong>Verificação não executada neste vídeo</strong><p>Lean recebe enunciados e provas formais.<br/>Não recebe manuscritos ou linguagem natural diretamente.</p></div></div></Fade>
  <Fade t={t} at={30}><div className="neutral-callout">Não verificado <b>≠</b> falso<span>Ausência de verificação pode significar resultado inconclusivo.</span></div></Fade>
 </>}
 </div><Fade t={t} at={37} style={{position:'absolute',top:279,left:104,width:1712,textAlign:'center'}}><span className="audit-disclaimer">Demonstração controlada • Sem execução de IA, auditoria ou Lean 4</span></Fade></AbsoluteFill>;
};
const Explanation:React.FC<{t:number}>=({t})=>{
 const restore=ease(t,9,2),result=ease(t,17,2);
 return <AbsoluteFill><div style={{position:'absolute',left:104,top:145}}><Eyebrow>05 / A EXPLICAÇÃO</Eyebrow><h1 style={{fontSize:66}}>Entender o erro.<br/><span>Reconstruir o caminho.</span></h1></div>
 <div className="feedback-message" style={{opacity:ease(t,1)}}><span className="feedback-icon"><Icon kind="check" size={34}/></span><div><strong>Sua fórmula inicial está correta.</strong><p>Ao simplificar, mantenha a divisão por 2.</p><Badge>Devolutiva pedagógica ilustrativa</Badge></div></div>
 <div className="equation-theater" style={{transform:`scale(${1+t*.0008})`}}><div className="equation-s">S =</div><div className="fraction"><div className="numerator">20 × 21</div><div className="fraction-bar" style={{transform:`scaleX(${restore})`}}/><div className="denominator" style={{opacity:restore,transform:`translateY(${(1-restore)*55}px)`}}>2</div></div><div className="equation-equal" style={{opacity:result}}>=</div><div className="equation-result" style={{opacity:result,transform:`translateY(${(1-result)*40}px)`}}>210</div></div>
 <svg width="1920" height="1080" style={{position:'absolute',pointerEvents:'none'}}><path d="M910 744 Q880 812 745 806" fill="none" stroke={C.blue} strokeWidth="2" strokeDasharray="190" strokeDashoffset={190*(1-ease(t,11,1.5))}/></svg>
 <Fade t={t} at={11} style={{position:'absolute',left:435,top:793,fontSize:29,color:C.blue}}>A operação que faltava.</Fade>
 <Fade t={t} at={22} style={{position:'absolute',left:1170,top:750,width:560}}><div className="learning-line">Uma explicação que orienta<br/>a próxima tentativa.</div></Fade></AbsoluteFill>;
};
const Ecosystem:React.FC<{t:number}>=({t})=>{
 const nodes=[{x:115,y:338,kind:'student',title:'ALUNO',subtitle:'Apoio à aprendizagem',body:'Caderno e envio de soluções',state:'Implementado',tone:'green' as const},{x:685,y:390,kind:'teacher',title:'PROFESSOR',subtitle:'Apoio à avaliação matemática',body:'Revisão e decisão docente',state:'Implementado',tone:'green' as const},{x:1255,y:338,kind:'management',title:'GESTÃO',subtitle:'Informações educacionais',body:'Indicadores agregados',state:'Implementado',tone:'green' as const}];
 return <AbsoluteFill><div style={{position:'absolute',left:104,top:145}}><Eyebrow>06 / O ECOSSISTEMA CONFIA</Eyebrow><h1 style={{fontSize:64}}>Três perspectivas. Um compromisso.</h1></div>
 <svg width="1920" height="1080" style={{position:'absolute'}}><path d="M365 480Q960 180 1505 480M365 480Q960 940 1505 480" fill="none" stroke={C.border} strokeWidth="2"/>{Array.from({length:8},(_,i)=>{const a=t*.25+i*Math.PI/4;return <circle key={i} cx={960+580*Math.cos(a)} cy={540+210*Math.sin(a)} r="5" fill={C.blue} opacity=".45"/>;})}</svg>
 {nodes.map((n,i)=><Fade key={n.title} t={t} at={.5+i*.8} style={{position:'absolute',left:n.x,top:n.y}}><div className="ecosystem-card" style={{transform:`translateY(${Math.sin(t*.25+i)*7}px)`}}><div className="eco-icon"><Icon kind={n.kind} size={46}/></div><Eyebrow>{n.title}</Eyebrow><h2>{n.subtitle}</h2><p>{n.body}</p><Badge tone={n.tone}>{n.state} no projeto</Badge></div></Fade>)}
 <Fade t={t} at={12.5} style={{position:'absolute',left:160,top:806,width:1600}}><div className="development-band"><Badge tone="warning">Em desenvolvimento</Badge><span>Histórico permanente de prática</span><i/><span>Feedback do TutorIA: <b>demonstrativo</b></span></div></Fade>
 <div style={{position:'absolute',left:114,top:915,fontSize:21,color:C.muted}}>Piloto TME²: correção assistida • decisão final do avaliador</div></AbsoluteFill>;
};
const institutionAssets:{name:string;src:string|null}[]=[{name:'UFPI',src:null},{name:'FAPEPI',src:null},{name:'SIA',src:null}];
const Closing:React.FC<{t:number}>=({t})=><AbsoluteFill>
 <div style={{position:'absolute',left:600,top:220,opacity:ease(t,.4,1.4),transform:`translateY(${(1-ease(t,.4))*30}px)`}}><Brand size={3.1}/></div>
 <Fade t={t} at={2} style={{position:'absolute',top:425,width:'100%',textAlign:'center'}}><h1 style={{fontSize:48,margin:0}}>ConfIA — Confiabilidade e Explicabilidade.</h1></Fade>
 <Fade t={t} at={4} style={{position:'absolute',left:290,top:540,width:1340,textAlign:'center'}}><p style={{fontSize:43,lineHeight:1.45,color:C.navy}}>Pesquisa, matemática e inteligência artificial<br/>para transformar a avaliação e a aprendizagem.</p></Fade>
 <Fade t={t} at={6} style={{position:'absolute',left:470,top:795,width:980}}><div className="institution-row">{institutionAssets.map(a=>a.src?<Img key={a.name} src={staticFile(a.src)} style={{maxWidth:250,maxHeight:100,objectFit:'contain'}}/>:<span key={a.name}>{a.name}</span>)}</div></Fade>
 <div style={{position:'absolute',bottom:0,width:`${ease(t,0,5)*100}%`,height:8,display:'flex'}}>{[C.blue,C.yellow,C.stripRed,C.green].map((c,i)=><div key={c} style={{background:c,flex:[7,2,2,3][i]}}/>)}</div>
 </AbsoluteFill>;
const sceneComponents=[Challenge,Solution,Resolution,Audit,Explanation,Ecosystem,Closing];
const Scene:React.FC<{index:number}>=({index})=>{const frame=useCurrentFrame(),t=frame/FPS;const duration=timeline[index].end-timeline[index].start;const Component=sceneComponents[index];const opacity=Math.min(ease(t,0,.8),index===6?1:1-linear(t,duration-.6,.6));return <AbsoluteFill style={{opacity,transform:`translateX(${(1-ease(t,0,.9))*24}px)`}}><Component t={t}/></AbsoluteFill>;};
export const Film:React.FC<{captions?:boolean;audio?:boolean}>=({captions=true,audio=true})=>{
 const f=useCurrentFrame(),t=f/FPS;
 const cue=cues.find(c=>t>=c.start&&t<c.end);
 const scene=timeline.find(s=>t>=s.start&&t<s.end)??timeline[6];
 return <AbsoluteFill style={{fontFamily:font,background:C.bg,color:C.ink}}><Backdrop t={t}/>
  <div className="top-rule"/><div className="masthead"><Brand size={.7}/><span>PESQUISA • MATEMÁTICA • INTELIGÊNCIA ARTIFICIAL</span><span className="chapter-counter">{String(scene.id).padStart(2,'0')} / 07</span></div>
  {timeline.map((s,i)=><Sequence key={s.id} from={s.start*FPS} durationInFrames={(s.end-s.start)*FPS}><Scene index={i}/></Sequence>)}
  <div className="illustrative-label">Demonstração ilustrativa do funcionamento do ConfIA</div>
  {captions&&cue&&<div className="captions"><span>{cue.text}</span></div>}
  <div className="film-progress" style={{width:`${t/180*100}%`}}/>
  {audio&&<Audio src={staticFile('audio/mix.wav')}/>}
 </AbsoluteFill>;
};
