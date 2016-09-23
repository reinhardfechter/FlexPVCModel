from tinydb import Query
from datahandling import my_query, access_other_db, access_sv_db
from itertools import combinations
from winsound import Beep
from time import time
from sklearn.cross_validation import cross_val_score
from sklearn.feature_selection import f_classif
from sklearn.linear_model import LinearRegression
from gen_model_inputs import get_all_lin_model_inp
Q = Query()

def gen_Y(db, equipment, data_type):
    # Generates Y to for one equipment and data_type
    Y = []
    sample_nos_Y = []
    for i in range(53):
        sample_number = i + 1
        entry = db.search(my_query(equipment, sample_number, data_type))
        if len(entry) == 1:
            Y.append(entry[0]['value'])
            sample_nos_Y.append(sample_number)
            
        elif len(entry) != 0:
            print 'ERROR: repeated entry'
    
    Y_scaled = [(2*(y - min(Y))/(max(Y) - min(Y)) - 1) for y in Y]
    
    return Y_scaled, sample_nos_Y

def gen_X(sample_numbers_Y, all_full_models, model_select_code):
    # Generates X and Y to fit one model for one equipment and data_type
    X = []
    for i in sample_numbers_Y:
        full_model_lin = all_full_models[i - 1]
            
        full_model_selected = [p for i, p in enumerate(full_model_lin) if i in model_select_code]
            
        X.append(full_model_selected)

    return X
    
def gen_terms_key():
    # Generates the key to the model codes
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

def gen_all_possible_models(db, up_to_no_terms):
    # Generates all the possible 2nd order Scheffe models
    # up to a given number of model terms
    terms_key = gen_terms_key()

    cnt = 0
    t = time()

    for k in range(up_to_no_terms):
        number_of_terms = k + 1
        check = db.search(Query().NumberofTermsDone == number_of_terms)

        if len(check) == 0:
            db.insert({'NumberofTermsDone': number_of_terms})

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
            print 'Models with', number_of_terms, 'terms already done'

    my_sound()

def fit_1_model(db, equipment, data_type, model, model_code, Y, sample_numbers_Y, all_full_models):
    # Fits one model to given Y and enters into fitted models db
    check = db.search((Query().model_code == model_code)&
                      (Query().equipment_name == equipment)&
                      (Query().data_type == data_type))

    if len(check) == 0:
        X = gen_X(sample_numbers_Y, all_full_models, model_code)
        model.fit(X, Y)
        coef = model.coef_
        scores = cross_val_score(model, X, Y)
        R_sqrd = model.score(X,Y)
        F, p_val = f_classif(X, Y)

        entry = {'model_code': model_code,
                 'n_terms': len(model_code),
                 'equipment_name': equipment,
                 'data_type': data_type,
                 'coef': list(coef),
                 'kfold_scores': list(scores),
                 'R_sqrd': R_sqrd,
                 'p_val': list(p_val)
                }

        db.insert(entry)

def fit_models_per_data_type(db, sv_db, equipment, data_type, model, all_full_models, only_model_codes):
    # Fits all the models for a certain data type
    Y, sn_Y = gen_Y(sv_db, equipment, data_type)
    
    for i in only_model_codes[:100]:
        model_code = i['mk']
        fit_1_model(db, equipment, data_type, model, model_code, Y, sn_Y, all_full_models)
        
def get_data_req_to_fit_model():
    # Calculates all the data required to run fit_models_per_data_type
    # that does not need to be recalculated in fit_models_per_data_type
    all_mod_db = access_other_db(0)
    sv_db = access_sv_db()
    fit_res_db = access_other_db(2)
    only_model_codes = all_mod_db.search(Query().mk.exists())
    model = LinearRegression(fit_intercept=False)
    all_full_models = get_all_lin_model_inp()
    return fit_res_db, sv_db, model, all_full_models, only_model_codes