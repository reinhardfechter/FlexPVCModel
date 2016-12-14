from __future__ import division
import glob
import os
import os.path
import pandas
import datahandling

from logging import debug
from numpy import isnan, argmax, argmin, mean, where, trapz, log, abs
from tinydb import Query
from lmfit import minimize
from thermomat_functions import f2min, find_cut_point, rand_ini_val, parameters

q = Query()

class Equipment(object):
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
    name = "base"
    encoding = 'iso-8859-1'

    def __init__(self):
        self.data = None

    def read_data(self, filename):
        """ Generic method to read from a file"""
        self.data = pandas.read_table(filename, skiprows=self.skiprows,
                                      sep=self.sep, encoding=self.encoding)

    def simple_data(self, filename):
        self.read_data(filename)
        return self.simplify_data()

    def simplify_data(self):
        return [self.data[field].values for field in self.datafields]

    def alldatafiles(self):
        return glob.glob(os.path.join(datahandling.datadir,
                                      self.name,
                                      self.file_type))

    def sample_number(self, filename):
        """ Given a filename, parse out the sample number - override"""
        raise NotImplementedError

    def file_parse(self, f):
        direct, filename = os.path.split(f)
        return self.sample_number(filename)
        
    def raw_data_to_db(self, db):
        """ Take raw data, process it and place it into database """
        
        File = self.alldatafiles()
        f = File[0]
        sample_numbers, vals = self.simple_data(f)

        for sample_number, val in zip(sample_numbers, vals):

            done = db.contains((q.equipment_name == self.name) & (q.sample_number == int(sample_number)))

            if not done:
                entry = {'equipment_name': self.name,
                         'sample_number': int(sample_number),
                         'data_type': self.data_type,
                         'value': val
                         }
                db.insert(entry)


class Thermomat(Equipment):
    skiprows = 4
    sep = ';'
    name = 'thermomat'
    file_type = '*.txt'

    def simple_data(self, filename):
        """
        This overrides the simple_data in the base class.

        :param filename: filename to read from
        :return: simple data
        """
        self.read_data(filename)

        time_data = self.data['s'].values / 60
        conduct_data = self.data[self.data.columns[1]].values
        return [time_data, conduct_data]

    def sample_number(self, filename):
        split_filename = filename.split(' ')
        sample_number = split_filename[1]

        return sample_number
        
    def raw_data_to_db(self, db, redo=False):
        """ Setting redo = True will repeat analysis even if it has been done for that sample already
        The data in the data base will only be updated if the Error is less """

        files = self.alldatafiles()

        q = Query()

        for j, f in enumerate(files):
            # Parsing filename
            sample_number = self.file_parse(f)

            # Check if the relevant data exists and only do fit if necessary
            done = db.contains((q.equipment_name == self.name)
                               & (q.sample_number == int(sample_number)))

            if done and not redo:
                debug('Skipped Fit %d', (j + 1))
                continue

            # Get data
            time_data, conduct_data = self.simple_data(f)

            # Trim Data
            cut_point = find_cut_point(conduct_data)

            if cut_point is not None:
                time_data = time_data[:cut_point]
                conduct_data = conduct_data[:cut_point]

            # Remove offset
            min_cond = min(conduct_data)
            conduct_data[:] = [cond - min_cond for cond in conduct_data]

            # Find max conductivity to set upper limit of initial beta value
            max_cond = max(conduct_data)
            ini_val_up_lim = [50.0, 500.0, 3.0 * max_cond, 1.5]

            # Fit Data with multiple starts
            starts = 10
            smallest_err = None

            for i in range(starts):
                ini_val = rand_ini_val(ini_val_up_lim)
                p0 = parameters(ini_val, ini_val_up_lim)
                result = minimize(f2min, p0, args=(time_data, conduct_data))
                p = result.params

                err = f2min(p, time_data, conduct_data)
                int_abs_err = trapz(abs(err), x=time_data)

                if smallest_err is None or int_abs_err < smallest_err:
                    smallest_err = int_abs_err
                    best_p = p

            # Entering info into tinydb
            # If previous value exist only update if err is less
            p_names = ['theta', 'tau', 'beta', 'm']
            values = [best_p[i].value for i in p_names]

            data_types = p_names
            data_types.append('int_of_abs_err')
            values.append(smallest_err)

            # Calculate and enter stability time
            # stability time used corresponds to the intercept
            # between the tangent line at the inflection point to the t axis
            theta = best_p['theta'].value
            tau = best_p['tau'].value

            stab_time = tau * (1 - (log(theta) / (theta - 1))) * ((theta - 1) ** (1 / theta))
            data_types.append('stab_time_min')
            values.append(stab_time)

            if not done:
                datahandling.insert_update_db(db, False, self.name, sample_number, data_types, values)
            else:
                old_err = db.search(datahandling.my_query(self.name, sample_number, 'int_of_abs_err'))[0]['value']
                if smallest_err < old_err:
                    datahandling.insert_update_db(db, True, self.name, sample_number, data_types, values)
                    debug('Updated Sample Number %s', sample_number)


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
        
    def raw_data_to_db(self, db):
        Files = self.alldatafiles()

        for f in Files:
            sample_no = self.file_parse(f)

            done = db.contains((q.sample_number == int(sample_no)) &
                               (q.equipment_name == self.name)
                               )

            if not done:
                params, param_vals = self.simple_data(f)

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

                datahandling.insert_update_db(db, False, self.name, sample_no, data_types, values)
            else:
                debug('skipped sample %s', sample_no)


class Rheomix(Equipment):
    skiprows = 3
    sep = ';'
    datafields = 't [min]', 'Torque [Nm]'
    name = 'rheomix'
    file_type = '*.txt'

    def sample_number(self, filename):
        split_filename = filename.split('_')
        sample_number = split_filename[1][1:]
        return sample_number
        
    def raw_data_to_db(self, db):
        for f in self.alldatafiles():
            sample_number = self.file_parse(f)

            done = db.contains((q.equipment_name == self.name)
                               & (q.sample_number == int(sample_number)))

            if done:
                debug('Skipped Sample %s', sample_number)
                continue

            time_data, torque_data = self.simple_data(f)

            # Remove NaN from data

            time_data = time_data[~isnan(time_data)]
            torque_data = torque_data[~isnan(torque_data)]

            # Find the first maximum of the curve
            # initial maximum for sample entering the rheomix

            no_of_data_points = len(torque_data)

            # Divide data in to the first third and the second two thirds to capture the two maximums

            cut_point = no_of_data_points // 3
            torque_data_1 = torque_data[:cut_point]
            index_1 = argmax(torque_data_1)

            # Sample 4 needs special attention since it has a maximum before the initial maximum

            if sample_number == '04':
                extra = 1
                torque_data = torque_data[index_1 + extra:]
                time_data = time_data[index_1 + extra:]
                torque_data_1 = torque_data[:cut_point]
                index_1 = argmax(torque_data_1)

            # Cut data to exclude data points before first maximum

            time_data = time_data[index_1:]
            torque_data = torque_data[index_1:]

            # Filter Data using EWMA Filter
            # 0 < alpha <= 1
            # alpha = 1 is no filtering, decrease alpha increase filtering

            alpha = 0.05
            my_com = 1.0 / alpha - 1.0

            torque_data = pandas.ewma(torque_data, com=my_com)

            # Find the second maximum of the curve
            # second maximum for final degradation point

            torque_data_2 = torque_data[cut_point:]

            index_2 = argmax(torque_data_2)
            index_2 = cut_point + index_2

            # Determine stability time

            index_min = argmin(torque_data[:index_2])
            torque_min = torque_data[index_min]

            # Threshold value set by user but is the same for every curve

            threshold = torque_min + 3.0

            i = 0
            t = torque_data[i]
            while t > threshold:
                i += 1
                t = torque_data[i]

            index_stab_start = i

            i = index_min
            t = torque_data[i]

            while t < threshold:
                i += 1
                t = torque_data[i]

            index_stab_end = i

            # Calculate stability time, resting torque, final degradation time

            stab_time = round(time_data[index_stab_end] - time_data[index_stab_start], 1)

            stab_torque = torque_data[index_stab_start:index_stab_end]
            rest_torque = round(mean(stab_torque), 1)

            final_deg_time = round(time_data[index_2] - time_data[index_stab_start], 1)

            diff_long_short = round(final_deg_time - stab_time, 1)

            # Insert single value data into data base

            data_types = ['stability_time_min',
                          'final_deg_time_min',
                          'diff_long_short_stab_min',
                          'resting_torque_Nm'
                          ]

            values = [stab_time, final_deg_time, diff_long_short, rest_torque]

            datahandling.insert_update_db(db, False, self.name, sample_number, data_types, values)

            debug('Processed Sample %s', sample_number)
        

class MCC(Equipment):
    skiprows = 7
    sep = "\t"
    datafields = 'Time (s)', 'Temperature (C)', 'HRR (W/g)'
    name = 'MCC'
    file_type = '*.txt'

    def sample_number(self, filename):
        split_filename = filename.split('.')
        split_filename = split_filename[0].split('_')
        sample_number = split_filename[0]
        return sample_number
    
    def raw_data_to_db(self, db):
        Files = self.alldatafiles()

        for f in Files:
            sample_number = self.file_parse(f)

            if sample_number in ['3', '4']:
                double = True
            else:
                double = False

            done = db.count((q.equipment_name == self.name) & (q.sample_number == int(sample_number)))

            if (not double and done == 9) or (double and done == 18):
                debug('Skipped Sample %s', sample_number)
                continue

            time_data, temp_data, HRR_data = self.simple_data(f)

            # cut data to exclude first 100 s and everything after 600 s

            cut_point = where(time_data == 100)[0][0]

            time_data = time_data[cut_point:]
            temp_data = temp_data[cut_point:]
            HRR_data = HRR_data[cut_point:]

            # Remove offste
            min_HRR = min(HRR_data)
            HRR_data[:] = [HRR - min_HRR for HRR in HRR_data]

            # Find first max

            ind_max_1 = argmax(HRR_data)

            # Find second max

            cut_end = where(time_data == 500)[0][0]
            ind_min_2 = argmin(HRR_data[ind_max_1:cut_end])
            ind_min_2 += ind_max_1
            ind_max_2 = argmax(HRR_data[ind_min_2:])
            ind_max_2 += ind_min_2

            # Data for each max

            indeces = [ind_max_1, ind_max_2]
            data = [time_data, temp_data, HRR_data]

            for j, i in enumerate(indeces):
                max_no = str(j + 1)
                names = ['time_s', 'temp_C', 'HRR_Wpg']
                names = [(n + '_peak_' + max_no) for n in names]
                values = [d[i] for d in data]
                values = [round(v, 3) for v in values]

                datahandling.insert_update_db(db, False, self.name, sample_number, names, values)

            # Calculate area under HRR curve to calculate total HR
            t_HR = trapz(HRR_data, x=time_data) / 1000
            t_HR_peak_1 = trapz(HRR_data[:ind_min_2], x=time_data[:ind_min_2]) / 1000
            t_HR_peak_2 = trapz(HRR_data[ind_min_2:], x=time_data[ind_min_2:]) / 1000

            names = ['t_HR_kJpg', 't_HR_peak_1_kJpg', 't_HR_peak_2_kJpg']
            values = [t_HR, t_HR_peak_1, t_HR_peak_2]
            values = [round(v, 3) for v in values]

            datahandling.insert_update_db(db, False, self.name, sample_number, names, values)


class Colour(Equipment):
    sep = ';'
    datafields = 'Sample', 'AVG YI'
    name = 'colour'
    data_type = 'YI'


class LOI(Equipment):
    datafields = 'Sample Number', 'LOI Final'
    name = 'LOI'
    data_type = 'Final'


class Tensile(Equipment):
    datafields = 'Sample Number', 'E_t', 'sigma_M', 'epsilon_M', 'sigma_B', 'epsilon_B'
    name = 'tensile'
    
    def raw_data_to_db(self, db):
        File = self.alldatafiles()
        f = File[0]

        data = self.simple_data(f)
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
                done = db.contains((q.equipment_name == self.name) &
                                   (q.sample_number == int(n)) &
                                   (q.specimen_number == int(s)) &
                                   (q.data_type == d_n)
                                   )
                if not done:
                    entry = {'equipment_name': self.name,
                             'sample_number': int(n),
                             'specimen_number': int(s),
                             'data_type': d_n,
                             'value': val
                             }
                    db.insert(entry)


class MassFrac(Equipment):
    sep = ';'
    datafields = 'Run', 'PVC', 'Filler', 'FR', 'Stabiliser', 'DINP', 'LDH', 'Spherical F.'
    name = 'MassFrac'
    
    def raw_data_to_db(self, db):
        File = self.alldatafiles()
        f = File[0]

        data = self.simple_data(f)
        sample_numbers = data[0]
        data = data[1:]

        ingredients = ['PVC', 'filler', 'FR', 'stabiliser', 'DINP', 'LDH', 'spherical_filler']

        for d, d_n in zip(data, ingredients):
            for n, val in zip(sample_numbers, d):
                done = db.contains((q.sample_number == n) &
                                   (q.data_type == self.name) &
                                   (q.ingredient == d_n)
                                   )

                if not done:
                    entry = {'sample_number': int(n),
                             'data_type': self.name,
                             'ingredient': d_n,
                             'value': val
                             }

                    db.insert(entry)

# The basic idea is that you would write all the functions you have everywhere
# which currently accept an equipment argument and then behave differently as
# methods of the particular equipment class. This keeps equipment-specific logic
# in one place.
