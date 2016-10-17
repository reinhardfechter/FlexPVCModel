from __future__ import division
from __future__ import print_function

import json
import os
import glob
import pandas as pd
from tinydb import Query, TinyDB
from logging import debug

with open('config.json') as f:
    config = json.load(f)
    datadir = os.path.expanduser(config['Raw_Data'])
    dbpath = os.path.expanduser(config['Databases'])

    assert os.path.exists(datadir)
    assert os.path.exists(dbpath)

def my_query(equipment, sample_number, data_type):
    my_q = ((Query().equipment_name == equipment) &
            (Query().sample_number == int(sample_number)) &
            (Query().data_type == data_type))
    return my_q

def insert_update_db(db, update, equipment, sample_number, names, values):
    """ Insert or update multiple data entries for the Single_Value_Database """
    for n, v in zip(names, values):
        if not update:
            entry = {'equipment_name': equipment,
                     'sample_number': int(sample_number),
                     'data_type': n,
                     'value': v
                    }
            db.insert(entry)

        else:
            db.update({'value': v}, my_query(equipment, sample_number, n))

def access_db(db, from_list):
    """ Accessing the databases
    If from_list is True then enter index of desired db name
    If from_list is False then enter db name as first entry """
    db_names = ['Single_Value_Database',
                'All_Lin_Full_Model_Inputs',
                'Only_Top_Models']
    if from_list:
        db_name = db_names[db]
        debug('Accessed db: %s', db_name)
    else:
        db_name = db
    
    my_db = TinyDB(os.path.join(dbpath, db_name + '.json'))
    return my_db


def get_equip_names(db):
    """ Get the equipment names from the Single_Value_Database """
    all_relevant = db.search(Query().equipment_name.exists())
    return list(set(extractnames(all_relevant, 'equipment_name')))

def get_dtype_names(db, equipment):
    """ Get the data types given an equipment name from the Single_Value_Database """
    equip_data = db.search(Query().equipment_name == equipment)
    return list(set(extractnames(equip_data, 'data_type')))

def extractnames(dictlist, *names):
    assert len(names) > 0
    result = list(map(list, list(zip(*[[item[name] for name in names]
                                  for item in dictlist]))))
    if len(names) == 1:
        return result[0]
    else:
        return result
