"""Analytic/numerical witnesses to scope gaps, not tests disproving fixed-weight results."""
from pathlib import Path
from statistics import NormalDist
import hashlib,json,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/validation_v3'
Phi=NormalDist().cdf
t=math.sqrt(2*math.log(40));z=NormalDist().inv_cdf(.975)
result={
 'fixed_weight_vs_selected_weight':{
  'N':100,'zeta':.05,'fixed_weight_radius':t,
  'fixed_gaussian_failure':2*(1-Phi(t)),
  'max_absolute_selected_failure':1-(2*Phi(t)-1)**100,
  'argument':'100 independent N(0,1) errors. Selecting largest absolute error is not a fixed direction.'},
 'selected_CLT':{
  'N':8,'cdf_at_zero':Phi(0)**8,'standard_normal_cdf_at_zero':.5,
  'nominal_95_coverage':Phi(z)**8-Phi(-z)**8,
  'argument':'Eight independent n-unit N(0,1) experiments, select largest sample mean. Standardized statistic is max of 8 normals for every n. Original influence variables independent; selected weighted variables are not.'},
 'sample_variance_not_proxy':{
  'n':2,'probability_zero_sample_variance_with_wrong_mean':.5,
  'argument':'Bernoulli(.5), n=2. Both outcomes equal with probability .5; sample variance zero and sample mean differs from .5.'},
 'marginal_not_selective':{
  'release_probability':.05,'conditional_coverage':0.,'marginal_coverage':.95,
  'argument':'Z~N(0,1), ordinary 95% interval, condition on |Z|>1.96. Illustrates logical implication only, not the actual ATLAS release rule.'},
 'representation_metric':{'mechanism_source':0.,'mechanism_target':1.,'effect_gap':1.,
  'representation_scale':.001,'uncorrected_observed_support_bound':.001,
  'argument':'mu(m)=m, r=.001m is invertible, hidden residual zero. Must transform L to representation units.'},
 'random_set_expectation':{'expected_fixed_set_value':.5,'expected_selected_realized_value':0.,
  'argument':'omega~Bernoulli(.5), rewards b=omega,c=1-omega. Select b if omega=0, c otherwise. F(S(omega))=.5 but E reward(S(omega),omega)=0. The policy is a logical selection counterexample, not the operational greedy algorithm.'},
 'lipschitz_not_smooth':{'left_derivative_distance_at_boundary':0.,'right_derivative_distance_at_boundary':1.,
  'argument':'For K=[-1,0], dist(x,K)=max(x,0). Valid Lipschitz witness; not C1 at zero.'}}
paper=ROOT/'docs/paper/overleaf/01_causal_atlas_bridge.tex'
source=paper.read_text(encoding='utf8');start=source.index('\\section{Appendix: Notation and Proofs}')
end=source.index('\\section{Appendix: Experimental Details}')
result['audit_source']={'path':paper.relative_to(ROOT).as_posix(),
 'whole_source_normalized_sha256':hashlib.sha256(source.encode()).hexdigest(),
 'appendix_A_normalized_sha256':hashlib.sha256(source[start:end].encode()).hexdigest(),
 'line_labels':{label:i for i,line in enumerate(source.splitlines(),1)
  for label in ('eq:app-proof-010','eq:app-proof-019','eq:app-proof-030','eq:app-proof-032',
   'eq:app-proof-051','eq:app-proof-057','eq:app-proof-078','eq:app-proof-084','eq:app-proof-103') if ('\\label{'+label+'}') in line}}
OUT.mkdir(exist_ok=True,parents=True)
(OUT/'proof_counterexamples.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(result,indent=2))
