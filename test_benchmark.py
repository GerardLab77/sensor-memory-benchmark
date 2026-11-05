import unittest
import numpy as np
from benchmark import features, split_indices
class Controls(unittest.TestCase):
    def test_future_cannot_change_past_features(self):
        x=np.random.default_rng(4).normal(size=(100,3));changed=x.copy();changed[60:]+=999
        for kind in ('current','summary','lags'):
            np.testing.assert_array_equal(features(x,kind,20)[:60],features(changed,kind,20)[:60])
    def test_split_gap(self):
        tr,va,te=split_indices(10000,600)
        self.assertGreater(va[0]-tr[-1],600);self.assertGreater(te[0]-va[-1],600)
        self.assertEqual(len(set(tr)&set(te)),0)
    def test_lag_alignment(self):
        x=np.arange(100.)[:,None];f=features(x,'lags',20)
        self.assertEqual(f[50,-1],30);self.assertEqual(f[50,0],50)
if __name__=='__main__':unittest.main()
