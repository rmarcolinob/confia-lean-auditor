"""Local pt-BR synthesis, original score, timed subtitles. All writes stay in this project."""
from pathlib import Path
import array, json, math, os, shutil, subprocess, textwrap, wave
ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / 'public/audio'
TAKES = AUDIO / 'takes'
TAKES.mkdir(parents=True, exist_ok=True)
cues = json.loads((ROOT/'src/narration.json').read_text())
def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)
def duration(p):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)],text=True))
def stamp(t, comma=True):
    ms=round(t*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02}{"," if comma else "."}{ms:03}'
# Render each utterance separately to prevent cumulative timing drift.
report=[]; sample_rate=48000
track=array.array('h',[0])*(180*sample_rate)
for i,c in enumerate(cues):
    raw=TAKES/f'{i+1:02}.aiff'; wav=TAKES/f'{i+1:02}.wav'; txt=TAKES/f'{i+1:02}.txt'
    spoken=c.get('speech',c['text'])
    changed=not txt.exists() or txt.read_text()!=spoken
    txt.write_text(spoken)
    if changed or not raw.exists() or raw.stat().st_size < 5000:
        if not shutil.which('say'):
            raise RuntimeError('Sem sintetizador local: grave os takes conforme src/narration.json. README descreve a integração.')
        run(['say','-v',os.environ.get('CONFIA_VOICE','Luciana'),'-r','165','-f',str(txt),'-o',str(raw)])
    d=duration(raw); slot=c['end']-c['start']-.12; tempo=max(1,d/slot)
    if tempo>1.35: raise RuntimeError(f'Take {i+1} exige compressão excessiva ({tempo:.2f}). Encurte o texto ou aumente a janela.')
    run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',f'atempo={tempo},loudnorm=I=-18:TP=-2:LRA=7','-ar',str(sample_rate),'-ac','1','-c:a','pcm_s16le',str(wav)])
    with wave.open(str(wav)) as w: data=array.array('h',w.readframes(w.getnframes()))
    pos=round(c['start']*sample_rate)
    if len(data)>round(slot*sample_rate)+sample_rate//20: raise RuntimeError('Áudio excedeu a janela.')
    track[pos:pos+len(data)]=data
    report.append({'cue':i+1,'start':c['start'],'end':c['start']+len(data)/sample_rate,'tempo':round(tempo,3)})
    print(f'Voz {i+1}/{len(cues)}: {len(data)/sample_rate:.2f}s',flush=True)
with wave.open(str(AUDIO/'narracao.wav'),'wb') as w:
    w.setparams((1,2,sample_rate,0,'NONE','not compressed')); w.writeframes(track.tobytes())
# Original ambient composition: Dmaj7 / Bm7 / Gmaj7 / Asus4; soft pentatonic bells.
# No recordings, loops or third-party samples. Deterministic synthesis.
sr=24000; total=180; chords=[(146.832,220,277.183,369.994),(123.471,184.997,246.942,293.665),(97.999,146.832,195.998,246.942),(110,164.814,220,293.665)]
melody=[587.330,659.255,739.989,880,739.989,659.255,587.330,440]
score=array.array('h')
for sec in range(total):
    for j in range(sr):
        t=sec+j/sr; ci=int(t//12)%4; u=t%12; fade=min(u/1.5,1)
        # Chord crossfade over 1.5s, gently moving pad; no percussive transients.
        v=0.0
        for k in range(4):
            curr=math.sin(math.tau*chords[ci][k]*t)
            prev=math.sin(math.tau*chords[(ci-1)%4][k]*t)
            v+=(fade*curr+(1-fade)*prev)*.012*(.8+.2*math.sin(.23*t+k))
        beat=t%3; note=melody[int(t//3)%len(melody)]
        v+=.013*math.sin(math.tau*note*t)*math.exp(-beat*1.8)*min(beat/.08,1)
        envelope=min(t/3,1,(180-t)/4)
        # Narration bed approximately 20dB below speech; breathe up between cues.
        speaking=any(c['start']-.25<=t<=c['end']+.25 for c in cues)
        v*=envelope*(.52 if speaking else .7)
        score.append(int(max(-1,min(1,v))*32767))
with wave.open(str(AUDIO/'trilha-original.wav'),'wb') as w:
    w.setparams((1,2,sr,0,'NONE','not compressed')); w.writeframes(score.tobytes())
run(['ffmpeg','-v','error','-y','-i',str(AUDIO/'narracao.wav'),'-i',str(AUDIO/'trilha-original.wav'),'-filter_complex','[0:a][1:a]amix=inputs=2:normalize=0,alimiter=limit=0.89:level=false,apad,atrim=duration=180','-ar','48000','-ac','2',str(AUDIO/'mix.wav')])
(ROOT/'qa/audio-report.json').write_text(json.dumps(report,indent=2))
srt=[]; vtt=['WEBVTT\n']; md=['# Narração temporalizada — português brasileiro','Voz local: Luciana (macOS); mix final em `public/audio/mix.wav`. Texto e janelas em `src/narration.json`.\n']
for i,c in enumerate(cues):
    words=c['text'].split()
    cut=min(range(1,len(words)),key=lambda k: max(len(' '.join(words[:k])),len(' '.join(words[k:]))))
    text=c['text'] if len(c['text'])<=64 else ' '.join(words[:cut])+'\n'+' '.join(words[cut:])
    srt.append(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{text}\n')
    vtt.append(f'{stamp(c["start"],False)} --> {stamp(c["end"],False)}\n{text}\n')
    md.append(f'**{stamp(c["start"])} – {stamp(c["end"])}**\n\n{c["text"]}\n')
(ROOT/'output/legendas-pt-BR.srt').write_text('\n'.join(srt))
(ROOT/'output/legendas-pt-BR.vtt').write_text('\n'.join(vtt))
(ROOT/'docs/narracao.md').write_text('\n'.join(md))
print('Mix, stems, legendas e roteiro gerados.',flush=True)
