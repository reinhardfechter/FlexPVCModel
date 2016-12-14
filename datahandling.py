from __future__ import division
from __future__ import print_function

import json
import os
from logging import debug
from pandas import DataFrame
from tinydb import Query, TinyDB

Q = Query()

with open('config.json') as f:
    config = json.load(f)
    datadir = os.path.expanduser(config['Raw_Data'])
    dbpath = os.path.expanduser(config['Databases'])

    assert os.path.exists(datadir)
    assert os.path.exists(dbpath)


def my_query(equipment, sample_number, data_type):
    my_q = ((Q.equipment_name == equipment) &
            (Q.sample_number == int(sample_number)) &
            (Q.data_type == data_type))
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
                'Only_Top_Models',
                'Select_Models']
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


def get_msrmnts(sv_db, Q):
    """Get all the measured data form the single value database"""
    measurements = DataFrame(sv_db.search(Q.equipment_name.exists() & Q.data_type.exists()))
    measurements['name'] = measurements.equipment_name + ' ' + measurements.data_type
    # This will automatically average the different measurements which repeat
    measurements = measurements.pivot_table(index='sample_number', columns='name', values='value')

    measurements = measurements.drop([#u'tensile E_t_MPa_mean',
                                      # u'tensile epsilon_break_%_mean',
                                      # u'tensile epsilon_max_%_mean',
                                      # u'tensile sigma_break_MPa_mean',
                                      # u'tensile sigma_max_MPa_mean',
                                      u'thermomat int_of_abs_err',
                                      u'ConeCal C-factor',
                                      u'tensile epsilon_max_%',
                                      u'tensile sigma_max_MPa',
                                      u'rheomix diff_long_short_stab_min'
                                      ], axis=1)

    return measurements


def access_file(f_name, write=True):
    if not write:
        return open(os.path.join(dbpath, f_name), 'r')
    return open(os.path.join(dbpath, f_name), 'wb')
