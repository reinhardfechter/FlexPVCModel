import json
import os
import glob
import pandas as pd

# read configuration file and expand ~ to user directory

def alldatafiles(equipment):
    with open('config.json') as f:
        config = json.load(f)
        datadir = os.path.expanduser(config[equipment])
    
	if equipment == 'thermomat':
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

    def simple_data(self, equipment):
        if equipment == 'thermomat':
            time_data = self.data['s'].values
            time_data = time_data/60
            conduct_data = self.data[self.data.columns[1]].values
            data = [time_data, conduct_data]
        if equipment == 'ConeCal':
            time_data = self.data['Time (s)'].values
            HRR_data = self.data[self.data.columns[3]].values
            data = [time_data, HRR_data]
			
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
    
    return sample_number
	

