from pandas import DataFrame
from itertools import combinations
from model_scoring_func import gen_terms_key, gen_X
from datahandling import access_db
from gen_model_inputs import get_all_lin_model_inp
from tinydb import Query
from sklearn.linear_model import LinearRegression
from sklearn.cross_validation import cross_val_score, ShuffleSplit
from numpy import mean
from ipyparallel import Client

rc = Client()

def get_msrmnts(sv_db, Q):
    """Get all the measured data form the single value database"""
    measurements = DataFrame(sv_db.search(Q.equipment_name.exists() & Q.data_type.exists()))
    measurements['name'] = measurements.equipment_name + ' ' + measurements.data_type
    # This will automatically average the different measurements which repeat
    measurements = measurements.pivot_table(index='sample_number', columns='name', values='value')

    measurements = measurements.drop([u'tensile E_t_MPa_mean', 
                                      u'tensile epsilon_break_%_mean', 
                                      u'tensile epsilon_max_%_mean',
                                      u'tensile sigma_break_MPa_mean',
                                      u'tensile sigma_max_MPa_mean',
                                      u'thermomat int_of_abs_err',
                                      u'ConeCal C-factor',
                                      u'tensile epsilon_max_%',
                                      u'tensile sigma_max_MPa',
                                      u'rheomix diff_long_short_stab_min'
                                     ], axis=1)
                                     
    return measurements
    
def get_Ys(measurements):
    """Scale the measurements for scoring"""
    Ys = measurements

    Ys = Ys - Ys.min()
    Ys = Ys/Ys.max()
    return Ys*2 - 1

Q = Query()

sv_db = access_db(0, True)

msrmnts = get_msrmnts(sv_db, Q)

Ys = get_Ys(msrmnts)

all_full_input = get_all_lin_model_inp()
model_obj = LinearRegression(fit_intercept=False)

def get_all_names():
    return Ys.columns
    
def gen_and_score_mod(column):
    """Generates all models and and scores the data,
    no big tinydb's are used"""
    Y = Ys[column].dropna().values
    sn_Y = Ys[column].dropna().index
    my_cv = ShuffleSplit(len(Y), n_iter=3, test_size=0.333, random_state=0)
    
    equip, d_type = column.split(' ')
    
    top_db = access_db('Top_score_results_'+ equip + '_' + d_type, False)
   
    for i in range(10):
        number_of_terms = i + 1

        done = top_db.contains(Q.n_terms == number_of_terms)
    
        if done:
            print('Skipped', column, 'with', number_of_terms, 'terms')
            continue

        terms_key = gen_terms_key()

        # Generate all possible models
        top_score = -10000.0
        for i in combinations(list(range(28)), number_of_terms):
            invalid = False

            for j in i:
                if j >= 7:
                    key_1 = terms_key[j][0]
                    key_2 = terms_key[j][1]
                    if key_1 not in i or key_2 not in i:
                        invalid = True

            if not invalid:
                # Generate X for certain model and Y
                X = gen_X(sn_Y, all_full_input, i)
                scores = cross_val_score(model_obj, X, Y, cv=my_cv)
                score = mean(scores)
                
                top_score = max(score, top_score)
                
                if top_score == score:
                    top_mcode = list(i)
        
        entry = {'equipment_name': equip,
                 'data_type': d_type,
                 'n_terms': number_of_terms,
                 'top_score': top_score,
                 'top_mcode': top_mcode
                }
        
        top_db.insert(entry)