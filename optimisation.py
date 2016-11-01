from datahandling import access_db
from tinydb import Query
from datahandling import get_msrmnts
from pandas import DataFrame, concat, Series
from numpy import matrix, array
from gen_model_inputs import full_model_lin
from random import uniform
Q = Query()

def constraints_list():
    return [u'LOI Final']
              
def min_max_df(const_list, full=False):
    mod_db = access_db(3, True)
    sv_db = access_db(0, True)
    
    msrmnts = get_msrmnts(sv_db, Q)
    
    if not full:
        for_opt = msrmnts[const_list]
    else:
        for_opt = msrmnts
    
    df = concat([for_opt.max(), for_opt.min()], axis=1)
    df.columns = ['max', 'min']
    
    return df
    
def get_mod_info():
    mod_db = access_db(3, True)
    
    mod_df = DataFrame(mod_db.all())
    mod_df['name'] = mod_df.equipment_name + ' ' + mod_df.data_type
    
    mod_df = mod_df.set_index('name')
    mod_df = mod_df.drop(['data_type', 
                          'equipment_name', 
                          'p_vals', 
                          'r_sqrd',
                          'select_score',
                          't_vals'
                         ], axis=1)
                         
    return mod_df
    
def info_for_constr(const_list, con_limits):
    df = min_max_df(const_list)
    
    df['constr_limits'] = Series(con_limits, index=df.index)
    con_scale = 2*(df['constr_limits'] - df['min'])/(df['max'] - df['min']) - 1
    df['constr_scaled'] = con_scale
    
    mod_df = get_mod_info()
    
    req_df = concat([df[['constr_scaled']], mod_df], axis=1)
    req_df = req_df.dropna()
    
    return req_df
    
def M_lim(req_df, do_lim=True):
    M = []
    lim = []

    for index, row in req_df.iterrows():
        M_row = [0.0]*28
        
        for ind, param in zip(row.select_mcode, row.model_params):
            M_row[ind] = param
        
        if do_lim:
            lim_row = row.constr_scaled
        
        if row.desired_vals == 'high' and do_lim:
            M_row = [i*(-1.0) for i in M_row]
            lim_row *= -1.0
        
        M.append(M_row)
        
        if do_lim:
            lim.append(lim_row)
        
    if not do_lim:
        return M
    
    return M, lim
 
def my_g(x, const_list, con_limits):
    """ Inequality constraints for the optimisation, 
    constraints required as g(x) >= 0 """
    
    g = []
    
    # Constraints on the original experimental design
    exp_des_lim = matrix([[-0.7, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                          [-0.2, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                          [-0.1, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
                          [0.02, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
                          [-0.7, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                          [0.2, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0],
                          [-0.15, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                          [-0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
                         ])
    
    x_m = matrix(x)
    g_exp_des = exp_des_lim*x_m.transpose()
    g.extend(array(g_exp_des.transpose())[0].tolist())
    
    # Constraints based on user defined limits on properties
    req_df = info_for_constr(const_list, con_limits)
    M, lim = M_lim(req_df)
    M = matrix(M)
    lim = matrix(lim)
    lim = lim.transpose()
    x_full = full_model_lin(x)
    x_full = matrix(x_full)
    x_full = x_full.transpose()
    
    g_mod = M*x_full-lim
    g.extend(array(g_mod.transpose())[0].tolist())
    
    return [-i for i in g]

def obj_fun(x, ingr_cost):
    return sum([i*j for i, j in zip(x, ingr_cost)]), ingr_cost

def highlight_true(val):
    if val == 'constrained':
        return 'background-color: yellow'
    else:
        return ''
    
def property_results(x, used_con, con_limits, show_used_only):
    df = min_max_df(used_con, full=True)

    mod_df = get_mod_info()
    M = M_lim(mod_df, do_lim=False)

    M = matrix(M)
    x_full = full_model_lin(x)
    x_full = matrix(x_full)
    x_full = x_full.transpose()

    prop_vals = M*x_full
    prop_vals = array(prop_vals.transpose())[0].tolist()

    df['value_scaled'] = prop_vals

    value_unscaled = (df['value_scaled'] + 1)*(df['max'] - df['min'])/2 + df['min']
    df['value_unscaled'] = value_unscaled
    df = df[['max', 'min', 'value_unscaled']]
    
    if show_used_only:
        return df.loc[used_con]

    df['constrained'] = ['constrained' if i in used_con else 'unconstrained' for i in df.index]
    df['constr_limit'] = [con_limits[used_con.index(i)] if i in used_con else None for i in df.index]
    
    return df.style.applymap(highlight_true)
    
def rand_x0():
    """ Generates random formulation within bounds of 
    original experimental designs. Note that sum(x0) != 1 """
    lim = [[100.0, 100.0], 
           [0.0, 70.0], 
           [0.0, 20.0], 
           [2.0, 10.0], 
           [20.0, 70.0], 
           [0.0, 15.0],
           [0.0, 20.0]
          ]
          
    x0 = []
    for i, l in enumerate(lim):
        l = [p*j/100.0 for j, p in zip(l, [0.4, 0.8])]
        x0.append(round(uniform(l[0], l[1]), 3))
        
    return x0
        
def formulation_result(x):
    ingredients = ['PVC', 'filler', 'FR', 'stabiliser', 'DINP', 'LDH', 'spherical_filler']
    return DataFrame([round(i, 4)*100 for i in x], index=ingredients, columns=['mass_frac_%'])