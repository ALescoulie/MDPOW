import pytest

import numpy as np
from numpy.testing import assert_array_almost_equal, assert_almost_equal
from scipy import constants
from copy import deepcopy

import gromacs

import mdpow.config
import mdpow.fep

def test_molar_to_nm3():
    assert_almost_equal(mdpow.fep.molar_to_nm3(1.5), 0.9033212684)
    assert_almost_equal(mdpow.fep.molar_to_nm3(55.5), 33.42288693449999)

def test_bar_to_kJmolnm3():
    assert_almost_equal(mdpow.fep.bar_to_kJmolnm3(1.0), 0.0602214179)

def test_kcal_to_kJ():
    assert_almost_equal(mdpow.fep.kcal_to_kJ(10.0), 41.84)

def test_kJ_to_kcal():
    assert_almost_equal(mdpow.fep.kJ_to_kcal(41.84), 10.0)

def test_kBT_to_kJ():
    ref = constants.N_A*constants.k*1e-3
    assert_almost_equal(mdpow.fep.kBT_to_kJ(1, 1), ref)

class TestFEPschedule(object):
    reference = {
        'VDW':
        {'couple_lambda0': 'vdw',
         'couple_lambda1': 'none',
         'description': 'decoupling vdw --> none',
         'label': 'VDW',
         'lambdas': np.array([ 0.  ,  0.05,  0.1 ,  0.2 ,  0.3 ,  0.4 ,  0.5 ,  0.6 ,  0.65,
                               0.7 ,  0.75,  0.8 ,  0.85,  0.9 ,  0.95,  1.  ]),
         'name': 'vdw',
         'sc_alpha': 0.5,
         'sc_power': 1,
         'sc_sigma': 0.3},
        'Coulomb':
        {'couple_lambda0': 'vdw-q',
         'couple_lambda1': 'vdw',
         'description': 'dis-charging vdw+q --> vdw',
         'label': 'Coul',
         'lambdas': np.array([ 0.  ,  0.25,  0.5 ,  0.75,  1.  ]),
         'name': 'Coulomb',
         'sc_alpha': 0,
         'sc_power': 1,
         'sc_sigma': 0.3}
    }

    @pytest.fixture
    def cfg(self):
        # load default bundled configuration
        return mdpow.config.get_configuration()

    def test_VDW(self, cfg):
        return self._test_schedule(cfg, 'VDW')

    def test_Coulomb(self, cfg):
        return self._test_schedule(cfg, 'Coulomb')

    @pytest.mark.parametrize('component', ['VDW', 'Coulomb'])
    def test_copy(self, cfg, component):
        section = 'FEP_schedule_{0}'.format(component)
        schedule = deepcopy(mdpow.fep.FEPschedule.load(cfg, section))
        reference = self.reference[component]

        for k in schedule:
            assert k in reference, "additional entry {0} in runinput.yml".format(k)

        for k in reference:
            assert k in schedule, "missing entry {0} in runinput.yml".format(k)

        for k in schedule.keys():
            if k == "lambdas":
                assert_array_almost_equal(schedule[k], reference[k],
                                          err_msg="FEP schedule {0} mismatch".format(k))
            else:
                assert schedule[k] == reference[k], \
                    "mismatch between loaded FEP schedule entry {0} and reference".format(k)

    @pytest.mark.parametrize('component', ['VDW', 'Coulomb'])
    def test_write(self, cfg, component, tmp_path):
        filename = tmp_path / "cfg.yaml"
        cfg.write(filename)
        new_cfg = mdpow.config.get_configuration(filename)
        assert new_cfg.conf == cfg.conf

    @pytest.mark.parametrize("x,ref", [
                            ("test", False),
                            ([1, 1, 2, 3], True),
                            ({1, 2, 3}, True),
                            (None, False),
                            ])
    def test_iterable(self, x, ref):
        assert mdpow.config.iterable(x) == ref

    def _test_schedule(self, cfg, component):
        section = 'FEP_schedule_{0}'.format(component)
        schedule = mdpow.fep.FEPschedule.load(cfg, section)
        reference = self.reference[component]

        for k in schedule:
            assert k in reference, "additional entry {0} in runinput.yml".format(k)

        for k in reference:
            assert k in schedule, "missing entry {0} in runinput.yml".format(k)

        for k in schedule.keys():
            if k == "lambdas":
                assert_array_almost_equal(schedule[k], reference[k],
                                          err_msg="FEP schedule {0} mismatch".format(k))
            else:
                assert schedule[k] == reference[k], \
                    "mismatch between loaded FEP schedule entry {0} and reference".format(k)

    def test_skip_empty_entries(self, cfg, section="FEP_schedule_Coulomb"):
        # remove some entries
        del cfg.conf[section]['name']     # string
        del cfg.conf[section]['lambdas']  # array
        with pytest.warns(mdpow.config.NoOptionWarning):
            schedule = mdpow.fep.FEPschedule.load(cfg, section)

        assert schedule['label'] == "Coul"
        assert schedule['sc_power'] == 1
        assert 'name' not in schedule
        assert 'lambdas' not in schedule
