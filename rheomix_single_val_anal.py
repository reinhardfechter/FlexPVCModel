from __future__ import division
from __future__ import print_function
from datahandling import alldatafiles, file_parse, DataFile, insert_update_db, my_query
from numpy import isnan, argmax, argmin, mean
from pandas import ewma
from tinydb import TinyDB, Query

def rheomix_sva(db):
    Q = Query()
    equipment = 'rheomix'

    for f in alldatafiles(equipment):
        sample_number = file_parse(f, equipment)

        done = db.contains((Q.equipment_name == equipment)
                          & (Q.sample_number == int(sample_number)))

        if done:
            print('Skipped Sample', sample_number)
            continue

        time_data, torque_data = DataFile(f, equipment).simple_data(equipment)

        # Remove NaN from data

        time_data = time_data[~isnan(time_data)]
        torque_data = torque_data[~isnan(torque_data)]

        # Find the first maximum of the curve
        # initial maximum for sample entering the rheomix

        no_of_data_points = len(torque_data)

        # Divide data in to the first third and the second two thirds to capture the two maximums

        cut_point = no_of_data_points//3
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
        my_com = 1.0/alpha - 1.0

        torque_data = ewma(torque_data, com=my_com)

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

        insert_update_db(db, False, equipment, sample_number, data_types,
                         values)

        print('Processed Sample', sample_number)
