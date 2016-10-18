from __future__ import print_function
from datahandling import access_db, get_equip_names, get_dtype_names
from rheomix_single_val_anal import rheomix_sva
from thermomat_single_val_anal import thermomat_sva
from MCC_single_val_anal import MCC_sva
from raw_to_db import raw_to_db, raw_to_db_conecal, raw_to_db_tensile, calc_tensile_mean, raw_to_db_massfrac
from model_scoring_func import gen_all_possible_models, get_data_req_to_score_model, score_models_per_data_type, score_model_per_comp
from time import time
from model_analysis import get_top_models
from gen_model_inputs import gen_all_lin_model_inp
from logging import info, basicConfig, DEBUG
from ipyparallel import Client
from random import shuffle
from pca import pca

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
    
    info('****************************')
    info('Data Prepocessing')
    info('')

    for n in equip_names:
        info('Processing %s', n)
        info('')

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


        info('___________________________')

    info('Data Preprocessing Complete')
    info('****************************')

# Calling Client for multiprocessing

    
def all_poss_models():
    info('****************************')
    info('Generate All Possible Models')
    info('')
    
    # Calling Client for multiprocessing
    rc = Client()
    v = rc.load_balanced_view()
    v.block=False
   
    # gen_all_possible_models(1, True)
    n_terms = [i+1 for i in range(4)]
    
    t = time()
    
    v.map_async(gen_all_possible_models, n_terms)
    
    req_time = time() - t
    read_time(req_time)
    
    info('')
    info('Generate All Possible Models Complete')
    info('****************************')
    
def model_scoring():
    """Scores the models for all data_types iteratively"""
    rc = Client()
    v = rc[:]
    
    t = time()

    for_scoring = equip_dtypes_for_scoring(False)

    v.map_sync(score_models_per_data_type, for_scoring)

    req_time = time() - t
    read_time(req_time)
    
def model_scoring_pca():
    rc = Client()
    v = rc[:]
    
    n_comp = pca().n_components_
    
    v.map_sync(score_model_per_comp, range(n_comp))
    
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

def equip_dtypes_for_scoring(do_pca):
    """ Puts all the data type names and corresponding equipment names that
    are going to be or have been scored in a list """
    
    if do_pca:
        my_pca = pca()
        n_comp = my_pca.n_components_
        data_types = ['component_' + str(i + 1) for i in range(n_comp)]
        equips = ['pca' for i in range(n_comp)]
        for_scoring = [[i, j] for i, j in zip(equips, data_types)]
        return for_scoring
    
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

def get_all_top_models(do_pca):
    """ Get all the top models for all the different data types which have
    been scored """
    for_scoring = equip_dtypes_for_scoring(do_pca)
    tm_db = access_db(2, True)
    
    for i in for_scoring:
        en, dt = i
        sr_db = access_db('Score_results_'+ en + '_' + dt, False)

        get_top_models(tm_db, sr_db, en, dt, 3)
        
def read_time(req_time):
    hours, seconds_left = divmod(req_time, 3600)
    minutes, seconds = divmod(seconds_left, 60)
    info('Required Time: %d h, %d min and %d s' % (int(hours), int(minutes), int(seconds)))

def full_pipeline(do_pca):
    basicConfig(filename='full_pipeline.log', level=DEBUG)
    
    t = time()
    
    preprocessing()
    all_poss_models()
    gen_all_lin_model_inp()
    
    if do_pca:
        model_scoring_pca()
    else:
        model_scoring()
    
    get_all_top_models(do_pca)
    
    info('')
    info('******************')
    info('Full data processing pipeline complete')
    req_time = time() - t
    read_time(req_time)

if __name__ == "__main__":
    full_pipeline()