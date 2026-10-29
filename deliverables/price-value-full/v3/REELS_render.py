import json,pathlib,subprocess,concurrent.futures,textwrap,os
r=pathlib.Path(__file__).parent;out=r/'mp4';out.mkdir(exist_ok=True);plan=json.load(open(r/'plan.json'));b=pathlib.Path('/workspace/longform-full');root=r.parent; font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';faces={1:'/workspace/longform-edit/assets/face-part1.mp4',2:str(b/'assets/face2.mp4')};screens={1:'/workspace/longform-edit/assets/screen-part1.mp4',2:str(b/'assets/screen2.mp4')}
if os.environ.get('REEL_IDS'):plan=[x for x in plan if str(x['id']) in os.environ['REEL_IDS'].split(',')]
def run(cmd,log):
 with open(log,'w') as f:p=subprocess.run(cmd,stdout=f,stderr=f)
 if p.returncode:raise RuntimeError(pathlib.Path(log).read_text()[-2000:])
def render(d):
 i=d['id'];raw=r/f'raw-{i}.mp4';dur=d['duration']-2
 if not raw.exists():
  start=d['ranges'][0][0];end=d['ranges'][-1][1]
  cmd=['ffmpeg','-v','error','-y','-threads','2','-filter_complex_threads','1','-ss',str(start),'-t',str(end-start),'-i',faces[d['part']]];f=[];tags=[]
  for k,(a,z) in enumerate(d['ranges']):
   a-=start;z-=start
   f.extend([f'[0:v]trim=start={a}:end={z},setpts=PTS-STARTPTS[v{k}]',f'[0:a]atrim=start={a}:end={z},asetpts=PTS-STARTPTS[a{k}]']);tags.append(f'[v{k}][a{k}]')
  f.append(''.join(tags)+f'concat=n={len(tags)}:v=1:a=1[v][a]');cmd+=['-filter_complex',';'.join(f),'-map','[v]','-map','[a]','-c:v','libx264','-preset','fast','-crf','20','-threads','2','-c:a','pcm_s16le','-f','matroska',str(raw)]
  run(cmd,r/f'raw-{i}.log')
 target=out/f'Reel_{i:02}.mp4'
 if target.exists():return
 heading=r/f'title-{i}.txt';heading.write_text('\n'.join(textwrap.wrap(d['heading'],width=26)))
 sub=r/f'sub-{i}.txt';sub.write_text('Подробный разбор и курс\nsemenchenko-vladyslav.com')
 source=d['visual'];cmd=['ffmpeg','-v','error','-y','-threads','2','-filter_complex_threads','1','-i',str(raw),'-stream_loop','-1','-i',str(r/f'panel-{i}.mp4')]
 if source in ['screen','dual']:
  path=screens[d['part']] if source=='screen' else str(b/'assets/screen3.mp4');ss=d['ranges'][0][0] if source=='screen' else 0
  if source=='screen' and len(d['ranges'])>1:
   sync=r/f'screen-{i}.mp4'
   if not sync.exists():
    st=d['ranges'][0][0];en=d['ranges'][-1][1];sf=[]
    for k,(a,z) in enumerate(d['ranges']):sf.append(f'[0:v]trim=start={a-st}:end={z-st},setpts=PTS-STARTPTS[s{k}]')
    sf.append(''.join(f'[s{k}]' for k in range(len(d['ranges'])))+f'concat=n={len(d["ranges"])}:v=1:a=0,scale=1280:720[v]')
    run(['ffmpeg','-v','error','-y','-threads','2','-filter_complex_threads','1','-ss',str(st),'-t',str(en-st),'-i',path,'-filter_complex',';'.join(sf),'-map','[v]','-an','-c:v','libx264','-preset','ultrafast','-crf','22','-threads','2',str(sync)],r/f'screen-{i}.log')
   path=str(sync);ss=0
  cmd+=['-stream_loop','-1','-ss',str(ss),'-i',path]
 elif source in ['factory','train','stock']:
  path=root/'assets'/({'factory':'stock-factory.mp4','train':'stock-train.mp4','stock':'pexels.mp4'}[source]);cmd+=['-stream_loop','-1','-i',str(path)]
 else:
  # Actual source or definition remains in the animated panel for proof topics.
  cmd+=['-stream_loop','-1','-i',str(r/f'panel-{i}.mp4')]
 f=[f'color=c=0x10283f:s=1080x1920:r=25:d={d["duration"]}[bg]',f'[0:v]crop=1440:1080:240:0,scale=972:729,setsar=1,fps=25,tpad=stop_mode=clone:stop_duration=2[face]',f'[bg][face]overlay=54:230[layout]',f'[2:v]scale=972:576:force_original_aspect_ratio=decrease,pad=972:576:(ow-iw)/2:(oh-ih)/2:color=0xf5f7fa,setsar=1,fps=25[real]',f'[layout][real]overlay=54:1000[realbase]',f'[1:v]scale=972:576,setsar=1,fps=25[panel]',f"[realbase][panel]overlay=54:1000:enable='lt(mod(t,18),10)'[filled]",f"[filled]drawtext=fontfile={font}:textfile={heading}:fontsize=57:fontcolor=white:line_spacing=13:x=55:y=65,drawbox=x=54:y=1630:w=972:h=180:color=0x1b3b59:t=fill,drawtext=fontfile={font}:textfile={sub}:fontcolor=white:fontsize=34:line_spacing=17:x=85:y=1665,drawtext=fontfile={font}:text='Владислав Семенченко':fontcolor=0x9cc9ee:fontsize=27:x=55:y=1840,drawbox=x=54:y=965:w=972:h=4:color=0x3b759b:t=fill[v]"]
 cmd+=['-filter_complex',';'.join(f),'-map','[v]','-map','0:a','-af','highpass=f=65,loudnorm=I=-16:TP=-1.5:LRA=9,apad=pad_dur=2','-t',str(d['duration']),'-c:v','libx264','-crf','24','-preset','fast','-threads','2','-c:a','aac','-b:a','128k','-ar','48000','-pix_fmt','yuv420p','-r','25','-movflags','+faststart',str(target)]
 try:run(cmd,r/f'reel-{i}.log')
 except:target.unlink(missing_ok=True);raise
 print('DONE',i,d['title'],d['duration'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(render,plan))
