from __future__ import division
from __future__ import print_function

import json
import os
import glob
import pandas as pd
from tinydb import Query, TinyDB

with open('config.json') as f:
    config = json.load(f)
    datadir = os.path.expanduser(config['Raw_Data'])
    dbpath = os.path.expanduser(config['Databases'])

    assert os.path.exists(datadir)
    assert os.path.exists(dbpath)


def alldatafiles(equipment):
    if equipment in ['thermomat', 'rheomix', 'MCC']:
        file_type = '*.txt'
    else:
        file_type = '*.csv'
    return glob.glob(os.path.join(datadir, equipment, file_type))


class DataFile(object):
    """ Class for holding data """
    def __init__(self, filename, equipment):
        # Split into directory and filename parts
        self.directory, self.filename = os.path.split(filename)
        # Load with pandas
        if equipment == 'thermomat':
            self.data = pd.read_table(filename, skiprows = 4, sep=';', encoding='iso-8859-1')
        elif equipment == 'ConeCal':
            self.data = pd.read_table(filename, skiprows = 1, sep=',', encoding='iso-8859-1')
        elif equipment == 'rheomix':
            self.data = pd.read_table(filename, skiprows = 3, sep=';', encoding='iso-8859-1')
        elif equipment == 'MCC':
            self.data = pd.read_table(filename, skiprows = 7, encoding='iso-8859-1')
        elif equipment in ['colour', 'LOI', 'tensile', 'MassFrac']:
            self.data = pd.read_table(filename, sep=';', encoding='iso-8859-1')

    def simple_data(self, equipment):
        if equipment == 'thermomat':
            time_data = self.data['s'].values/60
            conduct_data = self.data[self.data.columns[1]].values
            data = [time_data, conduct_data]
        elif equipment == 'ConeCal':
            params = self.data['Parameter'].values
            param_vals = self.data['Value'].values
            # time_data = self.data['Time (s)'].values
            # HRR_data = self.data[self.data.columns[3]].values
            data = [params, param_vals]
        elif equipment == 'rheomix':
            time_data = self.data['t [min]'].values
            torque_data = self.data['Torque [Nm]'].values
            data = [time_data, torque_data]
        elif equipment == 'MCC':
            time_data = self.data['Time (s)'].values
            temp_data = self.data['Temperature (C)'].values
            HRR_data = self.data['HRR (W/g)'].values
            data = [time_data, temp_data, HRR_data]
        elif equipment == 'colour':
            sample_numbers = self.data['Sample'].values
            YI = self.data['AVG YI'].values
            data = [sample_numbers, YI]
        elif equipment == 'LOI':
            sample_numbers = self.data['Sample Number'].values
            LOIs = self.data['LOI Final'].values
            data = [sample_numbers, LOIs]
        elif equipment == 'tensile':
            sample_numbers = self.data['Sample Number'].values
            E_t = self.data['E_t'].values
            sigma_M = self.data['sigma_M'].values
            epsilon_M = self.data['epsilon_M'].values
            sigma_B = self.data['sigma_B'].values
            epsilon_B = self.data['epsilon_B'].values
            data = [sample_numbers, E_t, sigma_M, epsilon_M, sigma_B, epsilon_B]
        elif equipment == 'MassFrac':
            sample_numbers = self.data['Run'].values
            PVC = self.data['PVC'].values
            filler = self.data['Filler'].values
            FR = self.data['FR'].values
            stabiliser = self.data['Stabiliser'].values
            DINP = self.data['DINP'].values
            LDH = self.data['LDH'].values
            sphericalF = self.data['Spherical F.'].values
            data = [sample_numbers, PVC, filler, FR, stabiliser, DINP, LDH, sphericalF] 
           
        return data

def file_parse(f, equipment):
    """ Parses file names for different equipments to determine sample numbers """
    from os import path
    
    direct, filename = path.split(f)

    if equipment == 'thermomat':
        split_filename = filename.split(' ')
        sample_number = split_filename[1]
    elif equipment == 'ConeCal':
        split_filename = filename.split(' ')
        split_filename = split_filename[1].split('_')
        sample_number = split_filename[0]
    elif equipment == 'rheomix':
        split_filename = filename.split('_')
        sample_number = split_filename[1][1:]
    elif equipment == 'MCC':
        split_filename = filename.split('.')
        split_filename = split_filename[0].split('_')
        sample_number = split_filename[0]
    
    return sample_number

def my_query(equipment, sample_number, data_type):
    my_q = ((Query().equipment_name == equipment) &
            (Query().sample_number == int(sample_number)) &
            (Query().data_type == data_type))
    return my_q

def insert_update_db(db, update, equipment, sample_number, names, values):
    """ Insert or update multiple data entries for the Single_Value_Database """
    for n, v in zip(names, values):
        if update == False:
            entry = {'equipment_name': equipment,
                     'sample_number': int(sample_number),
                     'data_type': n,
                     'value': v
                    }
            db.insert(entry)

        elif update == True:
            db.update({'value': v}, my_query(equipment, sample_number, n))

def access_db(db, from_list):
    """ Accessing the databases
    If from_list is True then enter index of desired db name
    If from_list is False then enter db name as first entry """
    db_names = ['Single_Value_Database',
                'All_Lin_Full_Model_Inputs',
                'Only_Top_Models']
    if from_list == True:
        db_name = db_names[db]
        print('Accessed db:', db_name)
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
