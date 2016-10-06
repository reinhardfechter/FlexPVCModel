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

    def read_data(self, filename):
        """ Generic method to read from a file"""
        self.data = pd.read_table(filename, skiprows=self.skiprows, sep=self.sep)

    def simple_data(self, filename):
        self.read_data(filename)
        return self.simplify_data()

    def simplify_data(self):
        return [self.data[field].values for field in self.datafields]


class Thermomat(Equipment):
    skiprows = 4
    sep = ';'

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


class ConeCal(Equipment):
    skiprows = 1
    sep = ','
    datafields = 'Parameter', 'Value'


class LOI(Equipment):
    datafields = 'Sample Number', 'LOI Final'


class MCC(Equipment):
    skiprows = 0
    sep = "\t"
    datafields = 'Time (s)', 'Temperature (C)', 'HRR (W/g)'


class MassFrac(Equipment):
    sep = ';'
    datafields = 'Run', 'PVC', 'Filler', 'FR', 'Stabiliser', 'DINP', 'LDH', 'Spherical F.'


class Colour(Equipment):
    sep = ';'
    datafields = 'Sample', 'AVG YI'


class Rheomix(Equipment):
    skiprows = 3
    sep = ';'
    datafields = 'Parameter', 'Value'


class Tensile(Equipment):
    datafields = 'Sample Number', 'E_t', 'sigma_M', 'epsilon_M', 'sigma_B', 'epsilon_B'



# The basic idea is that you would write all the functions you have everywhere
# which currently accept an equipment argument and then behave differently as
# methods of the particular equipment class. This keeps equipment-specific logic
# in one place.