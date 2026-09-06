"""Run isolated experimental extensions from protocol v2; no original outputs touched."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
OUT=ROOT/'results/extensions'


def save(name,records):
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/(name+'.csv')
    with path.open('w',newline='',encoding='utf-8') as f:
        if records:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)


def synthetic(repetitions):
    from causal_atlas_sim.dgp import SimulationConfig,generate_minimal_archive
    from causal_atlas_sim.methods import AtlasConfig,fit_causal_atlas,fit_semantic_forced_composition
    from causal_atlas_sim.extension_baselines import archive_baselines
    records=[]
    for scenario,shift,noise in (('nominal',0,1),('moderate',.25,1),('severe',.8,1),('high_noise',0,3)):
        for batch,base in enumerate((20260811,20260812,20260813)):
            for rep,ss in enumerate(np.random.SeedSequence(base).spawn(repetitions)):
                seed=int(ss.generate_state(1,dtype=np.uint32)[0])
                g=generate_minimal_archive(SimulationConfig(target_shift_fraction=shift,outcome_noise_sd=noise),seed=seed)
                a,t=g.archive,g.target
                baseline,tuning=archive_baselines(np.vstack([e.observed_representation for e in a]),
                    [e.estimated_effect for e in a],[e.standard_error_certificate for e in a],t.observed_representation)
                atlas=fit_causal_atlas(a,t,AtlasConfig())
                semantic=fit_semantic_forced_composition(a,t,AtlasConfig(representation_dimensions=(0,1)))
                pred={m:float(v[0]) for m,v in baseline.items()}
                pred.update(atlas=atlas.raw_point_estimate,atlas_no_rejection=atlas.raw_point_estimate,
                            semantic_forced=semantic.raw_point_estimate)
                for m,value in pred.items():
                    released=bool(atlas.accepted) if m=='atlas' else True
                    records.append(dict(scenario=scenario,batch=batch,replicate=rep,seed=seed,method=m,
                        truth=t.true_effect,estimate=value,absolute_error=abs(value-t.true_effect),released=released,
                        ridge=tuning['ridge']['ridge'] if m=='ridge_meta_regression' else None,
                        kernel_ridge=tuning['kernel']['ridge'] if m=='rbf_kernel_ridge' else None,
                        kernel_bandwidth=tuning['kernel']['bandwidth_multiplier'] if m=='rbf_kernel_ridge' else None))
            print(f"Synthetic {scenario} batch {batch+1}/3",flush=True)
    save('synthetic_baselines_records',records)


def metadata(args):
    paths=[ROOT/'data/nsw_dw.dta',ROOT/'docs/paper/extension_protocol_v2.md',Path(__file__),
        *(ROOT/'src/causal_atlas_sim').glob('extension_*.py')]
    data=dict(command=sys.argv,settings=vars(args),python=platform.python_version(),numpy=np.__version__,
        base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        sources={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    data['outputs']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.csv')}
    (OUT/(args.block+'_metadata.json')).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('block',choices=['synthetic','nsw','bridge'])
    parser.add_argument('--repetitions',type=int,default=100);parser.add_argument('--bootstrap',type=int,default=200)
    parser.add_argument('--bridge-repetitions',type=int,default=12)
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    if args.block=='synthetic': synthetic(args.repetitions)
    elif args.block=='nsw':
        from causal_atlas_sim.extension_nsw import read_data,fixed_design,real_reference,semisynthetic
        x,t,y=read_data(ROOT/'data/nsw_dw.dta');design=fixed_design(x,t)
        (OUT/'nsw_design.json').write_text(json.dumps(dict(zip(['source_units','reference_units','source_anchors','target_anchors'],
            [v.tolist() for v in design])),indent=2)+'\n')
        real,failures=real_reference(x,t,y,design,args.bootstrap)
        save('nsw_real_records',real);save('nsw_real_failures',failures)
        semi,failures=semisynthetic(x,design,args.repetitions)
        save('nsw_semisynthetic_records',semi);save('nsw_semisynthetic_failures',failures)
    else:
        from causal_atlas_sim.extension_bridge import bridge_checks
        records,sets,failures=bridge_checks(args.bridge_repetitions)
        save('bridge_checks',records);save('bridge_set_values',sets);save('bridge_empty_intersections',failures)
    metadata(args)


if __name__=='__main__':main()
