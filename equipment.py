import glob
import json
import os

class Equipment:
    """
    Base class for equipment
    Currently implements the stuff that DataFile implements, but without
    accepting an "equipment" argument.
    """

    # These are class properties which can be overridden by classes which inherit from this one
    skiprows = 0  # for read_table
    sep = ';'  # for read_table
    datafields = ()  # for extracting simple_data - the base class doesn't use this
    file_type = "*.csv"  # for alldatafiles


    def read_data(self, filename):
        """ Generic method to read from a file"""
        self.data = pd.read_table(filename, skiprows=self.skiprows, sep=self.sep)


    def simple_data(self, filename):
        self.read_data(filename)
        return self.simplify_data()


    def simplify_data(self):
        return [self.data[field].values for field in self.datafields]


    def alldatafiles(self):
        with open('config.json') as f:
            config = json.load(f)
            datadir = os.path.expanduser(config['Raw_Data'] + self.name + '/')

        return glob.glob(os.path.join(datadir, file_type))


    def sample_number(self, filename):
        """ Given a filename, parse out the sample number - override"""
        raise NotImplementedError


    def file_parse(self, f):
        direct, filename = path.split(f)
        return self.sample_number(filename)


class Thermomat(Equipment):
    skiprows = 4
    sep = ';'
    name = 'thermomat'


    def simple_data(self, filename):
        """
        This overrides the simple_data in the base class.

        :param filename: filename to read from
        :return: simple data
        """
        self.read_data(filename)

        time_data = self.data['s'].values
        time_data = time_data / 60
        conduct_data = self.data[self.data.columns[1]].values
        return [time_data, conduct_data]


    def sample_number(self, filename):
        split_filename = filename.split(' ')
        sample_number = split_filename[1]

        return sample_number


class ConeCal(Equipment):
    skiprows = 1
    sep = ','
    datafields = 'Parameter', 'Value'
    name = 'ConeCal'

    def sample_number(self, filename):
        split_filename = filename.split(' ')
        split_filename = split_filename[1].split('_')
        sample_number = split_filename[0]
        return sample_number


class Rheomix(Equipment):
    skiprows = 3
    sep = ';'
    datafields = 'Parameter', 'Value'
    name = 'rheomix'

    def sample_number(self, filename):
        split_filename = filename.split('_')
        sample_number = split_filename[1][1:]
        return sample_number


class MCC(Equipment):
    skiprows = 0
    sep = "\t"
    datafields = 'Time (s)', 'Temperature (C)', 'HRR (W/g)'
    name = 'MCC'

    def sample_number(self, filename):
        split_filename = filename.split('.')
        split_filename = split_filename[0].split('_')
        sample_number = split_filename[0]
        return sample_number


class Colour(Equipment):
    sep = ';'
    datafields = 'Sample', 'AVG YI'
    name = 'colour'


class LOI(Equipment):
    datafields = 'Sample Number', 'LOI Final'
    name = 'LOI'


class Tensile(Equipment):
    datafields = 'Sample Number', 'E_t', 'sigma_M', 'epsilon_M', 'sigma_B', 'epsilon_B'
    name = 'tensile'


class MassFrac(Equipment):
    sep = ';'
    datafields = 'Run', 'PVC', 'Filler', 'FR', 'Stabiliser', 'DINP', 'LDH', 'Spherical F.'
    name = 'MassFrac'



# The basic idea is that you would write all the functions you have everywhere
# which currently accept an equipment argument and then behave differently as
# methods of the particular equipment class. This keeps equipment-specific logic
# in one place.