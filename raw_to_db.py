from __future__ import print_function
from datahandling import insert_update_db, get_dtype_names, extractnames
from tinydb import Query
from numpy import mean
from equipment import LOI, Colour, Tensile, MassFrac, ConeCal
from logging import debug

Q = Query()

def raw_to_db(db, equip_name, data_type):
    """ Works for LOI and Colour Data """
    
    if equip_name == 'LOI':
        equipment = LOI()
    elif equip_name == 'colour':
        equipment = Colour()
        
    File = equipment.alldatafiles()
    f = File[0]
    sample_numbers, vals = equipment.simple_data(f)
           
    for sample_number, val in zip(sample_numbers, vals):
        
        done = db.contains((Q.equipment_name == equipment.name) & (Q.sample_number == int(sample_number)))
        
        if not done:
            entry = {'equipment_name': equipment.name,
                     'sample_number': int(sample_number),
                     'data_type': data_type,
                     'value': val
                    }
            db.insert(entry)
            
def raw_to_db_tensile(db):
    equipment = Tensile()
    File = equipment.alldatafiles()
    f = File[0]
    
    data = equipment.simple_data(f)
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
            done = db.contains((Q.equipment_name == equipment.name) &
                              (Q.sample_number == int(n)) &
                              (Q.specimen_number == int(s)) &
                              (Q.data_type == d_n)
                             ) 
            if not done:
                entry = {'equipment_name': equipment.name,
                         'sample_number': int(n),
                         'specimen_number': int(s),
                         'data_type': d_n,
                         'value': val
                        }
                db.insert(entry)
 
def calc_tensile_mean(sv_db):
    """ Calculates the mean values between the different tensile specimens
    and enters them into the single values database """
    equipment = Tensile()
    data_types = get_dtype_names(sv_db, equipment.name)
    if len(data_types) == 10:
        data_types = [d for i, d in enumerate(data_types) if i in [0,4,6,8,9]]
    
    for i in range(53):
        sn = i + 1

        for dt in data_types:
                data = sv_db.search((Q.equipment_name == equipment.name) &
                                    (Q.sample_number == sn) &
                                    (Q.data_type == dt)
                                   )
                if len(data) != 0:
                    done = sv_db.contains((Q.equipment_name == equipment.name) &
                                         (Q.sample_number == sn) &
                                         (Q.data_type == (dt + '_mean'))
                                         )
                                         
                    if not done:
                        vals = extractnames(data, 'value')
                        mean_val = mean(vals)
                        sv_db.insert({'equipment_name': equipment.name,
                                      'sample_number': sn,
                                      'data_type': (dt + '_mean'),
                                      'value': mean_val})
                              
def raw_to_db_massfrac(db):
    raw_in = MassFrac()
    File = raw_in.alldatafiles()
    f = File[0]
    
    data = raw_in.simple_data(f)
    sample_numbers = data[0]
    data = data[1:]
    
    ingredients = ['PVC', 'filler', 'FR', 'stabiliser', 'DINP', 'LDH', 'spherical_filler']
    
    for d, d_n in zip(data, ingredients):
        for n, val in zip(sample_numbers, d):
            done = db.contains((Q.sample_number == n) &
                              (Q.data_type == raw_in.name) &
                              (Q.ingredient == d_n)
                             )

            if not done:
                entry = {'sample_number': int(n),
                         'data_type': raw_in.name,
                         'ingredient': d_n,
                         'value': val
                        }

                db.insert(entry)
    
def raw_to_db_conecal(db):
    equipment = ConeCal()
    Files = equipment.alldatafiles()

    for f in Files:
        sample_no = equipment.file_parse(f)

        done = db.contains((Q.sample_number == int(sample_no)) &
                          (Q.equipment_name == equipment.name)
                         )

        if not done:
            params, param_vals = equipment.simple_data(f)

            data_types = ['peak_HRR_kWpm2',
                          't_peak_HRR_s',
                          'tot_HR_MJpm2',
                          'tot_O2cons_g',
                          'tot_masslost_g',
                          'tot_smokeprod_m2',
                          'MARHE_kW_m2',
                          'C-factor',
                          't_to_ign_s'
                         ]

            dtype_indexes = [1, 9, 23, 24, 25, 28, 29, 83, 84]

            values = [param_vals[i] for i in dtype_indexes]

            insert_update_db(db, False, equipment.name, sample_no, data_types, values)
        else:
            debug('skipped sample %s', sample_no)
