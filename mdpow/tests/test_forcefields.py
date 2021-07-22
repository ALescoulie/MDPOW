import os.path

import pytest
from mdpow.config import topfiles
import mdpow.forcefields

# currently supported
WATERMODELS = ('tip4p', 'tip3p', 'tip5p', 'spc', 'spce', 'm24', 'tip4pd')
SOLVENTMODELS = ('water', 'cyclohexane', 'octanol')



class TestIncludedForcefiels(object):
    @staticmethod
    def test_default_forcefield():
        assert mdpow.forcefields.DEFAULT_FORCEFIELD == "OPLS-AA"

    @staticmethod
    def test_oplsaa_itp():
        assert "ffoplsaa.itp" in topfiles
        assert topfiles["ffoplsaa.itp"].endswith(
            os.path.join('mdpow', 'top', 'ffoplsaa.itp'))

    @staticmethod
    def test_oplsaa_ff():
        assert "oplsaa.ff" in topfiles
        assert topfiles["oplsaa.ff"].endswith(
            os.path.join('mdpow', 'top', 'oplsaa.ff'))

class TestIncludedSolvents(object):
    solvents = {
        'tip4p': {
            'tip4p.itp': os.path.join('mdpow', 'top', 'oplsaa.ff', 'tip4p.itp'),
            'tip4p.gro': os.path.join('mdpow', 'top', 'tip4p.gro')
        },
        'octanol': {
            '1oct.gro': os.path.join('mdpow', 'top', '1oct.gro'),
            '1oct.itp': os.path.join('mdpow', 'top', 'oplsaa.ff', '1oct.itp'),
        },
        'cyclohexane': {
            '1cyclo.gro': os.path.join('mdpow', 'top', '1cyclo.gro'),
            '1cyclo.itp': os.path.join('mdpow', 'top', 'oplsaa.ff', '1cyclo.itp')
        },
    }

    # using nosetest-style test generators.. .feel free to rewrite for
    # py.test but I found the docs for parameterizing tests in py.test
    # too complicated

    def _test_solvent(self, name):
        solvent = self.solvents[name]
        def _assert_has_filename(filename):
            assert filename in topfiles
        def _assert_correct_path(filename, path):
            assert topfiles[filename].endswith(path)

        for filename, path in solvent:
            yield _assert_has_filename, filename
            yield _assert_correct_path, filename, path

    def test_tip4p(self):
        self._test_solvent('tip4p')

    def test_octanol(self):
        self._test_solvent('octanol')

    def test_cyclohexane(self):
        self._test_solvent('cyclohexane')

class TestWatermodels(object):
    watermodels = WATERMODELS

    @staticmethod
    def test_default_water_model():
        assert mdpow.forcefields.DEFAULT_WATER_MODEL == "tip4p"

    @pytest.mark.parametrize('expected', WATERMODELS)
    def test_gromacs_water_models(self, expected):
        models = mdpow.forcefields.GROMACS_WATER_MODELS

        def has_identifier(identifier):
            assert identifier in models

        def itp_in_top(identifier):
            model = models[identifier]
            assert model.itp in topfiles

        def coordinates_in_top(identifier):
            model = models[identifier]
            assert model.coordinates in topfiles

        has_identifier(expected)
        itp_in_top(expected)
        coordinates_in_top(expected)

    def test_watermodelsdat(self):
        included_watermodels = open(topfiles['watermodels.dat']).read()
        for line, ref in zip(self._simple_line_parser(mdpow.forcefields.GMX_WATERMODELS_DAT),
                             self._simple_line_parser(included_watermodels)):
            assert line.strip() == ref.strip()

    @staticmethod
    def _simple_line_parser(string):
        for line in string.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            yield line

    @staticmethod
    def test_get_water_model():
        model = mdpow.forcefields.DEFAULT_WATER_MODEL
        assert (mdpow.forcefields.get_water_model(model) is
                mdpow.forcefields.GROMACS_WATER_MODELS[model])

    @staticmethod
    def test_get_water_model_ValueError():
        with pytest.raises(ValueError):
            mdpow.forcefields.get_water_model("The Jabberwock is an imaginary beast.")


class TestSolventModels(object):
    watermodels = WATERMODELS
    solventmodels = [model for model in SOLVENTMODELS if model != "water"]

    @staticmethod
    def test_get_solvent_default_water():
        model = "water"
        defaultmodel = mdpow.forcefields.DEFAULT_WATER_MODEL
        assert (mdpow.forcefields.get_solvent_model(model) is
                mdpow.forcefields.GROMACS_WATER_MODELS[defaultmodel])

    @staticmethod
    def test_get_solvent_model_ValueError():
        with pytest.raises(ValueError):
            mdpow.forcefields.get_solvent_model("The Jabberwock is an imaginary beast.")

    @staticmethod
    def test_get_solvent_cyclohexane():
        model = 'cyclohexane'
        forcefield = 'OPLS-AA'
        assert (mdpow.forcefields.get_solvent_model(model) is
                mdpow.forcefields.GROMACS_SOLVENT_MODELS[forcefield][model])

    @pytest.mark.parametrize("forcefield", ['OPLS-AA', 'CHARMM', 'AMBER'])
    @staticmethod
    def test_get_solvent_octanol(forcefield):
        model = 'octanol'
        assert (mdpow.forcefields.get_solvent_model(model, forcefield=forcefield) is
                mdpow.forcefields.GROMACS_SOLVENT_MODELS[forcefield][model])

    @pytest.mark.parametrize("forcefield", ['OPLS-AA', 'CHARMM', 'AMBER'])
    @staticmethod
    def test_get_solvent_wetoctanol(forcefield):
        model = 'wetoctanol'
        assert (mdpow.forcefields.get_solvent_model(model, forcefield=forcefield) is
                mdpow.forcefields.GROMACS_SOLVENT_MODELS[forcefield][model])

    @staticmethod
    def test_get_solvent_identifier_default_is_water():
        assert (mdpow.forcefields.get_solvent_identifier('water') is
                mdpow.forcefields.DEFAULT_WATER_MODEL)

    @pytest.mark.parametrize('test_model', WATERMODELS)
    def test_get_solvent_identifier_water(self, test_model):
        def _assert_model(model):
            assert mdpow.forcefields.get_solvent_identifier('water', model=model) is model

        _assert_model(test_model)

    @pytest.mark.parametrize('test_solvent', [model for model in SOLVENTMODELS if model != "water"])
    def test_get_solvent_identifier_solvents(self, test_solvent):
        def _assert_model(solvent, model):
            assert mdpow.forcefields.get_solvent_identifier(solvent, model=model) is solvent

        _assert_model(test_solvent, None)

        # make sure that model is ignored
        _assert_model(test_solvent, "Jabberwock model")

    @staticmethod
    def test_get_solvent_identifier_None():
        assert mdpow.forcefields.get_solvent_identifier('water', model="foobar") is None
        assert mdpow.forcefields.get_solvent_identifier('benzene') is None
