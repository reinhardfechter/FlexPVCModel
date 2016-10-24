from pandas import DataFrame
from itertools import combinations
from model_scoring_func import gen_terms_key, gen_X
from datahandling import access_db, get_msrmnts
from gen_model_inputs import get_all_lin_model_inp
from tinydb import Query
from sklearn.linear_model import LinearRegression
from sklearn.cross_validation import cross_val_score, ShuffleSplit
from numpy import mean
from pca import pca_X
from sklearn.decomposition import PCA
Q = Query()
 
def get_Ys(measurements, do_pca=False):
    """Scale the measurements for scoring"""
    
    if do_pca:
        X, df = pca_X()
        my_pca = PCA(n_components=0.99)
        my_pca.fit(X)
        
        X_trans = my_pca.transform(X)
        sn_Y = list(df.index)
        Ys = map(list, zip(*X_trans))
        names = ['PCA Comp_' + str(i + 1) for i in range(my_pca.n_components_)]
        Ys = DataFrame(X_trans, index=sn_Y, columns=names)
        return Ys
    
    Ys = measurements

    Ys = Ys - Ys.min()
    Ys = Ys/Ys.max()
    return Ys*2 - 1

def get_all_names():
    sv_db = access_db(0, True)
    msrmnts = get_msrmnts(sv_db, Q)
    Ys = get_Ys(msrmnts)
    return Ys.columns
    
def gen_and_score_mod(column):
    """Generates all models and scores the data without storing all the possible models,
    no big tinydb's are used"""
    
    sv_db = access_db(0, True)
    msrmnts = get_msrmnts(sv_db, Q)
    Ys = get_Ys(msrmnts)
    all_full_input = get_all_lin_model_inp()
    model_obj = LinearRegression(fit_intercept=False)
    
    Y = Ys[column].dropna().values
    sn_Y = Ys[column].dropna().index
    my_cv = ShuffleSplit(len(Y), n_iter=3, test_size=0.333, random_state=0)
    
    equip, d_type = column.split(' ')
    
    top_db = access_db('Top_score_results_'+ equip + '_' + d_type, False)
   
    for i in range(1):
        number_of_terms = i + 1

        done = top_db.contains(Q.n_terms == number_of_terms)
    
        if done:
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
                        break

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