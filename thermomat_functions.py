from __future__ import division

from numpy import log, random, array


def cond_model(p, time):
    theta = p['theta'].value
    tau = p['tau'].value
    beta = p['beta'].value
    m = p['m'].value

    # F_t = 1 - 1/(1 + (t/tau)**theta)
    F_t = log(1 + (time / tau) ** theta)
    model = m * time + beta * F_t

    return model


def f2min(p, time, data):
    model = cond_model(p, time)
    return model - data


def find_cut_point(conduct_data):
    prev_cond = 1.0
    prev_prev_cond = 2.0

    for i, cond in enumerate(conduct_data):
        if cond == prev_cond == prev_prev_cond and cond > 40:
            return i - 1

        prev_prev_cond = prev_cond
        prev_cond = cond

        # functions return None by default


def rand_ini_val(ub):
    lb = array([1., 1., 0., 0.])
    return lb + random.rand(len(lb)) * (ub - lb)


def parameters(ini_val, up_limits):
    from lmfit import Parameters
    p = Parameters()

    theta, tau, beta, m = ini_val
    theta_lim, tau_lim, beta_lim, m_lim = up_limits

    #              Name, Value,  Vary,  Min, Max)
    p.add_many(('theta', theta, True, 1.0, theta_lim),
               ('tau', tau, True, 1.0, tau_lim),
               ('beta', beta, True, 1.0, beta_lim),
               ('m', m, True, 0.0, m_lim))

    return p
