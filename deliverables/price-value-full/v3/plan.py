import json,pathlib
r=pathlib.Path('/workspace/longform-rebuild')
keep={1:[(0,46.88),(131.32,224.36),(258.64,311.96),(321.0,345.28),(349.20,356.40),(361.12,459.48),(469.26,570.88),(572.8,616.98),(678.3,724.88)],2:[(13.48,28.40),(35.50,66.98),(72,174.20),(179.60,264.30),(280,354.8),(366.8,422.64),(435.76,451),(486.72,581.8),(607.3,633),(636.28,655.96),(659.84,720.86),(759.84,775.50),(786.02,791.80),(810.30,941.28)],3:[(11.12,23.4),(24.8,43.92),(78.08,91.48)]}
scenes={1:[(0,17.2,'face',''),(17.2,24.5,'note','hook'),(24.5,46.88,'face',''),(131.32,151.74,'note','eps'),(151.74,163.6,'note','profit'),(163.6,177.08,'face',''),(177.08,192,'note','risk'),(192,214.64,'face',''),(214.64,271.2,'note','multiple'),(271.2,289.2,'note','example'),(289.2,311.96,'note','years'),(321,345.28,'note','example'),(349.2,382,'note','company'),(382,469.26,'screen',''),(469.26,489.8,'screen','eps'),(489.8,528.72,'screen','disclaimer'),(528.72,572.8,'screen','calculation'),(572.8,616.98,'forward','forward'),(678.3,724.88,'note','growth')],2:[(13.48,40,'note','growth'),(40,51.7,'note','quality'),(51.7,57.4,'note','buyback-base'),(57.4,72,'note','buyback'),(72,102.5,'proof','paypal'),(102.5,125,'note','moat'),(125,151.2,'note','competition'),(151.2,174.2,'face',''),(179.6,189.3,'note','comment'),(189.3,226,'proof','law'),(226,249,'note','network'),(249,264.3,'face',''),(280,329.5,'note-new','drivers'),(329.5,354.8,'dual',''),(366.8,382.7,'note','operations'),(382.7,408,'face',''),(408,422.64,'note','compound'),(435.76,451,'note','sentiment'),(486.72,532,'dual',''),(532,546.3,'proof','palantir'),(546.3,572.3,'face',''),(572.3,581.8,'dual',''),(607.3,633,'dual','compression'),(636.28,646,'note-new','drivers'),(646,678,'screen','forward-caption'),(678,695.2,'screen',''),(695.2,720.86,'screen',''),(759.84,810.3,'screen','pe-history'),(810.3,891.88,'screen','pe-history'),(891.88,904.08,'screen','eps'),(904.08,941.28,'screen','scenario')]}
units=[];firstcta=False
for part in [1,2]:
 for a,b,mode,detail in scenes[part]:
  if part==1 and a>=349.2 and not firstcta:units.append({'part':3,'from':11.12,'to':23.4,'mode':'cta','detail':'intro'});firstcta=True
  if part==2 and a==280:units.append({'part':3,'from':24.8,'to':43.92,'mode':'cta','detail':'club'})
  for x,y in keep[part]:
   start=max(a,x);end=min(b,y)
   if end-start>.03:units.append({'part':part,'from':round(start*25)/25,'to':round(end*25)/25,'mode':mode,'detail':detail})
units.append({'part':3,'from':73.0,'to':91.48,'mode':'cta','detail':'close'});units.append({'part':2,'from':951.6,'to':952.92,'mode':'cta','detail':'close'})
# Eight-second graphic assets, then a calm hold. No waveform-based trimming or fragments inside words.
out=0
for i,j in enumerate(units):j.update(index=i,duration=round(j['to']-j['from'],2),output_start=round(out,2));out+=j['duration'];j['animate']=not(i and j['mode']==units[i-1]['mode'] and j['detail']==units[i-1]['detail'])
p={'duration':round(out+6,2),'voice_duration':round(out,2),'jobs':units,'tail':6,'edit_policy':'Whole utterances and paragraph boundaries; retain normal pauses and mild hesitations. No automatic silence cutting.'};(r/'edit-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2));print('Duration',out+6,'jobs',len(units))
