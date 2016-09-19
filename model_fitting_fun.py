from tinydb import Query
from datahandling import my_query
Q = Query()

def get_formulation(db, sample_number):
    # Get mass fractions of the ingredients for a certain sample
    ingredients = ['PVC', 'filler', 'FR', 'stabiliser', 'DINP', 'LDH', 'spherical_filler']
    
    formulation = []
    for ing in ingredients:
        mass_fr_entr = db.search((Q.sample_number == sample_number) &
                                 (Q.ingredient == ing)
                                )
        formulation.append(mass_fr_entr[0]['value'])

    return formulation

def all_formulations(db):
    # Get formulation for every sample
    all_form = []

    for i in range(53):
        sample_number = i + 1
        formulation = get_formulation(db, sample_number)

        all_form.append(formulation)
    
    return all_form

def full_model_lin(formulation):
    # Include 2nd order Scheffe model terms
    fml = formulation
        
    for j, m_fr in enumerate(formulation):
        for k in range(j+1, 7):
            param_2nd = m_fr*formulation[k]
            fml.append(param_2nd)
    
    return fml

def all_full_model_lin(db):
    # Get all the full linearised model input values for each sample
    all_form = all_formulations(db)

    all_fml = []
    for f in all_form:
        full = full_model_lin(f)
        all_fml.append(full)

    return all_fml

def gen_XY(db, equipment, data_type, all_full_models, model_select_code):
    # Generates X and Y to fit one model for one equipment and data_type
    X = []
    Y = []
    for i in range(53):
        sample_number = i + 1
        entry = db.search(my_query(equipment, sample_number, data_type))
        if len(entry) == 1:
            full_model_lin = all_full_models[i]
            
            full_model_selected = [p for i, p in enumerate(full_model_lin) if i in model_select_code]
            
            X.append(full_model_selected)
            Y.append(entry[0]['value'])
            
        elif len(entry) != 0:
            print 'ERROR: repeated entry'
    
    Y_scaled = [(2*(y - min(Y))/(max(Y) - min(Y)) - 1) for y in Y]
    
    return X, Y_scaled
    