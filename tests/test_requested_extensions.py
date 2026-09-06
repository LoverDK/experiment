"""Meaningful checks for information access and coefficient diagnostics."""
import sys
import unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from causal_atlas_sim.extension_baselines import archive_baselines,regression_predictions
from causal_atlas_sim.extension_bridge import audit_set_function
from causal_atlas_sim.extension_nsw import fixed_design,make_objects,read_data,response_surface


class RequestedExtensionsTests(unittest.TestCase):
    def test_modular_objective_has_unit_gamma_and_valid_bound(self):
        values=np.array([sum(j+1 for j in range(4) if mask&(1<<j)) for mask in range(16)],float)
        r=audit_set_function(values,values,2)
        self.assertEqual(r['gamma'],1);self.assertEqual(r['epsilon'],0)
        self.assertTrue(r['bound_holds']);self.assertEqual(r['selected_value'],7)

    def test_complementarity_and_nonmonotonicity_are_not_hidden(self):
        complement=np.array([0,0,0,1.])
        r=audit_set_function(complement,complement,2)
        self.assertEqual(r['gamma'],0);self.assertIsNone(r['lower_bound'])
        values=np.array([0,1,1,.5])
        r=audit_set_function(values,values,2)
        self.assertFalse(r['monotone']);self.assertIsNone(r['lower_bound'])

    def test_uniform_error_accounts_for_paired_marginals(self):
        values=np.array([0,1,2,3.]);estimate=np.array([0,1.1,1.9,3.2])
        self.assertAlmostEqual(audit_set_function(values,estimate,2)['epsilon'],.3)

    def test_undefined_set_invalidates_check(self):
        r=audit_set_function(np.array([0,np.nan,1,2]),np.arange(4),1)
        self.assertFalse(r['valid']);self.assertIsNone(r['gamma'])

    def test_constant_source_effect_is_preserved(self):
        rng=np.random.default_rng(7);x=rng.normal(size=(24,4));y=np.full(24,2.)
        pred,_=archive_baselines(x,y,np.ones(24),rng.normal(size=(3,4)))
        for p in pred.values():np.testing.assert_allclose(p,2,atol=1e-9)

    def test_tuning_is_invariant_to_target_covariates(self):
        rng=np.random.default_rng(2);x=rng.normal(size=(15,3));y=rng.normal(size=15)
        for kernel in (False,True):
            _,a=regression_predictions(x,y,np.zeros((1,3)),kernel=kernel)
            _,b=regression_predictions(x,y,np.ones((1,3))*100,kernel=kernel)
            self.assertEqual(a,b)

    def test_real_reference_units_disjoint_and_exact_semisynthetic_estimand(self):
        x,t,y=read_data(ROOT/'data/nsw_dw.dta');a,b,aa,bb=fixed_design(x,t)
        self.assertFalse(set(a)&set(b));self.assertEqual(len(a)+len(b),445)
        source=make_objects(x,t,y,a,aa);target=make_objects(x,t,y,b,bb)
        self.assertFalse(set(sum([list(s.neighborhood_rows) for s in source],[])) &
                         set(sum([list(s.neighborhood_rows) for s in target],[])))
        _,tau=response_surface(x,'constant')
        for obj in target:self.assertEqual(tau[list(obj.neighborhood_rows)].mean(),2)


if __name__=='__main__':unittest.main()
