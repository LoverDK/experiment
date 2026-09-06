"""Run one independently reproducible v3 block; save provenance after completion."""
from pathlib import Path
import argparse, hashlib, json, platform, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from causal_atlas_sim import validation_v3 as v

if __name__=='__main__':
    functions={'selection':v.selection_intervals,'mechanisms':v.mechanism_benchmark,
        'nuisance':v.nuisance_experiment,'dependence':v.dependence_experiment,
        'constants':v.constants_experiment,'nsw':v.nsw_stability,'hillstrom':v.hillstrom,'bridge':v.bridge_stability}
    p=argparse.ArgumentParser();p.add_argument('block',choices=functions);args=p.parse_args()
    v.OUT.mkdir(parents=True,exist_ok=True)
    started=time.time()
    sources=[* (ROOT/'src/causal_atlas_sim').glob('*.py'),Path(__file__),ROOT/'docs/paper/validation_v3_protocol.md']
    meta=dict(block=args.block,command=sys.argv,started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        python=platform.python_version(),numpy=v.np.__version__,pandas=v.pd.__version__,
        base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_sha256={x.relative_to(ROOT).as_posix():hashlib.sha256(x.read_bytes()).hexdigest() for x in sources})
    try: functions[args.block]();meta['status']='completed'
    except Exception as ex:meta['status']='failed';meta['error']=repr(ex);raise
    finally:
        meta['seconds']=time.time()-started
        (v.OUT/(args.block+'_metadata.json')).write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
