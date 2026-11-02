#!/usr/bin/env python3
"""FREQUENCY: local-only browser UI, ACE-Step proxy and non-neural instant revisions."""
import array, json, math, os, re, struct, threading, time, wave, io, uuid
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs
from urllib.error import HTTPError, URLError

BASE=Path(__file__).resolve().parent
DATA=Path.home()/'Library'/'Application Support'/'FREQUENCY'/'tracks'
DATA.mkdir(parents=True,exist_ok=True)
ACE='http://127.0.0.1:'+str(int(os.environ.get('ACE_PORT','8001')))
PORT=int(os.environ.get('FREQUENCY_PORT','8765'))
LOCK=threading.RLock(); TASKS={}; TRACKS={}

def api(endpoint, payload=None, timeout=20):
    req=Request(ACE+endpoint,data=(json.dumps(payload).encode() if payload is not None else None),headers={'Content-Type':'application/json'}, method='POST' if payload is not None else 'GET')
    with urlopen(req,timeout=timeout) as r:return json.load(r)

def get_output_path(entry):
    s=entry.get('file') or entry.get('audio_path') or entry.get('url') or ''
    u=urlparse(s)
    if u.path!='/v1/audio':raise ValueError('모델이 지원하지 않는 파일 경로를 반환했습니다')
    p=parse_qs(u.query).get('path',[''])[0]
    if not p:raise ValueError('출력 오디오 경로가 없습니다')
    from urllib.parse import urlencode
    return '/v1/audio?'+urlencode({'path':p})

def wav_read(data):
    if len(data)>50_000_000:raise ValueError('오디오 파일이 너무 큽니다')
    with wave.open(io.BytesIO(data),'rb') as w:
        ch=w.getnchannels();rate=w.getframerate();bits=w.getsampwidth();n=w.getnframes();fmt=w.getcomptype()
        if ch not in (1,2) or bits!=2 or fmt!='NONE' or not 8000<=rate<=96000:raise ValueError('PCM 16비트 WAV만 지원합니다')
        if n>rate*120:raise ValueError('최대 120초 WAV만 지원합니다')
        a=array.array('h');a.frombytes(w.readframes(n))
        if os.sys.byteorder!='little':a.byteswap()
    return a,rate,ch

def wav_write(a,rate,ch):
    out=io.BytesIO()
    if os.sys.byteorder!='little':a.byteswap()
    with wave.open(out,'wb') as w:w.setnchannels(ch);w.setsampwidth(2);w.setframerate(rate);w.writeframes(a.tobytes())
    return out.getvalue()

def loop30(raw):
    samples,rate,ch=wav_read(raw);frames=len(samples)//ch
    if frames<rate:raise ValueError('원본 오디오가 너무 짧습니다')
    target=rate*30
    # Overlap-add segments with short boundary crossfades; output always 30s.
    cross=min(int(rate*.13),frames//12)
    period=frames-cross
    out=array.array('h',[0])*(target*ch)
    for frame in range(target):
        j=frame%period
        for k in range(ch):
            a=samples[j*ch+k]
            if j<cross:
                weight=j/max(1,cross-1)
                prev=samples[(period+j)*ch+k]
                a=round(prev*(1-weight)+a*weight)
            out[frame*ch+k]=a
    # Match the last/first 30ms to ensure click-free looping.
    fade=min(rate//33,target//50)
    for i in range(fade):
        mix=(i+1)/(fade+1)
        for k in range(ch):
            idx=(target-fade+i)*ch+k
            head=out[i*ch+k]
            out[idx]=round(out[idx]*(1-mix)+head*mix)
    for k in range(ch):out[(target-1)*ch+k]=out[k]
    return wav_write(out,rate,ch)

def edit_audio(raw, direction):
    a,rate,ch=wav_read(raw)
    direction=direction.strip()
    if len(direction)>400:raise ValueError('수정 요청은 400자 이하로 입력하세요')
    low=direction.lower()
    dark=any(x in low for x in ['어둡','부드럽','따뜻','먹먹','dark','warm','soft','mellow'])
    bright=any(x in low for x in ['밝','선명','명료','bright','crisp','clear'])
    bass=any(x in low for x in ['저음','베이스','묵직','bass','low end'])
    quiet=any(x in low for x in ['조용','잔잔','작게','quiet','softer','lower volume'])
    loud=any(x in low for x in ['크게','강렬','힘있','loud','powerful','punch'])
    if not any((dark,bright,bass,quiet,loud)):
        raise ValueError('빠른 수정은 음색·저음·음량에만 적용됩니다. 악기·멜로디·장르 변경은 AI 재생성을 선택하세요.')
    lp=[0.0]*ch;prev=[0.0]*ch; slow=[0.0]*ch
    alpha=0.13;slow_a=0.009
    gain=.68 if quiet else 1.16 if loud else 1.0
    for i,x in enumerate(a):
        k=i%ch;y=x/32768.0
        lp[k]+=alpha*(y-lp[k]);slow[k]+=slow_a*(y-slow[k])
        if dark:y=.54*y+.46*lp[k]
        if bright:y=1.22*y-.22*lp[k]
        if bass:y=y+.20*slow[k]
        y*=gain
        # Smooth bounded saturator, no clipping.
        y=math.tanh(1.05*y)/math.tanh(1.05)
        a[i]=max(-32768,min(32767,round(y*32767)))
    return wav_write(a,rate,ch)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def sendjson(self,status,value):
        raw=json.dumps(value,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def readjson(self):
        n=int(self.headers.get('Content-Length','0'))
        if not 1<=n<=12000:raise ValueError('요청 크기가 올바르지 않습니다')
        value=json.loads(self.rfile.read(n))
        if not isinstance(value,dict):raise ValueError('요청은 JSON 객체여야 합니다')
        return value
    def do_GET(self):
        p=urlparse(self.path)
        if p.path in ('/','/index.html'):
            raw=(BASE/'index.html').read_bytes();ct='text/html; charset=utf-8'
        elif p.path.startswith('/audio/'):
            ident=p.path.split('/')[-1]
            if not re.fullmatch(r'[a-f0-9]{32}',ident):self.sendjson(404,{'error':'파일을 찾을 수 없습니다'});return
            filename=DATA/(ident+'.wav')
            if not filename.exists():self.sendjson(404,{'error':'파일을 찾을 수 없습니다'});return
            raw=filename.read_bytes();ct='audio/wav'
        elif p.path=='/api/status':
            startup={}
            statefile=os.environ.get('FREQUENCY_MANAGER_STATUS','')
            if statefile:
                try:startup=json.loads(Path(statefile).read_text(encoding='utf8'))
                except (OSError,ValueError):pass
            try:
                backend=api('/health',timeout=2)
                self.sendjson(200,{'connected':True,'backend':backend,'startup':startup});return
            except Exception as e:self.sendjson(200,{'connected':False,'message':'ACE-Step 모델 서버 미연결','detail':str(e),'startup':startup});return
        elif p.path=='/api/tasks':
            with LOCK: snapshot=[dict(x) for x in TASKS.values()]
            self.sendjson(200,{'tasks':snapshot[-20:]});return
        else:self.sendjson(404,{'error':'없는 주소입니다'});return
        self.send_response(200);self.send_header('Content-Type',ct);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def do_POST(self):
        try:
            data=self.readjson()
            if self.path=='/api/start':
                prompt=str(data.get('prompt','')).strip()
                if not 5<=len(prompt)<=2200:raise ValueError('음악 설명은 5~2200자여야 합니다')
                bpm=int(data.get('bpm',100));seed=int(data.get('seed',-1))
                if not 40<=bpm<=200 or not -1<=seed<=2147483647:raise ValueError('BPM 또는 시드 값 오류')
                quality=str(data.get('quality','preview'))
                if quality not in ('preview','full'):raise ValueError('품질 설정 오류')
                duration=10 if quality=='preview' else 30
                steps=4 if quality=='preview' else 8
                job=uuid.uuid4().hex
                with LOCK:TASKS[job]={'id':job,'status':'queued','message':'AI 요청 대기','created':time.time(),'quality':quality}
                threading.Thread(target=generate,args=(job,prompt,bpm,seed,duration,steps),daemon=True).start()
                self.sendjson(202,{'job':job});return
            elif self.path=='/api/job':
                job=str(data.get('job',''))
                with LOCK:val=TASKS.get(job)
                self.sendjson(200,dict(val) if val else {'status':'missing','error':'작업을 찾을 수 없습니다'});return
            elif self.path=='/api/edit':
                tid=str(data.get('track',''));direction=str(data.get('request',''))
                with LOCK:old=TRACKS.get(tid)
                if not old:raise ValueError('원본 트랙을 찾을 수 없습니다')
                raw=(DATA/(tid+'.wav')).read_bytes()
                changed=edit_audio(raw,direction)
                new=uuid.uuid4().hex;(DATA/(new+'.wav')).write_bytes(changed)
                with LOCK:TRACKS[new]={'id':new,'parent':tid,'prompt':old['prompt'],'description':direction,'type':'instant'}
                self.sendjson(200,{'id':new,'url':'/audio/'+new,'parent':tid,'type':'instant'});return
            else:self.sendjson(404,{'error':'없는 주소입니다'});return
        except (ValueError,TypeError,json.JSONDecodeError) as e:self.sendjson(400,{'error':str(e)})
        except Exception as e:self.sendjson(500,{'error':str(e)})

def update(j,**fields):
    with LOCK:TASKS[j].update(fields)

def generate(job,prompt,bpm,seed,duration,steps):
    try:
        update(job,status='running',message='AI 초안 생성 중')
        p={'prompt':prompt+' Instrumental game background music, repeatable motifs, consistent harmony, no ending, no vocals.',
           'lyrics':'[Instrumental]','audio_duration':duration,'bpm':bpm,'key_scale':'',
           'time_signature':'4','audio_format':'wav','inference_steps':steps,'batch_size':1,
           'thinking':False,'infer_method':'ode','use_random_seed':seed<0,'seed':seed}
        response=api('/release_task',p,timeout=100)
        task=(response.get('data') or {}).get('task_id') or response.get('task_id')
        if not task:raise RuntimeError('ACE-Step이 작업 ID를 반환하지 않았습니다: '+str(response)[:200])
        update(job,message='AI 오디오 생성 중',remote_task=str(task))
        deadline=time.monotonic()+720
        while time.monotonic()<deadline:
            time.sleep(3)
            result=api('/query_result',{'task_id_list':[task]},timeout=30)
            rows=result.get('data') or []
            if isinstance(rows,dict):rows=[rows]
            if not rows:continue
            row=next((x for x in rows if x.get('task_id')==task),rows[0])
            status=str(row.get('status',''))
            if status in ('2','failed','error'):raise RuntimeError(str(row.get('error') or row.get('message') or row.get('result') or 'AI 생성 실패')[:250])
            if status not in ('1','completed','success'):continue
            items=row.get('result') or []
            if isinstance(items,str):items=json.loads(items)
            if isinstance(items,dict):items=[items]
            if not items:raise RuntimeError('AI 출력 파일을 찾지 못했습니다')
            path=get_output_path(items[0])
            with urlopen(ACE+path,timeout=120) as r:raw=r.read(50_000_001)
            track=uuid.uuid4().hex
            out=loop30(raw) if duration<30 else loop30(raw)
            (DATA/(track+'.wav')).write_bytes(out)
            with LOCK:TRACKS[track]={'id':track,'parent':None,'prompt':prompt,'type':'ai'}
            update(job,status='done',message='완료',track=track,url='/audio/'+track);return
        raise TimeoutError('12분 동안 결과가 도착하지 않았습니다. 저사양 환경에서는 서버에서 생성이 계속 진행될 수 있습니다.')
    except Exception as e:update(job,status='error',message=str(e)[:450])

if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',PORT),Handler)
    print(f'FREQUENCY http://127.0.0.1:{PORT}',flush=True)
    server.serve_forever()
