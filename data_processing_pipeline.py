from __future__ import print_function
from logging import info, basicConfig, DEBUG
from time import time
from ipyparallel import Client
from MCC_single_val_anal import MCC_sva
from datahandling import access_db
from gen_model_inputs import gen_all_lin_model_inp
from model_analysis import get_select_models
from model_scoring_func import gen_all_possible_models, get_all_names, score_models
from raw_to_db import raw_to_db, raw_to_db_conecal, raw_to_db_tensile, calc_tensile_mean, raw_to_db_massfrac
from rheomix_single_val_anal import rheomix_sva
from thermomat_single_val_anal import thermomat_sva

rc = Client()


def preprocessing():
    """ Runs all the functions that put raw data into the single values database """
    sv_db = access_db(0, True)

    equip_names = ['rheomix',
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
    # rc = Client()
    v = rc.load_balanced_view()
    v.block = False

    n_terms = [i + 1 for i in range(28)]

    t = time()

    v.map_async(gen_all_possible_models, n_terms)

    req_time = time() - t
    read_time(req_time)

    info('')
    info('Generate All Possible Models Complete')
    info('****************************')


def model_scoring():
    """Scores the models for all data_types iteratively"""
    # rc = Client()
    v = rc[:]

    t = time()

    for_scoring = get_all_names()

    v.map_sync(score_models, for_scoring)

    req_time = time() - t
    read_time(req_time)


def read_time(req_time):
    hours, seconds_left = divmod(req_time, 3600)
    minutes, seconds = divmod(seconds_left, 60)
    info('Required Time: %d h, %d min and %d s' % (int(hours), int(minutes), int(seconds)))


def full_pipeline():
    """ Runs all the code except the code to generate and store all possible models because
    of issue with running two parallel tasks after each other"""
    basicConfig(filename='full_pipeline.log', level=DEBUG)

    t = time()

    all_poss_models()
    preprocessing()
    gen_all_lin_model_inp()
    model_scoring()
    get_select_models()

    info('')
    info('******************')
    info('Full data processing pipeline complete')
    req_time = time() - t
    read_time(req_time)


if __name__ == "__main__":
    full_pipeline()
