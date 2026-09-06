"""Validation of isolation, calibration endpoints and statistical counterexamples."""
import sys, unittest
from dataclasses import replace
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from causal_atlas_sim.validation_v3 import (finite_quantile, predictor_rows,
    generate_minimal_archive, fitted_aipw, surface_value)

class ValidationV3Tests(unittest.TestCase):
    def test_calibration_does_not_interpolate_unattainable_quantiles(self):
        self.assertTrue(np.isinf(finite_quantile([1,2,3],.95)))
        self.assertEqual(finite_quantile(np.arange(100),.95),95)

    def test_hidden_target_fields_cannot_change_prediction(self):
        g=generate_minimal_archive(seed=987)
        p=predictor_rows(g)
        h=replace(g,target=replace(g.target,true_effect=1e9,estimated_effect=-1e9,
            observed_outcome=np.full(g.target.n_units,np.nan)))
        q=predictor_rows(h)
        for a,b in zip(p,q):
            self.assertEqual(a['estimate'],b['estimate']);self.assertEqual(a['score'],b['score'])

    def test_known_propensity_fitted_aipw_unbiased_in_independent_runs(self):
        rng=np.random.default_rng(39);errors=[]
        for _ in range(300):
            x=rng.uniform(-1,1,300);a=rng.binomial(1,.5,300)
            y=1+.8*x+1.2*x*x+a*2+rng.normal(size=300)
            errors.append(fitted_aipw(x,a,y,2,'linear_known',.5).mean()-2)
        self.assertLess(abs(np.mean(errors)),4*np.std(errors,ddof=1)/np.sqrt(300))

    def test_equicorrelation_proxy_has_expected_variance(self):
        w=np.ones(8)/8;rho=.7
        sigma=.36*((1-rho)*np.eye(8)+rho*np.ones((8,8)))
        self.assertAlmostEqual(w@sigma@w,.36*(rho+(1-rho)/8))
        self.assertGreater(w@sigma@w,.36/8)

    def test_friedman2_domain_mapping(self):
        m=np.array([-1,-1,-1,-1])
        self.assertAlmostEqual(surface_value(m,'friedman2'),1/(40*np.pi)/500)

if __name__=='__main__':unittest.main()
