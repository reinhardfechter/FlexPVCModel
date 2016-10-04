from tinydb import Query
from datahandling import my_query, access_db
from itertools import combinations
from winsound import Beep
from time import time
from sklearn.cross_validation import cross_val_score, ShuffleSplit
from sklearn.feature_selection import f_regression
from sklearn.linear_model import LinearRegression
from gen_model_inputs import get_all_lin_model_inp
from numpy import mean
Q = Query()

def gen_Y(db, equipment, data_type):
    """ Generates Y to for one equipment and data_type """
    Y = []
    sample_nos_Y = []
    
    data = db.search((Q.equipment_name == equipment) &
                     (Q.data_type == data_type))
    
    for i in data:
        Y.append(i['value'])
        sample_nos_Y.append(i['sample_number'])
        
    Y_scaled = [(2*(y - min(Y))/(max(Y) - min(Y)) - 1) for y in Y]
    
    return Y_scaled, sample_nos_Y

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
    terms_key = range(7)
    for i in combinations(range(7), 2):
        terms_key.append(list(i))
    return terms_key

def my_sound():
    Beep(600,300)
    Beep(500,300)
    Beep(400,300)
    Beep(450,300)
    Beep(300,300)

def gen_all_possible_models(no_terms, up_to):
    """ Generates all the possible 2nd order Scheffe models
    up to a given number of model terms if up_to is True
    else only the number of terms """

    terms_key = gen_terms_key()

    cnt = 0
    t = time()
    
    if up_to == True:
        cut = 0
    else:
        cut = no_terms - 1

    for k in range(no_terms)[cut:]:
        number_of_terms = k + 1

        db = access_db(('All_Poss_Mod_' + str(number_of_terms) + '_Terms'), False)

        check = db.all()

        if len(check) == 0:

            for i in combinations(range(28), number_of_terms):
                invalid = False
                for j in i:
                    if j >= 7:
                        key_1 = terms_key[j][0]
                        key_2 = terms_key[j][1]
                        if key_1 not in i or key_2 not in i:
                            invalid = True

                if invalid == False:
                    db.insert({'mc': i})
                    cnt += 1

            print '________________'
            print cnt, 'models with', number_of_terms, 'terms entered into DB'
            req_time = time() - t
            minutes, seconds = divmod(req_time, 60)
            print 'Required Time:', round(minutes), 'min and', round(seconds, 2), 's'
        else:
            print '________________'
            print 'Models with', number_of_terms, 'terms already done'

    # my_sound()

def score_1_model(db, equipment, data_type, model, model_code, Y, sample_numbers_Y, all_full_models):
    """ Scores one model to given Y and enters into scored models db """
    
    do_check = True
    
    if do_check == True:
        check = db.search((Q.model_code == model_code))
                         
    else:
        check = []

    if len(check) == 0:
        X = gen_X(sample_numbers_Y, all_full_models, model_code)
        my_cv = ShuffleSplit(len(Y), n_iter=3, test_size=0.333, random_state=0)
        scores = cross_val_score(model, X, Y, cv=my_cv)

        entry = {'model_code': model_code,
                 'n_terms': len(model_code),
                 'kfold_score': mean(list(scores))
                }

        db.insert(entry)

def score_models_per_data_type(db, sv_db, equipment, data_type, model, all_full_models, all_model_codes):
    """ Fits all the models for a certain data type """
    Y, sn_Y = gen_Y(sv_db, equipment, data_type)
    
    for i in all_model_codes:
        model_code = i
        score_1_model(db, equipment, data_type, model, model_code, Y, sn_Y, all_full_models)
        
def get_data_req_to_score_model():
    """ Calculates all the data required to run score_models_per_data_type
    that does not need to be recalculated in score_models_per_data_type """
  
    all_model_codes = []

    for i in range(4):
        number_of_terms = i + 1
        db = access_db(('All_Poss_Mod_' + str(number_of_terms) + '_Terms'), False)
        
        db_all = db.all()
        if len(db_all) != 0:
            for entry in db_all:
                all_model_codes.append(entry['mc'])
    
    sv_db = access_db(0, True)
    model = LinearRegression(fit_intercept=False)
    all_full_models = get_all_lin_model_inp()
    return sv_db, model, all_full_models, all_model_codes