"""Validate actual exported media, not just renderer metadata."""
from pathlib import Path
import json, subprocess
root=Path(__file__).resolve().parents[1]
results=[]
for name,seconds,frames in [('qa/amostra-6s.mp4',6,180),('output/confia-previa-30s.mp4',30,900),('output/confia-institucional-180s.mp4',180,5400)]:
    path=root/name
    if not path.exists(): raise SystemExit(f'Ausente: {name}')
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)]))
    v=next(s for s in data['streams'] if s['codec_type']=='video'); a=next(s for s in data['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'])==(1920,1080)
    assert v['codec_name']=='h264' and a['codec_name']=='aac'
    assert v['r_frame_rate']=='30/1' and int(v['nb_read_frames'])==frames
    assert abs(float(data['format']['duration'])-seconds)<.05
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'],check=True)
    results.append({'file':name,'seconds':float(data['format']['duration']),'frames':frames,'size_bytes':path.stat().st_size,'video':'H.264 / 1920x1080 / 30fps','audio':'AAC','decode':'passed'})
    print(f'OK: {name}',flush=True)
(root/'qa/verification.json').write_text(json.dumps(results,indent=2))
