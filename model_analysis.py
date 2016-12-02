from __future__ import print_function
from datahandling import access_db, extractnames, get_msrmnts
from tinydb import Query
from numpy import mean, std, insert
from bisect import bisect
from model_scoring_func import gen_terms_key, gen_X
import statsmodels.api as sm
from heapq import nlargest
from logging import debug
from pandas import DataFrame
from no_big_db_func import get_Ys
from gen_model_inputs import get_all_lin_model_inp
Q = Query()
          
def translate_model_code(model_code):
    model_code = model_code[:]
    terms_key = gen_terms_key()
    ingredients = ['PVC', 'Filler', 'FR', 'Stabiliser', 'DINP', 'LDH', 'Sph. Filler']

    for i, mc in enumerate(model_code):
        if mc <= 6:
            model_code[i] = ingredients[mc]
        else:
            model_code[i] = '*'.join([ingredients[c] for c in terms_key[mc]])
            
    # mc_translated = ' + '.join(model_code)
    return model_code

def model_stats(X, Y):
    results = sm.OLS(Y, X).fit()
    params = results.params
    conf_int = results.conf_int()
    r_sqrd = results.rsquared
    p_vals = results.pvalues
    t_vals = results.tvalues
    
    return params, conf_int, r_sqrd, p_vals, t_vals
    
def get_select_models():
    """ Selects the model that is 'best' from the top models at each number of model terms """
    model_select_db = access_db(3, True)
    
    Ys = get_Ys()
    all_full_input = get_all_lin_model_inp()
    
    names = Ys.columns
    
    for column in names:
        equip, d_type = column.split(' ')

        top_db = access_db('Top_score_results_'+ equip + '_' + d_type, False)
                   
        df = DataFrame(top_db.all())

        scores = list(df['top_score'].values)
        mcodes = list(df['top_mcode'].values)

        max_score = max(scores)
        done = False

        # Select model with least number of terms where prediction improves
        # no more than 5 % at max prediction.
        lim = max_score - (abs(max_score*5/105))

        for s in scores:
            if s > lim and done == False:
                select_score = s
                done = True
                
        ind = scores.index(select_score)
        select_model = mcodes[ind]
        
        Y = Ys[column].dropna().values
        sn_Y = Ys[column].dropna().index
        X = gen_X(sn_Y, all_full_input, select_model)
        
        params, conf_int, r_sqrd, p_vals, t_vals = model_stats(X, Y)

        my_Q = ((Q.equipment_name == equip) &
                (Q.data_type == d_type))

        done = model_select_db.contains(my_Q)

        if done:
            model_select_db.update({'select_score': select_score,
                                    'select_mcode': select_model,
                                    'model_params': list(params),
                                    'r_sqrd': r_sqrd,
                                    'p_vals': list(p_vals),
                                    't_vals': list(t_vals)
                                   }, my_Q)
            continue

        entry = {'equipment_name': equip,
                 'data_type': d_type,
                 'select_score': select_score,
                 'select_mcode': select_model,
                 'model_params': list(params),
                 'r_sqrd': r_sqrd,
                 'p_vals': list(p_vals),
                 't_vals': list(t_vals)
                }

        model_select_db.insert(entry)
    
def resp_var_val(x, mcode, mparams):
    terms_key = gen_terms_key()

    val = 0
    for mc, mp in zip(mcode, mparams):
        tk = terms_key[mc]
        if mc <= 6:
            val += mp*x[mc]
        else:
            val += mp*x[tk[0]]*x[tk[1]]
            
    return val