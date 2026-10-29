import pathlib,json,subprocess,concurrent.futures,time,wave,numpy as np
r=pathlib.Path('/workspace/longform-rebuild');c=r/'chunks';c.mkdir(exist_ok=True);p=json.load(open(r/'edit-plan.json'));base=pathlib.Path('/workspace/longform-full');old=base/'graphics';new=r/'graphics';cta=base/'v2/graphics';faces={1:pathlib.Path('/workspace/longform-edit/assets/face-part1.mp4'),2:base/'assets/face2.mp4',3:base/'assets/face3.mp4'};screens={1:pathlib.Path('/workspace/longform-edit/assets/screen-part1.mp4'),2:base/'assets/screen2.mp4',3:base/'assets/screen3.mp4'};font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
texts={'eps':'EPS: $4.21 (2015) → $16.80 (LTM в записи)','disclaimer':'Образовательный разбор · не индивидуальная инвестиционная рекомендация','calculation':'P/E = цена акции / EPS · 453 / 16.80 ≈ 27×','forward-caption':'Forward P/E — цена / ожидаемый EPS следующих 12 месяцев','pe-history':'S&P Global · Forward P/E (×) · исторический график из записи','scenario':'Условный сценарий автора: рост EPS и неизменный P/E. Не гарантия.','dual':'S&P Global: EPS ($) и Forward P/E (×) · показатели с разными единицами','compression':'EPS может расти, а цена снижаться при сжатии P/E'}
def render(j):
 idx=j['index'];out=c/f'{idx:03}.mp4'
 if out.exists():return
 mode=j['mode'];detail=j['detail'];dur=j['duration'];part=j['part'];a=j['from'];cmd=['ffmpeg','-v','error','-y','-threads','2','-filter_complex_threads','1','-ss',str(a),'-i',str(faces[part])];f=[]
 if mode=='face':f=['[0:v]scale=1920:1080,setsar=1,fps=25,setpts=PTS-STARTPTS[v]']
 elif mode in ['note','note-new','proof','cta']:
  folder=old if mode=='note' else cta if mode=='cta' else new;duration=4 if mode=='note' else 8
  while not (folder/(detail+'.png')).exists():time.sleep(2)
  if j['animate']:cmd+=['-i',str(folder/(detail+'.mp4'))];bg=f'[1:v]tpad=stop_mode=clone:stop_duration={dur},setpts=PTS-STARTPTS[bg]'
  else:
   hold=folder/(detail+'-natural-hold.png')
   if not hold.exists():subprocess.run(['ffmpeg','-v','error','-y','-ss',str(duration-.04),'-i',str(folder/(detail+'.mp4')),'-frames:v','1',str(hold)],check=True)
   cmd+=['-loop','1','-framerate','25','-i',str(hold)];bg='[1:v]setpts=PTS-STARTPTS[bg]'
  f=[bg,'[0:v]crop=1080:1080:420:0,scale=440:440,fps=25,setsar=1,setpts=PTS-STARTPTS[pip]','[bg]drawbox=x=1425:y=245:w=450:h=450:color=white:t=fill[b]','[b][pip]overlay=1430:250:shortest=1[v]']
 else:
  screen=screens[3] if mode=='dual' else screens[part];ss=0 if mode=='dual' else a
  cmd+=['-threads','2','-ss',str(ss),'-i',str(screen)]
  f=['[1:v]scale=1920:1080,setsar=1,fps=25,setpts=PTS-STARTPTS[bg]','[0:v]crop=1080:1080:420:0,scale=300:300,setsar=1,fps=25,setpts=PTS-STARTPTS[pip]','[bg]drawbox=x=20:y=125:w=310:h=310:color=white:t=fill[b]','[b][pip]overlay=25:130:shortest=1[screen]']
  caption=texts.get(detail,texts['dual'] if mode=='dual' else '')
  if mode=='forward':
   cmd+=['-i',str(new/'forward.mp4')]
   f+= [f'[2:v]tpad=stop_mode=clone:stop_duration={dur},crop=1280:650:55:280,scale=700:356,setpts=PTS-STARTPTS[formula]','[screen][formula]overlay=1180:115:shortest=1[v]']
  elif caption:
   file=r/f'text-{idx}.txt';file.write_text(caption)
   size=29 if len(caption)>75 else 34
   f+=[f"[screen]drawbox=x=360:y=25:w=1515:h=80:color=white@0.96:t=fill,drawtext=fontfile={font}:textfile={file}:fontcolor=0x11283f:fontsize={size}:x=380:y=48:alpha='min(t/0.45,1)'[v]"]
  else:f[-1]=f[-1].replace('[screen]','[v]')
 cmd+=['-filter_complex',';'.join(f),'-map','[v]','-an','-t',str(dur),'-c:v','libx264','-crf','24','-preset','fast','-threads','2','-pix_fmt','yuv420p','-r','25','-movflags','+faststart',str(out)]
 with open(c/f'{idx:03}.log','w') as log:ret=subprocess.run(cmd,stdout=log,stderr=log)
 if ret.returncode:out.unlink(missing_ok=True);raise RuntimeError((c/f'{idx:03}.log').read_text()[-1500:])
 print('DONE',idx,part,mode,a,dur,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(render,p['jobs']))
end=c/'end.mp4';subprocess.run(['ffmpeg','-v','error','-y','-i',str(cta/'end.mp4'),'-t','6','-an','-c:v','libx264','-preset','fast','-crf','24','-threads','2','-r','25',str(end)],check=True)
runs=[]
for j in p['jobs']:
 if runs and runs[-1][0]==j['part'] and abs(runs[-1][2]-j['from'])<.001:runs[-1][2]=j['to']
 else:runs.append([j['part'],j['from'],j['to']])
audio={}
for part in [1,2,3]:
 with wave.open(str(base/'analysis'/f'camera{part}-48.wav')) as w:audio[part]=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2)
gain={1:1,2:10**(-.43/20),3:10**(3.6/20)}
with open(r/'voice.f32le','wb') as out:
 for part,a,b in runs:
  x=audio[part][round(a*48000):round(b*48000)].astype(np.float32)/32768*gain[part];n=min(720,len(x)//4)
  if n:x[:n]*=np.linspace(0,1,n)[:,None];x[-n:]*=np.linspace(1,0,n)[:,None]
  out.write(x.astype('<f4').tobytes())
(r/'audio-runs.json').write_text(json.dumps(runs,indent=2));paths=[c/f"{j['index']:03}.mp4" for j in p['jobs']]+[end];(r/'concat.txt').write_text('\n'.join("file '"+str(x)+"'" for x in paths))
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(r/'concat.txt'),'-f','f32le','-ar','48000','-ac','2','-i',str(r/'voice.f32le'),'-map','0:v','-map','1:a','-c:v','copy','-af','highpass=f=65,loudnorm=I=-16:TP=-1.5:LRA=9,apad=pad_dur=6','-c:a','aac','-b:a','160k','-ar','48000','-movflags','+faststart',str(r/'Price_Value_Natural_Edit.mp4')],check=True)
print('FINAL DONE',flush=True)
