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

def get_top_models(db, sr_db, equipment, data_type, no_models):
    """ Finds the models with the highest scores up to a set number of models
    and enters the scores and corresponding model codes into the Only_Top_Models database """

    for n in range(28):
        no_of_terms = n + 1
        all_score_data = sr_db.search((Q.n_terms == no_of_terms))

        if len(all_score_data) == 0:
            debug('Scoring results not available for %s %s with %d terms' % (equipment, data_type, no_of_terms))
            continue

        top_entries = nlargest(no_models, all_score_data,
                               key=lambda e: e['kfold_score'])

        top_scores, top_mcodes = extractnames(top_entries, 'kfold_score', 'model_code')

        my_Q = ((Q.equipment_name == equipment) &
                (Q.data_type == data_type) &
                (Q.n_terms == no_of_terms))

        done = db.contains(my_Q)

        if not done:
            entry = {'equipment_name': equipment,
                     'data_type': data_type,
                     'n_terms': no_of_terms,
                     'top_scores': top_scores,
                     'top_mcodes': top_mcodes
                    }
            db.insert(entry)
        else:
            db.update({'top_scores': top_scores, 'top_mcodes': top_mcodes}, my_Q)
          
def translate_model_code(model_code):
    model_code = model_code[:]
    terms_key = gen_terms_key()
    ingredients = ['PVC', 'filler', 'FR', 'stabiliser', 'DINP', 'LDH', 'spherical_filler']

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
    
