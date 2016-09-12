import json
import os
import glob
import pandas as pd

# read configuration file and expand ~ to user directory
with open('config.json') as f:
    config = json.load(f)
datadir = os.path.expanduser(config['datadir'])

def alldatafiles():
    return glob.glob(os.path.join(datadir, '*.txt'))
	
class DataFile:
    """ Class for holding data """
    def __init__(self, filename):
        # Split into directory and filename parts
        self.directory, self.filename = os.path.split(filename)
        # Load with pandas
        self.data = pd.read_table(filename, skiprows = 4, sep=';')

    def simple_data(self):
        time_data = self.data['s'].values
        time_data = time_data/60
        conduct_data = self.data[self.data.columns[1]].values

        return time_data, conduct_data

def file_parse(f):
    from os import path
    
    direct, filename = path.split(f)
    split_filename = filename.split(' ')
    sample_number = split_filename[1]
    
    return sample_number
