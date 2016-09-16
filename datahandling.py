import json
import os
import glob
import pandas as pd
from tinydb import Query, TinyDB

# read configuration file and expand ~ to user directory

def alldatafiles(equipment):
    with open('config.json') as f:
        config = json.load(f)
        datadir = os.path.expanduser(config['Raw_Data'] + equipment + '/')
    
	if equipment in ['thermomat', 'rheomix', 'MCC']:
	    file_type = '*.txt'
	else:
	    file_type = '*.csv'
    return glob.glob(os.path.join(datadir, file_type))
	
class DataFile:
    """ Class for holding data """
    def __init__(self, filename, equipment):
        # Split into directory and filename parts
        self.directory, self.filename = os.path.split(filename)
        # Load with pandas
        if equipment == 'thermomat':
            self.data = pd.read_table(filename, skiprows = 4, sep=';')
        elif equipment == 'ConeCal':
            self.data = pd.read_table(filename, skiprows = 1, sep=',')
        elif equipment == 'rheomix':
            self.data = pd.read_table(filename, skiprows = 3, sep=';')
        elif equipment == 'MCC':
            self.data = pd.read_table(filename, skiprows = 7)
        elif equipment in ['colour', 'LOI']:
            self.data = pd.read_table(filename, sep=';')

    def simple_data(self, equipment):
        if equipment == 'thermomat':
            time_data = self.data['s'].values
            time_data = time_data/60
            conduct_data = self.data[self.data.columns[1]].values
            data = [time_data, conduct_data]
        elif equipment == 'ConeCal':
            time_data = self.data['Time (s)'].values
            HRR_data = self.data[self.data.columns[3]].values
            data = [time_data, HRR_data]
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
           
        return data

def file_parse(f, equipment):
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

def access_db():
    with open('config.json') as f:
        config = json.load(f)
        path = config['Results_Database']
    my_db = TinyDB(path + 'Single_Value_Database.json')
    return my_db
