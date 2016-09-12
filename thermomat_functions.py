from numpy import log

def cond_model(p, time):
    theta = p['theta'].value
    tau = p['tau'].value
    beta = p['beta'].value
    m = p['m'].value
   
    model = []

    for t in time:
        # F_t = 1 - 1/(1 + (t/tau)**theta)
        F_t = log(1 + (t/tau)**theta)
        cond = m*t + beta*F_t
        model.append(cond)
        
    return model

def f2min(p, time, data):
    model = cond_model(p, time)
    return model - data
	
def find_cut_point(conduct_data): 
    prev_cond = 1.0
    prev_prev_cond = 2.0

    cut_found = False
    for i, cond in enumerate(conduct_data):
        if cond == prev_cond and cond == prev_prev_cond and cut_found == False and cond > 40:
            cut = i - 1
            cut_found = True

        prev_prev_cond = prev_cond
        prev_cond = cond
    
	if cut_found == False:
		cut = None
	
    return cut

def rand_ini_val(up_limits):
    theta_lim, tau_lim, beta_lim, m_lim = up_limits
    from random import random
    limits = [[1.0, theta_lim],
              [1.0, tau_lim],
              [1.0, beta_lim],
			  [0.0, m_lim]]
			  
    ini_val = []
    for l in range(len(limits)):
        lb = limits[l][0]
        ub = limits[l][1]
        new_val = lb + random()*(ub - lb)
        ini_val.append(new_val)
    
    return ini_val

def parameters(ini_val, up_limits):
    from lmfit import Parameters
    p = Parameters()
    
    theta, tau, beta, m = ini_val
    theta_lim, tau_lim, beta_lim, m_lim = up_limits
    
    #              Name, Value,  Vary,  Min, Max)
    p.add_many(('theta', theta,  True,  1.0, theta_lim),
               (  'tau',   tau,  True,  1.0, tau_lim),
               ( 'beta',  beta,  True,  1.0, beta_lim),
			   (    'm',     m,  True,  0.0, m_lim)) 
    
    return p
