from datahandling import alldatafiles, DataFile, insert_update_db, file_parse, get_dtype_names
from tinydb import Query
from numpy import mean

def raw_to_db(db, equipment, data_type):
    """ Works for LOI and Colour Data """
    
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
 
def calc_tensile_mean(sv_db):
    """ Calculates the mean values between the different tensile specimens
    and enters them into the single values database """
    equipment = 'tensile'
    data_types = get_dtype_names(sv_db, equipment)
    if len(data_types) == 10:
        data_types = [d for i, d in enumerate(data_types) if i in [0,4,6,8,9]]
    
    Q = Query()
    
    for i in range(53):
        sn = i + 1

        for dt in data_types:
                data = sv_db.search((Q.equipment_name == equipment) &
                                    (Q.sample_number == sn) &
                                    (Q.data_type == dt)
                                   )
                if len(data) != 0:
                    check = sv_db.search((Q.equipment_name == equipment) &
                                         (Q.sample_number == sn) &
                                         (Q.data_type == (dt + '_mean'))
                                         )
                                         
                    if len(check) == 0:
                        vals = [d['value'] for d in data]
                        mean_val = mean(vals)
                        sv_db.insert({'equipment_name': equipment,
                                      'sample_number': sn,
                                      'data_type': (dt + '_mean'),
                                      'value': mean_val})
                
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
    
def raw_to_db_conecal(db):
    equipment = 'ConeCal'
    Files = alldatafiles(equipment)

    for f in Files:
        sample_no = file_parse(f, equipment)

        check = db.search((Query().sample_number == int(sample_no)) &
                          (Query().equipment_name == equipment)
                         )

        if len(check) == 0:
            params, param_vals = DataFile(f, equipment).simple_data(equipment)

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

            insert_update_db(db, False, equipment, sample_no, data_types, values)
        else:
            print 'skipped sample', sample_no    
    
        