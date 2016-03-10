r"""Observables in $B\to P\nu\bar\nu$"""

import flavio
import scipy.integrate
from flavio.classes import Observable, Prediction
from math import sqrt, pi

def prefactor(q2, par, B, P):
    GF = par['GF']
    scale = flavio.config['renormalization scale']['bpll']
    alphaem = flavio.physics.running.running.get_alpha(par, scale)['alpha_e']
    di_dj = flavio.physics.bdecays.common.meson_quark[(B,P)]
    xi_t = flavio.physics.ckm.xi('t',di_dj)(par)
    return 4*GF/sqrt(2)*xi_t*alphaem/(4*pi)

def get_ff(q2, par, B, P):
    ff_name = flavio.physics.bdecays.common.meson_ff[(B,P)] + ' form factor'
    return flavio.classes.AuxiliaryQuantity.get_instance(ff_name).prediction(par_dict=par, wc_obj=None, q2=q2)

def helicity_amps(q2, wc_obj, par, B, P, nu1, nu2):
    scale = flavio.config['renormalization scale']['bpll']
    label = flavio.physics.bdecays.common.meson_quark[(B,P)] + nu1 + nu2 # e.g. bsnuenue, bdnutaunumu
    wc = wc_obj.get_wc(label, scale, par)
    if nu1 == nu2: # add the SM contribution if neutrino flavours coincide
        wc['CL_'+label] += flavio.physics.bdecays.wilsoncoefficients.CL_SM(par)
    mB = par['m_'+B]
    mP = par['m_'+P]
    N = prefactor(q2, par, B, P)
    ff = get_ff(q2, par, B, P)
    wc_eff = flavio.physics.bdecays.wilsoncoefficients.get_wceff_nunu(q2, wc, par, B, P, nu1, nu2, scale)
    # below, mb is set to 4 just to save time. It doesn't enter at all as there
    # are no dipole operators.
    h = flavio.physics.bdecays.angular.helicity_amps_p(q2, mB, mP, 4, 0, 0, 0, ff, wc_eff, N)
    return h

def bpnunu_obs(function, q2, wc_obj, par, B, P, nu1, nu2):
    mB = par['m_'+B]
    mP = par['m_'+P]
    h = helicity_amps(q2, wc_obj, par, B, P, nu1, nu2)
    # below, mb is set to 4 just to save time. It doesn't enter at all as there
    # are no dipole operators.
    J = flavio.physics.bdecays.angular.angularcoeffs_general_p(h, q2, mB, mP, 4, 0, 0, 0)
    return function(J)

def bpnunu_obs_int(function, q2min, q2max, wc_obj, par, B, P, nu1, nu2):
    def obs(q2):
        return bpnunu_obs(function, q2, wc_obj, par, B, P, nu1, nu2)
    return scipy.integrate.quad(obs, q2min, q2max, epsrel=0.01, epsabs=0)[0]

def bpnunu_dbrdq2(q2, wc_obj, par, B, P, nu1, nu2):
    tauB = par['tau_'+B]
    return tauB * bpnunu_obs(flavio.physics.bdecays.bpll.dGdq2, q2, wc_obj, par, B, P, lep)

def bpnunu_dbrdq2_summed(q2, wc_obj, par, B, P):
    tauB = par['tau_'+B]
    lep =  ['e', 'mu', 'tau']
    return tauB * sum([ bpnunu_obs(flavio.physics.bdecays.bpll.dGdq2, q2, wc_obj, par, B, P, 'nu'+nu1, 'nu'+nu2)
            for nu1 in lep for nu2 in lep ])

def bpnunu_dbrdq2_int_summed(q2min, q2max, wc_obj, par, B, P):
    def obs(q2):
        return bpnunu_dbrdq2_summed(q2, wc_obj, par, B, P)
    return scipy.integrate.quad(obs, q2min, q2max, epsrel=0.01, epsabs=0)[0]/(q2max-q2min)

def bpnunu_BRtot_summed(wc_obj, par, B, P):
    def obs(q2):
        return bpnunu_dbrdq2_summed(q2, wc_obj, par, B, P)
    mB = par['m_'+B]
    mP = par['m_'+P]
    q2max = (mB-mP)**2
    q2min = 0
    return scipy.integrate.quad(obs, q2min, q2max, epsrel=0.01, epsabs=0)[0]

# Functions returning functions needed for Prediction instances

def BRtot_summed(B, P):
    return lambda wc_obj, par: bpnunu_BRtot_summed(wc_obj, par, B, P)

def dbrdq2_int_summed(B, P):
    def fct(wc_obj, par, q2min, q2max):
        return bpnunu_dbrdq2_int_summed(q2min, q2max, wc_obj, par, B, P)
    return fct

def dbrdq2_summed(B, P):
    def fct(wc_obj, par, q2):
        return bpnunu_dbrdq2_summed(q2, wc_obj, par, B, P)
    return fct


_hadr = {
'B0->K': {'tex': r"B^0\to K^0", 'B': 'B0', 'P': 'K0', },
'B+->K': {'tex': r"B^+\to K^+", 'B': 'B+', 'P': 'K+', },
'B0->pi': {'tex': r"B^0\to \pi^0", 'B': 'B0', 'P': 'pi0', },
'B+->pi': {'tex': r"B^+\to \pi^+", 'B': 'B+', 'P': 'pi+', },
}

for M in _hadr.keys():

    # binned branching ratio
    _obs_name = "<dBR/dq2>("+M+"nunu)"
    _obs = flavio.classes.Observable(name=_obs_name, arguments=['q2min', 'q2max'])
    _obs.set_description(r"Binned differential branching ratio of $" + _hadr[M]['tex'] + r"\nu\bar\nu$")
    _obs.tex = r"$\langle \text{BR} \rangle(" + _hadr[M]['tex'] + r"\nu\bar\nu)$"
    flavio.classes.Prediction(_obs_name, dbrdq2_int_summed(_hadr[M]['B'], _hadr[M]['P']))

    # differential branching ratio
    _obs_name = "dBR/dq2("+M+"nunu)"
    _obs = flavio.classes.Observable(name=_obs_name, arguments=['q2'])
    _obs.set_description(r"Differential branching ratio of $" + _hadr[M]['tex'] + r"\nu\bar\nu$")
    _obs.tex = r"$\frac{d\text{BR}}{dq^2}(" + _hadr[M]['tex'] + r"\nu\bar\nu)$"
    flavio.classes.Prediction(_obs_name, dbrdq2_summed(_hadr[M]['B'], _hadr[M]['P']))

    # total branching ratio
    _obs_name = "BR("+M+"nunu)"
    _obs = flavio.classes.Observable(name=_obs_name)
    _obs.set_description(r"Branching ratio of $" + _hadr[M]['tex'] + r"\nu\bar\nu$")
    _obs.tex = r"$\text{BR}(" + _hadr[M]['tex'] + r"\nu\bar\nu)$"
    flavio.classes.Prediction(_obs_name, BRtot_summed(_hadr[M]['B'], _hadr[M]['P']))
