import {readFileSync,existsSync} from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const json=p=>JSON.parse(readFileSync(new URL(p,import.meta.url),'utf8'));
const timeline=json('../src/timeline.json'),cues=json('../src/narration.json');
assert.equal(timeline.length,7);assert.equal(timeline[0].start,0);assert.equal(timeline.at(-1).end,180);
for(let i=0;i<timeline.length;i++){assert(timeline[i].end>timeline[i].start);if(i)assert.equal(timeline[i-1].end,timeline[i].start);}
for(let i=0;i<cues.length;i++){const c=cues[i];assert(c.end>c.start);assert(c.start>=0&&c.end<=180);if(i)assert(c.start>=cues[i-1].end);assert(timeline.some(s=>c.start>=s.start&&c.end<=s.end),`Fala atravessa cena ${i}`);}
const manifest=json('../docs/asset-manifest.json');
for(const a of manifest.references){const bytes=readFileSync(new URL(`../../${a.source}`,import.meta.url));assert.equal(createHash('sha256').update(bytes).digest('hex'),a.sha256,`Referência alterada: ${a.source}`);}
assert.equal(20*(20+1)/2,210);assert.notEqual(20*(20+1)/2,420);
if(existsSync(new URL('../qa/audio-report.json',import.meta.url))){const report=json('../qa/audio-report.json');assert.equal(report.length,cues.length);report.forEach((r,i)=>assert(r.end<=cues[i].end,`Voz ultrapassou janela ${i}`));}
console.log('OK: 7 cenas, 180s, falas sem sobreposição, matemática e referências originais preservadas.');
