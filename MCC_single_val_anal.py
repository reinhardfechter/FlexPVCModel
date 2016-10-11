from __future__ import division
from __future__ import print_function

from datahandling import insert_update_db, my_query
from tinydb import Query
from numpy import where, argmax, argmin, trapz
from equipment import MCC
from logging import debug
Q = Query()

def MCC_sva(db):
    equipment = MCC()

    Files = equipment.alldatafiles()

    for f in Files:
        MCC_sva_one_f(db, f, equipment)

def MCC_sva_one_f(db, f, equipment):
    sample_number = equipment.file_parse(f)

    if sample_number in ['3', '4']:
        double = True
    else:
        double = False

    done = db.count((Q.equipment_name == equipment.name) & (Q.sample_number == int(sample_number)))
    
    if (not double and done == 9) or (double and done == 18):
        debug('Skipped Sample %s', sample_number)
        return
    
    time_data, temp_data, HRR_data = equipment.simple_data(f)

    # cut data to exclude first 100 s and everything after 600 s

    cut_point = where(time_data==100)[0][0]

    time_data = time_data[cut_point:]
    temp_data = temp_data[cut_point:]
    HRR_data = HRR_data[cut_point:]

    # Remove offste
    min_HRR = min(HRR_data)
    HRR_data[:] = [HRR - min_HRR for HRR in HRR_data]

    # Find first max

    ind_max_1 = argmax(HRR_data)

    # Find second max

    cut_end = where(time_data==500)[0][0]
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

        insert_update_db(db, False, equipment.name, sample_number, names, values)

    # Calculate area under HRR curve to calculate total HR
    t_HR = trapz(HRR_data, x=time_data)/1000
    t_HR_peak_1 = trapz(HRR_data[:ind_min_2], x=time_data[:ind_min_2])/1000
    t_HR_peak_2 = trapz(HRR_data[ind_min_2:], x=time_data[ind_min_2:])/1000

    names = ['t_HR_kJpg', 't_HR_peak_1_kJpg', 't_HR_peak_2_kJpg']
    values = [t_HR, t_HR_peak_1, t_HR_peak_2]
    values = [round(v, 3) for v in values]

    insert_update_db(db, False, equipment.name, sample_number, names, values)