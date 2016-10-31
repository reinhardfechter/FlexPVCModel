from datahandling import access_db
from tinydb import Query
from datahandling import get_msrmnts
from pandas import DataFrame, concat, Series
from numpy import matrix, array
from gen_model_inputs import full_model_lin
Q = Query()

def constraints_list():
    return [u'LOI Final']
              
def min_max_df():
    mod_db = access_db(3, True)
    sv_db = access_db(0, True)
    
    msrmnts = get_msrmnts(sv_db, Q)
    
    const_list = constraints_list()
    for_opt = msrmnts[const_list]
    
    df = concat([for_opt.max(), for_opt.min()], axis=1)
    df.columns = ['max', 'min']
    
    return df
    
def M_lim(con_limits):
    mod_db = access_db(3, True)

    df = min_max_df()
    
    df['constr_limits'] = Series(con_limits, index=df.index)
    con_scale = 2*(df['constr_limits'] - df['min'])/(df['max'] - df['min']) - 1
    df['constr_scaled'] = con_scale
    
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
                         
    req_df = concat([df[['constr_scaled']], mod_df], axis=1)
    req_df = req_df.dropna()
    
    M = []
    M_no_sign_change = []
    lim = []

    for index, row in req_df.iterrows():
        M_row = [0.0]*28
        
        for ind, param in zip(row.select_mcode, row.model_params):
            M_row[ind] = param
        
        lim_row = row.constr_scaled
        M_no_sign_change.append(M_row)
        
        if row.desired_vals == 'high':
            M_row = [i*(-1.0) for i in M_row]
            lim_row *= -1.0
        
        M.append(M_row)
        lim.append(lim_row)
        
    return M, lim, M_no_sign_change
 
def my_g(x, con_limits):
    g = []
    
    # Mixture constraint
    # g.append(sum(x) - 1.0)
    
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
    M, lim, ignore = M_lim(con_limits)
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