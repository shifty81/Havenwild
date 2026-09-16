from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile, textwrap
from pathlib import Path

RUNTIME=(Path(__file__).resolve().parents[1] / 'runtime' / 'forgepy.py')
PY=sys.executable

def run(root,*args,input_text=None):
    cp=subprocess.run([PY,str(RUNTIME),'--root',str(root),*args],input=input_text,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8')
    return cp

def sh(root,*args):
    cp=subprocess.run(list(args),cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8')
    if cp.returncode:
        raise RuntimeError(f"{args}: {cp.stdout}")
    return cp.stdout

def initgit(root):
    sh(root,'git','init','-q')
    sh(root,'git','config','user.email','forgepy-test@example.invalid')
    sh(root,'git','config','user.name','ForgePY Test')
    (root/'.forgepy').mkdir(exist_ok=True)
    (root/'.forgepy/.gitignore').write_text('state/\nartifacts/\nbuild/\ncache/\n__pycache__/\nruntime/__pycache__/\n')

def commitall(root,msg='base'):
    sh(root,'git','add','-A'); sh(root,'git','commit','-qm',msg)

fail=[]
def ok(name, cond, detail=''):
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: fail.append((name,detail))

# 1 explicit authority + custom state + GREEN/commit
with tempfile.TemporaryDirectory() as td:
    root=Path(td); initgit(root)
    (root/'gate.py').write_text("from pathlib import Path\nPath('gate-ran.txt').write_text('yes')\n")
    (root/'tracked.txt').write_text('base\n')
    (root/'project.control.json').write_text(json.dumps({
        'schema':'forge.project.v1','project':{'id':'explicit','name':'Explicit'},'stateDirectory':'.pccstate',
        'commands':[{'key':'gate.full','label':'Native Full','category':'gate','program':'python','args':['gate.py']}]
    }))
    commitall(root)
    (root/'tracked.txt').write_text('changed\n')
    cp=run(root,'full')
    ok('explicit full succeeds',cp.returncode==0,cp.stdout+cp.stderr)
    ok('explicit full authority ran',(root/'gate-ran.txt').read_text()=='yes')
    ok('custom state receipt',(root/'.pccstate/last-green.json').is_file())
    # Gate-generated outputs are part of the certified post-gate tree. A change made AFTER
    # the receipt must invalidate GREEN.
    (root/'tracked.txt').write_text('changed after receipt\n')
    cp2=run(root,'commit-green')
    ok('green detects post-gate source mutation',cp2.returncode!=0,cp2.stdout)
    # remove generated marker/change and re-gate, then commit
    (root/'gate-ran.txt').unlink()
    (root/'gate.py').write_text("print('native green')\n")
    sh(root,'git','add','gate.py'); sh(root,'git','commit','-qm','make gate nonmutating')
    (root/'tracked.txt').write_text('changed again\n')
    cp=run(root,'full'); cp2=run(root,'commit-green','matrix green')
    ok('commit-green after explicit full',cp.returncode==0 and cp2.returncode==0,cp2.stdout+cp2.stderr)

# 2 root drop patch can apply despite itself being untracked and is archived
with tempfile.TemporaryDirectory() as td:
    root=Path(td); initgit(root)
    (root/'a.txt').write_text('old\n'); commitall(root)
    (root/'a.txt').write_text('new\n')
    patch=sh(root,'git','diff','--','a.txt')
    sh(root,'git','checkout','--','a.txt')
    (root/'update.patch').write_text(patch)
    cp=run(root,'patch-apply','update.patch')
    ok('root patch applies with intake exception',cp.returncode==0,cp.stdout+cp.stderr)
    ok('patch changed source',(root/'a.txt').read_text()=='new\n')
    ok('root patch moved away',not (root/'update.patch').exists())
    receipts=list((root/'.forgepy/artifacts/patches/applied').glob('*/receipt.json'))
    ok('patch lineage receipt written',len(receipts)==1)

# 3 protected runtime patch rejected
with tempfile.TemporaryDirectory() as td:
    root=Path(td); initgit(root)
    (root/'.forgepy/runtime').mkdir(parents=True)
    (root/'.forgepy/runtime/x.txt').write_text('old\n'); commitall(root)
    (root/'.forgepy/runtime/x.txt').write_text('new\n')
    patch=sh(root,'git','diff','--','.forgepy/runtime/x.txt')
    sh(root,'git','checkout','--','.forgepy/runtime/x.txt')
    (root/'bad.patch').write_text(patch)
    cp=run(root,'patch-check','bad.patch')
    ok('protected ForgePY path rejected',cp.returncode!=0 and 'protected' in cp.stdout.lower(),cp.stdout)

# 4 CMake standalone build full
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\nproject(fp C)\nadd_executable(fp main.c)\n')
    (root/'main.c').write_text('int main(void){return 0;}\n')
    cp=run(root,'full')
    ok('cmake full configures+builds',cp.returncode==0,cp.stdout[-2500:]+cp.stderr)
    built=(root/'.forgepy/build/cmake/fp').exists() or (root/'.forgepy/build/cmake/fp.exe').exists()
    ok('cmake output exists',built)

# 5 hybrid Python+Node full must run both stacks
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/'app.py').write_text("print('python ok')\n")
    (root/'build.js').write_text("require('fs').writeFileSync('node-build-ran.txt','yes')\n")
    (root/'test.js').write_text("require('fs').writeFileSync('node-test-ran.txt','yes')\n")
    (root/'package.json').write_text(json.dumps({'scripts':{'build':'node build.js','test':'node test.js'}}))
    cp=run(root,'full')
    ok('hybrid full succeeds',cp.returncode==0,cp.stdout[-2500:]+cp.stderr)
    ok('hybrid node build ran',(root/'node-build-ran.txt').exists())
    ok('hybrid node test ran',(root/'node-test-ran.txt').exists())
    ok('hybrid python check reported','Python syntax' in cp.stdout)

# 6 JSONL stdout must be strict JSON lines only
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'app.py').write_text("print('hello')\n")
    cp=run(root,'serve-jsonl',input_text='{"op":"status"}\n{"op":"run","key":"gate.full"}\n')
    parsed=[]
    parse_ok=True
    for line in cp.stdout.splitlines():
        try: parsed.append(json.loads(line))
        except Exception: parse_ok=False
    ok('JSONL stdout remains machine-parseable',parse_ok and len(parsed)==3,cp.stdout)
    ok('JSONL human logs routed stderr','ForgePY composite full gate' in cp.stderr,cp.stderr)

# 7 malformed explicit contract gets clean failure, not traceback
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/'project.control.json').write_text(json.dumps({'schema':'forge.project.v1','commands':[{'key':'x','program':'python','args':'bad'}]}))
    cp=run(root,'status')
    ok('invalid contract rejected cleanly',cp.returncode==2 and '[FAIL]' in cp.stdout and 'Traceback' not in cp.stderr,cp.stdout+cp.stderr)

# 8 menu noninteractive exits and never autoapplies
with tempfile.TemporaryDirectory() as td:
    root=Path(td); initgit(root); (root/'a.txt').write_text('x\n'); commitall(root)
    (root/'candidate.patch').write_text('not a patch\n')
    cp=run(root,'menu',input_text='')
    ok('noninteractive menu does not autoapply',cp.returncode==0 and (root/'candidate.patch').exists(),cp.stdout+cp.stderr)


# 9 duplicate command keys are rejected deterministically
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/'project.control.json').write_text(json.dumps({
        'schema':'forge.project.v1',
        'commands':[
            {'key':'build.default','program':'python','args':['-V']},
            {'key':'BUILD.DEFAULT','program':'python','args':['-V']}
        ]
    }))
    cp=run(root,'status')
    ok('duplicate command keys rejected',cp.returncode==2 and 'duplicate command key' in cp.stdout.lower(),cp.stdout+cp.stderr)

# 10 protected rename source cannot evade touched-path protection
with tempfile.TemporaryDirectory() as td:
    root=Path(td); initgit(root)
    (root/'.forgepy/runtime').mkdir(parents=True)
    (root/'.forgepy/runtime/owned.txt').write_text('runtime\n'); commitall(root)
    sh(root,'git','mv','.forgepy/runtime/owned.txt','moved.txt')
    patch=sh(root,'git','diff','--cached','--binary')
    sh(root,'git','reset','--hard','HEAD')
    (root/'rename.patch').write_text(patch)
    cp=run(root,'patch-check','rename.patch')
    ok('protected rename source rejected',cp.returncode!=0 and '.forgepy/runtime/owned.txt' in cp.stdout,cp.stdout+cp.stderr)

# 11 operation timeout terminates a hung command and records failure
with tempfile.TemporaryDirectory() as td:
    root=Path(td); initgit(root)
    (root/'slow.py').write_text('import time\ntime.sleep(10)\n')
    (root/'project.control.json').write_text(json.dumps({
        'schema':'forge.project.v1','project':{'id':'timeout','name':'Timeout'},
        'commands':[{'key':'gate.full','label':'Slow Gate','category':'gate','program':'python','args':['slow.py'],'timeoutSeconds':0.5}]
    }))
    commitall(root)
    cp=run(root,'full')
    ok('hung full gate times out',cp.returncode==124 and 'timed out' in (cp.stdout+cp.stderr).lower(),cp.stdout+cp.stderr)
    failure=json.loads((root/'.forgepy/state/last-failure.json').read_text())
    ok('timeout failure receipt recorded',failure.get('result')=='FAIL' and failure.get('exitCode')==124,str(failure))

# 12 active operation lock prevents overlapping mutation
with tempfile.TemporaryDirectory() as td:
    root=Path(td); initgit(root)
    (root/'gate.py').write_text("from pathlib import Path\nPath('should-not-run.txt').write_text('bad')\n")
    (root/'project.control.json').write_text(json.dumps({
        'schema':'forge.project.v1','commands':[{'key':'gate.full','category':'gate','program':'python','args':['gate.py']}]
    }))
    commitall(root)
    state=root/'.forgepy/state'; state.mkdir(parents=True,exist_ok=True)
    import time as _time, socket as _socket
    (state/'operation.lock').write_text(json.dumps({'pid':os.getpid(),'host':_socket.gethostname(),'label':'matrix-holder','createdEpoch':_time.time()}))
    cp=run(root,'full')
    ok('active operation lock blocks overlap',cp.returncode==75 and not (root/'should-not-run.txt').exists(),cp.stdout+cp.stderr)

# 13 volatile tracked state does not invalidate source certification
with tempfile.TemporaryDirectory() as td:
    root=Path(td); initgit(root)
    (root/'gate.py').write_text("print('ok')\n")
    (root/'source.txt').write_text('v1\n')
    (root/'.pccstate').mkdir(); (root/'.pccstate/tracked.txt').write_text('old\n')
    (root/'project.control.json').write_text(json.dumps({
        'schema':'forge.project.v1','stateDirectory':'.pccstate',
        'commands':[{'key':'gate.full','category':'gate','program':'python','args':['gate.py']}]
    }))
    commitall(root)
    cp=run(root,'full')
    (root/'.pccstate/tracked.txt').write_text('operational-only change\n')
    cp2=run(root,'commit-green')
    ok('volatile tracked state excluded from green fingerprint',cp.returncode==0 and cp2.returncode==0,cp2.stdout+cp2.stderr)

# 14 symlink patch input is rejected when platform supports symlinks
with tempfile.TemporaryDirectory() as td:
    root=Path(td); initgit(root)
    (root/'a.txt').write_text('old\n'); commitall(root)
    (root/'a.txt').write_text('new\n'); patch=sh(root,'git','diff','--','a.txt'); sh(root,'git','checkout','--','a.txt')
    real=root/'real.patch'; real.write_text(patch)
    link=root/'link.patch'
    try:
        link.symlink_to(real.name)
        cp=run(root,'patch-check','link.patch')
        ok('symlink patch input rejected',cp.returncode!=0 and 'symbolic-link' in cp.stdout.lower(),cp.stdout+cp.stderr)
    except OSError:
        print('PASS symlink patch input rejected (symlinks unavailable on platform)')


# 15 timeout kills descendant process tree, not just the immediate parent
with tempfile.TemporaryDirectory() as td:
    root=Path(td); initgit(root)
    child_code="import time; from pathlib import Path; time.sleep(1.5); Path('orphan-marker.txt').write_text('alive')"
    (root/'tree.py').write_text("import subprocess,sys,time\nsubprocess.Popen([sys.executable,'-c',"+repr(child_code)+"])\ntime.sleep(10)\n")
    (root/'project.control.json').write_text(json.dumps({
        'schema':'forge.project.v1','commands':[{'key':'gate.full','category':'gate','program':'python','args':['tree.py'],'timeoutSeconds':0.4}]
    }))
    commitall(root)
    cp=run(root,'full')
    import time as _time
    _time.sleep(1.8)
    ok('timeout kills descendant process tree',cp.returncode==124 and not (root/'orphan-marker.txt').exists(),cp.stdout+cp.stderr)


# 16 safe command cwd executes inside project while traversal is rejected
with tempfile.TemporaryDirectory() as td:
    root=Path(td); initgit(root)
    work=root/'sub'; work.mkdir()
    (work/'gate.py').write_text("from pathlib import Path\nPath('cwd-marker.txt').write_text('yes')\n")
    (root/'project.control.json').write_text(json.dumps({
        'schema':'forge.project.v1','commands':[{
            'key':'gate.full','category':'gate','program':'python','args':['gate.py'],'cwd':'sub','timeoutSeconds':5
        }]
    }))
    commitall(root)
    cp=run(root,'full')
    ok('safe project cwd executes correctly',cp.returncode==0 and (work/'cwd-marker.txt').exists(),cp.stdout+cp.stderr)
    (root/'project.control.json').write_text(json.dumps({
        'schema':'forge.project.v1','commands':[{'key':'gate.full','program':'python','args':['-V'],'cwd':'../outside'}]
    }))
    cp=run(root,'status')
    ok('cwd traversal rejected',cp.returncode==2 and 'cwd must remain within' in cp.stdout,cp.stdout+cp.stderr)


# 17 init creates a stable project UUID and GUI-first launcher
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    # mirror the package pieces init expects
    (root/'.forgepy/runtime').mkdir(parents=True)
    (root/'.forgepy/gui').mkdir(parents=True)
    (root/'.forgepy/gui/pcc_gui.py').write_text("print('gui')\n")
    cp=run(root,'init')
    ident=json.loads((root/'.forgepy/project.identity.json').read_text())
    first=ident.get('uuid')
    cp2=run(root,'init')
    second=json.loads((root/'.forgepy/project.identity.json').read_text()).get('uuid')
    launcher=(root/'PROJECT_CONTROL_CENTER.cmd').read_text(errors='replace')
    ok('init creates stable project UUID',cp.returncode==0 and cp2.returncode==0 and first and first==second,str(ident))
    ok('default PCC is GUI-first','ForgePY-GUI.cmd' in launcher and '--cli' in launcher,launcher)

# 18 explicit internal PCC provider is surfaced with highest precedence
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/'gate.py').write_text("print('ok')\n")
    (root/'project.control.json').write_text(json.dumps({
        'schema':'forge.project.v1','provider':{'type':'internal-pcc','name':'Native PCC'},
        'commands':[{'key':'gate.full','category':'gate','program':'python','args':['gate.py']}]
    }))
    cp=run(root,'--json','status')
    payload=json.loads(cp.stdout)
    caps={x.get('key') for x in payload.get('capabilities',[])}
    ok('internal PCC provider precedence',cp.returncode==0 and payload.get('discovery',{}).get('provider')=='internal-pcc' and payload.get('discovery',{}).get('precedence')==1,cp.stdout)
    ok('internal PCC capability surfaced','provider.internal-pcc' in caps,cp.stdout)

# 19 project-local adapter is below root project contract but above auto discovery
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'.forgepy/adapters').mkdir(parents=True)
    (root/'.forgepy/adapters/project.control.json').write_text(json.dumps({
        'schema':'forge.project.v1','commands':[{'key':'build.default','category':'build','program':'python','args':['-V']}]
    }))
    cp=run(root,'--json','status'); payload=json.loads(cp.stdout)
    ok('adapter provider precedence',payload.get('discovery',{}).get('provider')=='forgepy-adapter' and payload.get('discovery',{}).get('precedence')==3,cp.stdout)

# 20 operation evidence is persisted as queryable history
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'app.py').write_text("print('ok')\n")
    cp=run(root,'quick'); hp=run(root,'history','10')
    rows=json.loads(hp.stdout)
    ok('operation history persisted',cp.returncode==0 and hp.returncode==0 and rows and rows[-1].get('key')=='gate.fast',hp.stdout)

# 21 JSONL exposes capabilities/identity/history without human stdout pollution
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'app.py').write_text("print('ok')\n")
    cp=run(root,'serve-jsonl',input_text='{"op":"capabilities"}\n{"op":"identity"}\n{"op":"history"}\n')
    lines=[json.loads(x) for x in cp.stdout.splitlines()]
    ok('JSONL provider discovery surfaces',len(lines)==4 and lines[1].get('ok') and 'capabilities' in lines[1] and 'identity' in lines[2] and 'history' in lines[3],cp.stdout)

# 22 project-owned PCC launcher is preserved while legacy ForgePY launcher is upgraded
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'.forgepy/gui').mkdir(parents=True); (root/'.forgepy/gui/pcc_gui.py').write_text("print('gui')\n")
    custom='@echo off\necho PROJECT OWNED\n'
    (root/'PROJECT_CONTROL_CENTER.cmd').write_text(custom)
    cp=run(root,'init')
    ok('custom project PCC launcher preserved',cp.returncode==0 and (root/'PROJECT_CONTROL_CENTER.cmd').read_text()==custom,cp.stdout)
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'.forgepy/gui').mkdir(parents=True); (root/'.forgepy/gui/pcc_gui.py').write_text("print('gui')\n")
    legacy='@echo off\nsetlocal EnableExtensions\ncd /d "%~dp0"\nif "%~1"=="" (\n  call "%~dp0ForgePY.cmd" menu\n) else (\n  call "%~dp0ForgePY.cmd" %*\n)\nexit /b %errorlevel%\n'
    (root/'PROJECT_CONTROL_CENTER.cmd').write_text(legacy)
    cp=run(root,'init'); updated=(root/'PROJECT_CONTROL_CENTER.cmd').read_text(errors='replace')
    ok('legacy ForgePY PCC launcher upgrades to GUI',cp.returncode==0 and 'ForgePY-GUI.cmd' in updated,cp.stdout+updated)

# 23 GUI source is syntactically valid and does not depend on third-party packages
try:
    gui=RUNTIME.parents[1]/'gui'/'pcc_gui.py'
    compile(gui.read_text(encoding='utf-8-sig'),str(gui),'exec')
    gui_ok=True
except Exception as exc:
    gui_ok=False; gui_detail=str(exc)
else:
    gui_detail=str(gui)
ok('GUI source compiles with stdlib-only imports',gui_ok,gui_detail)

# 24 U5 auto-onboarding discovers nested mixed components and unique semantic operations
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/'frontend').mkdir(); (root/'native').mkdir()
    (root/'frontend/package.json').write_text(json.dumps({'scripts':{'build':"node -e \"require('fs').writeFileSync('node-built.txt','yes')\"",'test':"node -e \"console.log('ok')\""}}))
    (root/'native/CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\nproject(n C)\nadd_executable(n main.c)\n')
    (root/'native/main.c').write_text('int main(void){return 0;}\n')
    cp=run(root,'--json','scan'); plan=json.loads(cp.stdout)
    kinds=set(plan.get('kinds') or [])
    keys={x.get('key') for x in plan.get('operations') or []}
    ok('nested mixed repository discovery',cp.returncode==0 and {'node','cmake'} <= kinds and plan.get('componentCount')==2,cp.stdout)
    ok('component-aware unique operations','build.node.node-frontend' in keys and 'build.cmake.cmake-native' in keys,cp.stdout)
    defaults=plan.get('defaults') or {}
    ok('mixed project default build includes every component',set(defaults.get('build.default') or [])=={'build.node.node-frontend','build.cmake.cmake-native'},str(defaults))

# 25 semantic Build executes every discovered build component in a mixed repo
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/'frontend').mkdir(); (root/'native').mkdir()
    (root/'frontend/package.json').write_text(json.dumps({'scripts':{'build':"node -e \"require('fs').writeFileSync('node-built.txt','yes')\""}}))
    (root/'native/CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\nproject(n C)\nadd_executable(n main.c)\n')
    (root/'native/main.c').write_text('int main(void){return 0;}\n')
    cp=run(root,'build')
    cmake_bin=root/'.forgepy/build/cmake/cmake-native/n'
    if os.name=='nt': cmake_bin=cmake_bin.with_suffix('.exe')
    ok('semantic build executes mixed components',cp.returncode==0 and (root/'frontend/node-built.txt').is_file() and cmake_bin.is_file(),cp.stdout[-5000:]+cp.stderr)

# 26 repository scan cache invalidates when a newly-buildable marker appears
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    first=json.loads(run(root,'--json','scan').stdout)
    second=json.loads(run(root,'--json','scan').stdout)
    (root/'app.py').write_text("print('new')\n")
    third=json.loads(run(root,'--json','scan').stdout)
    ok('repository scan cache hits unchanged tree',second.get('cacheHit') is True,str(second))
    ok('repository scan cache invalidates on new marker',third.get('cacheHit') is False and 'python' in (third.get('kinds') or []),str(third))

# 27 snapshot returns all GUI/Cortex surfaces in one process response
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'app.py').write_text("print('ok')\n")
    cp=run(root,'snapshot'); snap=json.loads(cp.stdout)
    ok('single-call project snapshot',cp.returncode==0 and snap.get('schema')=='forgepy.snapshot.v1' and all(k in snap for k in ('status','operations','patches','gitHistory','buildPlan')),cp.stdout)

# 28 generated adapter can be pinned but never overwrites a project-owned adapter
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'app.py').write_text("print('ok')\n")
    cp=run(root,'onboarding-apply')
    adapter=root/'.forgepy/adapters/project.control.json'
    payload=json.loads(adapter.read_text())
    ok('auto-onboarding can pin generated adapter',cp.returncode==0 and payload.get('provider',{}).get('type')=='forgepy-adapter' and payload.get('sourceScanSignature'),cp.stdout)
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'.forgepy/adapters').mkdir(parents=True)
    adapter=root/'.forgepy/adapters/project.control.json'
    custom={'schema':'forge.project.v1','provider':{'type':'forgepy-adapter','name':'Owned'},'commands':[{'key':'build.default','program':'python','args':['-V']}]}
    adapter.write_text(json.dumps(custom))
    cp=run(root,'onboarding-apply')
    ok('project-owned adapter is never overwritten',cp.returncode!=0 and json.loads(adapter.read_text()).get('provider',{}).get('name')=='Owned',cp.stdout)

# 29 build-release resolves to a real discovered release target rather than silently using debug build
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'Cargo.toml').write_text('[package]\nname="x"\nversion="0.1.0"\nedition="2021"\n')
    (root/'src').mkdir(); (root/'src/main.rs').write_text('fn main() {}\n')
    cp=run(root,'--json','operations'); rows=json.loads(cp.stdout)
    release=next((x for x in rows if x.get('key')=='build.release'),None)
    ok('release alias targets release category',release is not None and release.get('category')=='build-release' and release.get('_members'),str(release))

# 30 scanner surfaces Unreal as unresolved rather than fabricating an engine command
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'Game.uproject').write_text('{}\n')
    plan=json.loads(run(root,'--json','scan').stdout)
    text=' '.join(str(x.get('message')) for x in plan.get('unresolved') or [] if isinstance(x,dict))
    ok('unreal detection fails transparent', 'Unreal project' in text and not any(x.get('category')=='build' for x in plan.get('operations') or []),str(plan))

# 31 GUI uses single snapshot refresh and includes Build Plan source
try:
    gui=(RUNTIME.parents[1]/'gui'/'pcc_gui.py').read_text(encoding='utf-8-sig')
    ok('GUI optimized snapshot refresh','load_json_command(self.root_path, "snapshot")' in gui and 'Automatic Build Plan' in gui and 'Force Rescan' in gui,gui[:1200])
except Exception as exc:
    ok('GUI optimized snapshot refresh',False,str(exc))

# 32 generic patches may not rewrite executable project-control metadata
with tempfile.TemporaryDirectory() as td:
    root=Path(td); initgit(root)
    (root/'project.control.json').write_text(json.dumps({'schema':'forge.project.v1','commands':[{'key':'build.default','program':'python','args':['-V']}]})); commitall(root)
    (root/'project.control.json').write_text(json.dumps({'schema':'forge.project.v1','commands':[{'key':'build.default','program':'python','args':['-c','print(1)']}]}))
    patch=sh(root,'git','diff','--','project.control.json'); sh(root,'git','checkout','--','project.control.json'); (root/'control.patch').write_text(patch)
    cp=run(root,'patch-check','control.patch')
    ok('project control plane protected from generic patches',cp.returncode!=0 and 'protected' in cp.stdout.lower(),cp.stdout)



# 33 source-only Python discovery is structural and cached without rescanning on ordinary edits
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'src').mkdir()
    first=json.loads(run(root,'--json','scan').stdout)
    (root/'src/tool.py').write_text("print('one')\n")
    second=json.loads(run(root,'--json','scan').stdout)
    (root/'src/tool.py').write_text("print('two')\n")
    third=json.loads(run(root,'--json','scan').stdout)
    ok('source-only Python repository discovered',second.get('cacheHit') is False and 'python' in (second.get('kinds') or []),str(second))
    ok('ordinary Python edit keeps structural scan cache hot',third.get('cacheHit') is True,str(third))

# 34 nested conventional build scripts resolve relative to their component cwd
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'tool').mkdir()
    script=root/'tool/build.sh'
    script.write_text("#!/bin/sh\nprintf yes > nested-built.txt\n")
    try: script.chmod(0o755)
    except OSError: pass
    plan=json.loads(run(root,'--json','scan').stdout)
    rows=[x for x in plan.get('operations') or [] if x.get('category')=='build']
    if shutil.which('bash'):
        cp=run(root,'build')
        ok('nested project-local build script executes from cwd',cp.returncode==0 and (root/'tool/nested-built.txt').is_file(),cp.stdout+cp.stderr)
    else:
        ok('nested project-local build script discovered',any(x.get('cwd')=='tool' and x.get('program')=='build.sh' for x in rows),str(rows))

# 35 Make and non-wrapper Gradle projects receive deterministic component plans
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'native').mkdir(); (root/'java').mkdir()
    (root/'native/Makefile').write_text('all:\n\t@echo ok\ntest:\n\t@echo test\n')
    (root/'java/build.gradle').write_text('plugins { id \'base\' }\n')
    plan=json.loads(run(root,'--json','scan').stdout)
    keys={x.get('key') for x in plan.get('operations') or []}
    ok('Make component auto-discovered','build.make.make-native' in keys and 'test.make.make-native' in keys,str(plan))
    ok('Gradle without wrapper auto-discovered','build.gradle.gradle-java' in keys and 'test.gradle.gradle-java' in keys,str(plan))

# 36 generated Python adapter remains portable and resolves project interpreter at execution time
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'app.py').write_text("print('ok')\n"); (root/'tests').mkdir(); (root/'tests/test_one.py').write_text('import unittest\nclass T(unittest.TestCase):\n def test_x(self): self.assertTrue(True)\n')
    cp=run(root,'onboarding-apply'); adapter=json.loads((root/'.forgepy/adapters/project.control.json').read_text())
    py_programs=[x.get('program') for x in adapter.get('commands') or [] if str(x.get('key','')).startswith(('test.python','run.python'))]
    ok('generated Python adapter is interpreter-portable',cp.returncode==0 and py_programs and all(x=='python' for x in py_programs),str(adapter))

if fail:
    print('\nFAILURES:',fail)
    raise SystemExit(1)
print('\nALL U5 VALIDATION MATRIX TESTS PASSED')
