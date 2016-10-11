from __future__ import print_function
from datahandling import access_db, extractnames
from tinydb import Query
from numpy import mean, std, insert
from bisect import bisect
from model_scoring_func import gen_terms_key
import statsmodels.api as sm
from heapq import nlargest
from logging import debug
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
    terms_key = gen_terms_key()
    ingredients = ['PVC', 'filler', 'FR', 'stabiliser', 'DINP', 'LDH', 'spherical_filler']

    for i, mc in enumerate(model_code):
        if mc <= 6:
            model_code[i] = ingredients[mc]
        else:
            model_code[i] = '*'.join([ingredients[c] for c in terms_key[mc]])
            
    mc_translated = ' + '.join(model_code)
    return mc_translated

def model_stats(X, Y):
    results = sm.OLS(Y, X).fit()
    params = results.params
    conf_int = results.conf_int()
    r_sqrd = results.rsquared
    p_vals = results.pvalues
    t_vals = results.tvalues
    
    return params, conf_int, r_sqrd, p_vals, t_vals