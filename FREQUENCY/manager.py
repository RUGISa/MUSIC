#!/usr/bin/env python3
"""FREQUENCY local launcher. Localhost only, no privileged installation."""
import json, os, shutil, signal, socket, subprocess, sys, threading, time, urllib.request, webbrowser
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DATA=Path.home()/'Library'/'Application Support'/'FREQUENCY'
DATA.mkdir(parents=True,exist_ok=True)
REPO=DATA/'ACE-Step-1.5'; LOG=DATA/'frequency-web.log'; AI_LOG=DATA/'ace-step.log'
STATUS=DATA/'startup.json'; API='http://127.0.0.1:8001'; CHILD=[]

def emit(phase,message):
    state={'phase':phase,'message':message,'timestamp':time.time()}
    STATUS.write_text(json.dumps(state,ensure_ascii=False),encoding='utf8')
    with LOG.open('a',encoding='utf8') as f:f.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {phase}: {message}\n')
    print(f'[{phase}] {message}',flush=True)

def alive(url,timeout=2):
    try:
        with urllib.request.urlopen(url,timeout=timeout) as r:return 200<=r.status<300
    except Exception:return False

def port():
    for n in range(8765,8830):
        with socket.socket() as s:
            try:s.bind(('127.0.0.1',n));return n
            except OSError:pass
    raise RuntimeError('사용 가능한 웹 포트가 없습니다')

def cmd(args,cwd=None,timeout=1200):
    with AI_LOG.open('a',encoding='utf8') as log:
        log.write('\n$ '+' '.join(map(str,args))+'\n');log.flush()
        return subprocess.run(args,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,timeout=timeout).returncode

def ensure_uv():
    for item in [shutil.which('uv'),str(Path.home()/'.local/bin/uv'),str(Path.home()/'.cargo/bin/uv')]:
        if item and Path(item).is_file():return item
    emit('install','uv 패키지 관리 도구 설치 중')
    installer=DATA/'uv-install.sh'
    urllib.request.urlretrieve('https://astral.sh/uv/install.sh',installer)
    if cmd(['/bin/sh',str(installer)],timeout=300)!=0:raise RuntimeError('uv 설치 실패. ace-step.log를 확인하세요')
    for item in [Path.home()/'.local/bin/uv',Path.home()/'.cargo/bin/uv']:
        if item.is_file():return str(item)
    raise RuntimeError('uv 실행 파일을 찾지 못했습니다')

def ensure_repo():
    script=REPO/'start_api_server_macos.sh'
    if script.exists():return
    if REPO.exists():raise RuntimeError(f'ACE-Step 소스 폴더가 불완전합니다: {REPO}')
    if not shutil.which('git'):raise RuntimeError('Git 설치가 필요합니다. xcode-select --install 명령으로 설치하세요')
    emit('install','ACE-Step 공식 소스 다운로드 중')
    if cmd(['git','clone','--depth','1','https://github.com/ace-step/ACE-Step-1.5.git',str(REPO)],timeout=600)!=0:
        raise RuntimeError('ACE-Step 소스 다운로드 실패. 인터넷 연결 및 ace-step.log를 확인하세요')

def download_model(uv):
    # The previous client reported runtime download failure, not an API connection failure.
    # Explicitly verify model download before reporting ready. Fallback mirror on failure.
    marker=DATA/'model_download_ok_v1.5'
    model_root=REPO/'checkpoints'
    required=('vae','acestep-v15-turbo')
    def has_weights():
        return all((model_root/name).is_dir() and any((model_root/name).rglob('*.safetensors')) for name in required)
    if has_weights():return
    if marker.exists():marker.unlink()
    for source in ('huggingface','modelscope'):
        emit('download',f'AI 모델 다운로드 확인 중 · {source} (첫 설치는 오래 걸릴 수 있음)')
        code=cmd([uv,'run','acestep-download','--download-source',source],cwd=REPO,timeout=3600)
        if code==0 and has_weights():
            marker.write_text(f'{source}\n',encoding='utf8');return
    raise RuntimeError('모델 다운로드 실패: HuggingFace와 ModelScope 모두 실패했습니다. 네트워크·디스크·로그를 확인하세요. 모델 다운로드가 완료되기 전에는 생성할 수 없습니다.')

def backend():
    running=alive(API+'/health')
    try:
        if sys.platform!='darwin':raise RuntimeError('이 실행 파일은 macOS용입니다')
        if os.uname().machine!='arm64':raise RuntimeError('Apple Silicon ARM64 Mac에서 실행하세요')
        if running:
            emit('ready','이미 실행 중인 ACE-Step 서버에 연결했습니다. 실제 생성 시 모델 상태를 확인합니다.');return
        ensure_repo()
        uv=ensure_uv()
        emit('install','AI 실행 환경 준비 중')
        if cmd([uv,'sync'],cwd=REPO,timeout=1800)!=0:raise RuntimeError('의존성 설치 실패. ace-step.log 확인')
        download_model(uv)
        emit('model','ACE-Step AI 모델 서버 시작 중')
        env=os.environ.copy();env['PATH']=str(Path(uv).parent)+':'+env.get('PATH','')
        env.update({'ACESTEP_LM_BACKEND':'mlx','ACESTEP_INIT_LLM':'false','CHECK_UPDATE':'false','TOKENIZERS_PARALLELISM':'false'})
        with AI_LOG.open('a',encoding='utf8') as log:
            child=subprocess.Popen(['/bin/bash','start_api_server_macos.sh'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        CHILD.append(child)
        for _ in range(240):
            if alive(API+'/health'):
                emit('ready','AI 서버 준비됨 · 생성 테스트를 진행할 수 있습니다');return
            if child.poll() is not None:raise RuntimeError(f'AI 서버 종료 코드 {child.returncode}. ace-step.log 확인')
            time.sleep(2)
        raise TimeoutError('AI 서버가 8분 내에 준비되지 않았습니다. ace-step.log 확인')
    except Exception as e:emit('error',str(e))

def main():
    emit('starting','웹사이트 시작')
    n=port(); env=os.environ.copy();env['FREQUENCY_PORT']=str(n);env['FREQUENCY_MANAGER_STATUS']=str(STATUS)
    with LOG.open('a',encoding='utf8') as log:
        local=subprocess.Popen([sys.executable,str(ROOT/'server.py')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    CHILD.append(local);url=f'http://127.0.0.1:{n}'
    for _ in range(100):
        if alive(url+'/api/status'):break
        if local.poll() is not None:raise RuntimeError('웹사이트 실행 실패. frequency-web.log 확인')
        time.sleep(.15)
    else:raise TimeoutError('웹서버가 응답하지 않습니다')
    print('FREQUENCY URL:',url,flush=True);webbrowser.open(url)
    threading.Thread(target=backend,daemon=True).start()
    while local.poll() is None:time.sleep(.5)

def stop(*_):
    for p in reversed(CHILD):
        if p.poll() is None:p.terminate()
    raise SystemExit(0)

if __name__=='__main__':
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    try:main()
    except Exception as e:emit('error',str(e));raise SystemExit(1)
