from datahandling import alldatafiles, DataFile
from tinydb import Query

def raw_to_db(db, equipment, data_type):
    # Works for LOI and Colour Data
    
    File = alldatafiles(equipment)
    f = File[0]
    sample_numbers, vals = DataFile(f, equipment).simple_data(equipment)
    
    Q = Query()

    for sample_number, val in zip(sample_numbers, vals):
        
        check = db.search((Q.equipment_name == equipment) & (Q.sample_number == int(sample_number)))
        
        if len(check) == 0:
            entry = {'equipment_name': equipment,
                     'sample_number': int(sample_number),
                     'data_type': data_type,
                     'value': val
                    }
            db.insert(entry)
            
def raw_to_db_tensile(db):
    equipment = 'tensile'
    Q = Query()
    File = alldatafiles(equipment)
    f = File[0]
    
    data = DataFile(f, equipment).simple_data(equipment)
    data_types = ['E_t_MPa', 'sigma_max_MPa', 'epsilon_max_%',
                  'sigma_break_MPa', 'epsilon_break_%']
    
    sample_numbers = data[0]
    data = data[1:]
    
    specimens = []
    sample_numbers_only = []
    for n in sample_numbers:
        n_split = n.split('_')
        sample_numbers_only.append(n_split[0])
        specimens.append(n_split[1])
    
    for d, d_n in zip(data, data_types):
        for n, s, val in zip(sample_numbers_only, specimens, d):
            check = db.search((Q.equipment_name == equipment) &
                              (Q.sample_number == int(n)) &
                              (Q.specimen_number == int(s)) &
                              (Q.data_type == d_n)
                             ) 
            if len(check) == 0:
                entry = {'equipment_name': equipment,
                         'sample_number': int(n),
                         'specimen_number': int(s),
                         'data_type': d_n,
                         'value': val
                        }
                db.insert(entry)
                
def raw_to_db_massfrac(db):
    Q = Query()
    File = alldatafiles('InputMassFractions')
    f = File[0]
    
    raw_in = 'MassFrac'
    
    data = DataFile(f, raw_in).simple_data(raw_in)
    sample_numbers = data[0]
    data = data[1:]
    
    ingredients = ['PVC', 'filler', 'FR', 'stabiliser', 'DINP', 'LDH', 'spherical_filler']
    
    for d, d_n in zip(data, ingredients):
        for n, val in zip(sample_numbers, d):
            check = db.search((Q.sample_number == n) &
                              (Q.data_type == raw_in) &
                              (Q.ingredient == d_n)
                             )

            if len(check) == 0:
                entry = {'sample_number': int(n),
                         'data_type': raw_in,
                         'ingredient': d_n,
                         'value': val
                        }

                db.insert(entry)
    
    
    
        