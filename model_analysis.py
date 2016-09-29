from datahandling import access_db
from tinydb import Query
from numpy import mean, std, insert
from bisect import bisect
from model_scoring_func import gen_terms_key
import statsmodels.api as sm

def get_top_models(db, sr_db, equipment, data_type, no_models):
    """ Finds the models with the highest scores up to a set number of models
    and enters the scores and corresponding model codes into the Only_Top_Models database """

    for n in range(28):
        no_of_terms = n + 1
        all_score_data = sr_db.search((Query().n_terms == no_of_terms))

        if len(all_score_data) == 0:
            print 'Scoring results not available for', equipment, data_type, 'with', no_of_terms, 'terms'
        else:
            top_scores = []
            top_mcodes_pos = []

            for j, i in enumerate(all_score_data):
                scores = i['kfold_scores']
                score = mean(scores)

                index = bisect(top_scores, score)
                top_scores = insert(top_scores, index, score)
                top_mcodes_pos = insert(top_mcodes_pos, index, j)

                if len(top_scores) == no_models + 1:
                    top_scores = top_scores[1:]
                    top_mcodes_pos = top_mcodes_pos[1:]
               
            top_mcodes = []
            for j in top_mcodes_pos:
                entry = all_score_data[int(j)]
                mcode =  entry['model_code']
                top_mcodes.append(mcode)

            check = db.search((Query().equipment_name == equipment) &
                              (Query().data_type == data_type) &
                              (Query().n_terms == no_of_terms)
                             )

            entry = {'equipment_name': equipment,
                     'data_type': data_type,
                     'n_terms': no_of_terms,
                     'top_scores': list(reversed(top_scores)),
                     'top_mcodes': list(reversed(top_mcodes))
                    }

            if len(check) == 0:
                db.insert(entry)
            else:
                db.remove((Query().equipment_name == equipment) &
                          (Query().data_type == data_type) &
                          (Query().n_terms == no_of_terms))
                db.insert(entry)
          
def translate_model_code(model_code):
    mc_translated = []
    terms_key = gen_terms_key()
    ingredients = ['PVC', 'filler', 'FR', 'stabiliser', 'DINP', 'LDH', 'spherical_filler']

    for i in model_code:
        key = terms_key[i]
        if type(key) == int:
            mc_translated.append(ingredients[key])
        else:
            mc_translated.append(ingredients[key[0]] + '*' + ingredients[key[1]])
    return mc_translated

def model_stats(X, Y):
    results = sm.OLS(Y, X).fit()
    params = results.params
    conf_int = results.conf_int()
    r_sqrd = results.rsquared
    p_vals = results.pvalues
    t_vals = results.tvalues
    
    return params, conf_int, r_sqrd, p_vals, t_vals