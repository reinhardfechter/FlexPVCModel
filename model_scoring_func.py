from __future__ import print_function
from tinydb import Query
from datahandling import access_db, extractnames, access_file, get_msrmnts
from itertools import combinations

try:
    from winsound import Beep
except ImportError:
    def Beep(a, b):
        pass

from sklearn.cross_validation import cross_val_score, ShuffleSplit
from sklearn.linear_model import LinearRegression
from gen_model_inputs import get_all_lin_model_inp
import cPickle
from pandas import DataFrame
from numpy import mean
from pca import pca_X
from sklearn.decomposition import PCA
Q = Query()

def gen_X(sample_numbers_Y, all_full_models, model_select_code):
    """ Generates X to score one model for one equipment and data_type """
    X = []
    for i in sample_numbers_Y:
        full_model_lin = all_full_models[i - 1]
            
        full_model_selected = [p for i, p in enumerate(full_model_lin) if i in model_select_code]
            
        X.append(full_model_selected)

    return X
    
def gen_terms_key():
    """ Generates the key to the model codes """
    terms_key = list(range(7))
    for i in combinations(list(range(7)), 2):
        terms_key.append(list(i))
    return terms_key

def my_sound():
    Beep(600,300)
    Beep(500,300)
    Beep(400,300)
    Beep(450,300)
    Beep(300,300)

def gen_all_possible_models(number_of_terms):
    """ Generates all the possible 2nd order Scheffe models
    up to a given number of model terms if up_to is True
    else only the number of terms """

    terms_key = gen_terms_key()

    f_name = 'All_Poss_Mod_{}_Terms'.format(number_of_terms)
    
    try:
        f_obj = access_file(f_name, write=False)
        f_obj.close()
    except:
        all_mcodes = []
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
                all_mcodes.append(list(i))


        f_obj = access_file(f_name)
        cPickle.dump(all_mcodes, f_obj)
        f_obj.close()

def get_data_req_to_score_model():
    """ Calculates all the data required to run score_models_per_data_type
    that does not need to be recalculated in score_models_per_data_type """
    Q = Query()
  
    all_model_codes = []

    for i in range(28):
        number_of_terms = i + 1
        db = access_db(('All_Poss_Mod_{}_Terms'.format(number_of_terms)), False)

        all_model_codes += extractnames(db.search(Q.mc.exists()), 'mc')

    sv_db = access_db(0, True)
    model = LinearRegression(fit_intercept=False)
    all_full_models = get_all_lin_model_inp()
    return sv_db, model, all_full_models, all_model_codes
    
def get_Ys(do_pca=False):
    """Get Ys as DataFrame for fitting, if no PCA measurements are scaled from -1 to 1"""
    
    sv_db = access_db(0, True)
    measurements = get_msrmnts(sv_db, Q)
    
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
    Ys = get_Ys()
    return Ys.columns

def score_models(column):
    """Generates all models and scores the data without storing all the possible models,
    no big tinydb's are used"""
    
    Ys = get_Ys()
    all_full_input = get_all_lin_model_inp()
    model_obj = LinearRegression(fit_intercept=False)
    
    Y = Ys[column].dropna().values
    sn_Y = Ys[column].dropna().index
    my_cv = ShuffleSplit(len(Y), n_iter=3, test_size=0.333, random_state=0)
    
    equip, d_type = column.split(' ')
    
    top_db = access_db('Top_score_results_'+ equip + '_' + d_type, False)
   
    for i in range(4):
        number_of_terms = i + 1

        done = top_db.contains(Q.n_terms == number_of_terms)
    
        if done:
            continue
           
        f_name = 'All_Poss_Mod_{}_Terms'.format(number_of_terms)
        f_obj = access_file(f_name, write=False)
        mcodes = cPickle.load(f_obj)
        f_obj.close()

        top_score = -10000.0
        for i in mcodes:
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
