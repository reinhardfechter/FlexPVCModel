from __future__ import print_function
from datahandling import access_db, get_equip_names, get_dtype_names
from rheomix_single_val_anal import rheomix_sva
from thermomat_single_val_anal import thermomat_sva
from MCC_single_val_anal import MCC_sva
from raw_to_db import raw_to_db, raw_to_db_conecal, raw_to_db_tensile, calc_tensile_mean, raw_to_db_massfrac
from model_scoring_func import gen_all_possible_models, get_data_req_to_score_model, score_models_per_data_type
from time import time
from model_analysis import get_top_models
from gen_model_inputs import gen_all_lin_model_inp

def preprocessing():
    """ Runs all the functions that put raw data into the single values database """
    sv_db = access_db(0, True)
    
    equip_names =['rheomix',
                  'thermomat',
                  'colour',
                  'LOI',
                  'MCC',
                  'ConeCal',
                  'tensile',
                  'massfrac'
                 ]
    
    print('****************************')
    print('Data Prepocessing')
    print('')

    for n in equip_names:
        print('Processing', n)
        print('')

        if n == 'rheomix':
            rheomix_sva(sv_db)
        elif n == 'thermomat':
            thermomat_sva(sv_db, False)
        elif n == 'colour':
            raw_to_db(sv_db, n, 'YI')
        elif n == 'LOI':
            raw_to_db(sv_db, n, 'Final')
        elif n == 'MCC':
            MCC_sva(sv_db)
        elif n == 'ConeCal':
            raw_to_db_conecal(sv_db)
        elif n == 'tensile':
            raw_to_db_tensile(sv_db)
            calc_tensile_mean(sv_db)
        elif n == 'massfrac':
            raw_to_db_massfrac(sv_db)


        print('___________________________')

    print('Data Preprocessing Complete')
    print('****************************')
   
def all_poss_models():
    print('****************************')
    print('Generate All Possible Models')
    print('')
   
    gen_all_possible_models(4, True)
    
    print('')
    print('Generate All Possible Models Complete')
    print('****************************')
    
def model_scoring():
    """Scores the models for all data_types iteratively"""
    
    sv_db, model, all_full_models, all_model_codes = get_data_req_to_score_model()
    t = time()
    
    for_scoring = equip_dtypes_for_scoring()

    for i in for_scoring:
        equip_name, data_type = i
        db = access_db('Score_results_'+ equip_name + '_' + data_type, False)
        split_time = time()
        score_models_per_data_type(db, sv_db, equip_name, data_type, model, all_full_models, all_model_codes)
        print('Scored models for', equip_name, data_type)
        split_time = time() - split_time
        print('Split Time:', round(split_time, 2), 's')

    req_time = time() - t
    minutes, seconds = divmod(req_time, 60)
    print('Required Time:', round(minutes), 'min and', round(seconds, 2), 's')
    
def do_not_score_list():
    do_not_score = ['int_of_abs_err',
                  'E_t_MPa',
                  'epsilon_max_%',
                  'epsilon_break_%',
                  'sigma_max_MPa',
                  'sigma_break_MPa',
                  'C-factor'
                 ]
    return do_not_score

def equip_dtypes_for_scoring():
    """ Puts all the data type names and corresponding equipment names that
    are going to be or have been scored in a list """
    sv_db = access_db(0, True)
    equip_names = get_equip_names(sv_db)
    
    dnt_score = do_not_score_list()

    for_scoring = []
    for en in equip_names:
        data_types = get_dtype_names(sv_db, en)

        for dt in data_types:
            if dt not in dnt_score:
                en_dt = [en, dt]
                for_scoring.append(en_dt)
                
    return for_scoring

def get_all_top_models():
    """ Get all the top models for all the different data types which have
    been scored """
    for_scoring = equip_dtypes_for_scoring()
    tm_db = access_db(2, True)
   
    # from tinydb import TinyDB
    # tm_db = TinyDB('test.json')
    
    for i in for_scoring:
        en, dt = i
        sr_db = access_db('Score_results_'+ en + '_' + dt, False)

        get_top_models(tm_db, sr_db, en, dt, 3)

def full_pipeline():
    t = time()
    
    preprocessing()
    all_poss_models()
    gen_all_lin_model_inp()
    model_scoring()
    get_all_top_models()
    
    print('')
    print('******************')
    print('Full data processing timeline complete')
    req_time = time() - t
    hours, seconds_left = divmod(req_time, 3600)
    minutes, seconds = divmod(seconds_left, 60)
    print('Required Time:', int(hours), 'h,', int(minutes), 'min and', int(round(seconds)), 's')


if __name__ == "__main__":
    full_pipeline()