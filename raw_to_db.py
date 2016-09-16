from datahandling import alldatafiles, DataFile
from tinydb import Query

def raw_to_db(db, equipment, data_type):
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
        