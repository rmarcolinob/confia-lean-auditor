import {bundle} from '@remotion/bundler';
import {selectComposition, renderMedia, renderStill, openBrowser} from '@remotion/renderer';
import {mkdirSync, existsSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
const mode=process.argv[2]??'preview';
const allowed=['stills','sample','preview','full'];
if(!allowed.includes(mode))throw new Error(`Modo inválido: ${mode}`);
const root=resolve(import.meta.dirname,'..');process.chdir(root);
mkdirSync('output',{recursive:true});mkdirSync('qa',{recursive:true});
const chrome=process.env.CHROME_EXECUTABLE??(existsSync('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')?'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome':undefined);
const serveUrl=await bundle({entryPoint:resolve('src/index.ts'),outDir:resolve('.cache/bundle'),publicDir:resolve('public')});
const browser=await openBrowser('chrome',{browserExecutable:chrome});
try{
 const inputProps={captions:true,audio:mode!=='stills'};
 if(inputProps.audio&&!existsSync('public/audio/mix.wav'))throw new Error('Execute npm run audio ou forneça public/audio/mix.wav (180s).');
 const composition=await selectComposition({serveUrl,id:'ConfIA',puppeteerInstance:browser,inputProps});
 if(mode==='stills'){
  const times=process.env.QA_TIMES?process.env.QA_TIMES.split(',').map(Number):[5,17,32,40,51,61,68,75,83,90,98,104,112,119,127,135,142,150,162,175];
  for(const s of times){await renderStill({serveUrl,composition,puppeteerInstance:browser,inputProps,frame:s*30,output:resolve(`qa/frame-${String(s).padStart(3,'0')}.png`),imageFormat:'png'});console.log(`Quadro ${s}s`);}
  writeFileSync('qa/frames.json',JSON.stringify(times));
 }else{
  // Sample focuses on handwriting and maths before the full-length render.
  const ranges={sample:[51*30,57*30-1],preview:[0,30*30-1],full:[0,5400-1]};
  const out={sample:'qa/amostra-6s.mp4',preview:'output/confia-previa-30s.mp4',full:'output/confia-institucional-180s.mp4'}[mode];
  let logged=-1;
  await renderMedia({serveUrl,composition,puppeteerInstance:browser,inputProps,codec:'h264',audioCodec:'aac',audioBitrate:'192k',crf:18,pixelFormat:'yuv420p',imageFormat:'jpeg',jpegQuality:95,concurrency:4,frameRange:ranges[mode],outputLocation:resolve(out),onProgress:({progress})=>{const n=Math.floor(progress*20);if(n>logged){logged=n;console.log(`${mode}: ${Math.round(progress*100)}%`);}}});
  const probe=spawnSync('ffprobe',['-v','error','-show_streams','-show_format','-of','json',out],{encoding:'utf8'});
  if(probe.status!==0)throw new Error(probe.stderr);
  writeFileSync(`qa/${mode}-ffprobe.json`,probe.stdout);
  console.log(resolve(out));
  if(mode==='full'){
   // Exact first 900 video frames, copied without image recompression.
   const preview='output/confia-previa-30s.mp4';
   const cut=spawnSync('ffmpeg',['-v','error','-y','-i',out,'-t','30','-frames:v','900','-c','copy','-movflags','+faststart',preview],{encoding:'utf8'});
   if(cut.status!==0)throw new Error(cut.stderr);
   const previewProbe=spawnSync('ffprobe',['-v','error','-show_streams','-show_format','-of','json',preview],{encoding:'utf8'});
   if(previewProbe.status!==0)throw new Error(previewProbe.stderr);
   writeFileSync('qa/preview-ffprobe.json',previewProbe.stdout);
   console.log(`Prévia atualizada a partir do filme final: ${resolve(preview)}`);
  }
 }
}finally{await browser.close({silent:true});}
