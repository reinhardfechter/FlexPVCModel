from __future__ import print_function
from tinydb import Query
from datahandling import access_db

Q = Query()

def get_formulation(db, sample_number):
    """ Get mass fractions of the ingredients for a certain sample """
    ingredients = ['PVC', 'filler', 'FR', 'stabiliser', 'DINP', 'LDH', 'spherical_filler']
    
    formulation = []
    for ing in ingredients:
        mass_fr_entr = db.search((Q.sample_number == sample_number) &
                                 (Q.ingredient == ing)
                                )
        formulation.append(mass_fr_entr[0]['value'])

    return formulation
    
def all_formulations(db):
    """ Get formulation for every sample """
    all_form = []

    for i in range(53):
        sample_number = i + 1
        formulation = get_formulation(db, sample_number)

        all_form.append(formulation)
    
    return all_form
    
def full_model_lin(formulation):
    """ Include 2nd order Scheffe model terms """
    fml = formulation
        
    for j, m_fr in enumerate(formulation):
        for k in range(j+1, 7):
            param_2nd = m_fr*formulation[k]
            fml.append(param_2nd)
    
    return fml
    
def all_full_model_lin(db):
    """ Get all the full linearised model input values for each sample """
    all_form = all_formulations(db)

    all_fml = []
    for f in all_form:
        full = full_model_lin(f)
        all_fml.append(full)

    return all_fml

def gen_all_lin_model_inp():
    """ Generates all linearised full 2nd order Scheffe 
    model inputs from space filling experimental design """
    tag = 'All_Lin_Full_Model_List'

    db = access_db(1, True)
    
    if db:
        print('Already generated all linearised full model inputs')
        return

    sv_db = access_db(0, True)
    all_full_models = all_full_model_lin(sv_db)
    db.insert({tag: all_full_models})

def get_all_lin_model_inp():
    """ Gets all the full model inputs from the All_Lin_Full_Model_Inputs """ 
    tag = 'All_Lin_Full_Model_List'
    db = access_db(1, True)
    return db.all()[0][tag]