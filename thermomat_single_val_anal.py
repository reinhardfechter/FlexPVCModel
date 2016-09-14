from datahandling import alldatafiles, DataFile, file_parse
from time import time as tm
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from lmfit import Parameters, minimize, report_fit
from thermomat_functions import cond_model, f2min, find_cut_point, rand_ini_val, parameters
from os import path
from numpy import trapz
import matplotlib.pyplot as plt
from tinydb import Query

def thermomat_sva(db):
    equipment = 'thermomat'
    
    Files = alldatafiles(equipment)
	
    t = tm()

    Q = Query()

    with PdfPages('Test.pdf') as pdf:
        for j, f in enumerate(Files[:3]):
			split_tm = tm ()
			
			# Parsing filename
			sample_number = file_parse(f, equipment)
			
			# Check if the relevant data exists and only do fit if necessary
			check = db.search((Q.equipment_name == 'thermomat') & (Q.sample_number == int(sample_number)))
			if len(check) == 0:
			
				# Get data
				time_data, conduct_data = DataFile(f, equipment).simple_data(equipment)

				# Trim Data
				cut_point = find_cut_point(conduct_data)

				if cut_point != None:
					time_data = time_data[:cut_point]
					conduct_data = conduct_data[:cut_point]

				# Remove offset
				min_cond = min(conduct_data)
				conduct_data[:] = [cond - min_cond for cond in conduct_data]        

				# Find max conductivity to set upper limit of initial beta value
				max_cond = max(conduct_data)
				ini_val_up_lim = [50.0, 500.0, 3.0*max_cond, 1.5]

				# Fit Data with multiple starts 
				starts = 10
				smallest_err = 10000000.0

				for i in range(starts):
					ini_val = rand_ini_val(ini_val_up_lim)
					p = parameters(ini_val, ini_val_up_lim)
					result = minimize(f2min, p, args=(time_data, conduct_data))

					err_list = f2min(p, time_data, conduct_data)
					abs_err_list = map(abs, err_list)
					int_abs_err = trapz(abs_err_list, x=time_data)

					smallest_err = min([smallest_err, int_abs_err])
					if smallest_err == int_abs_err:
						best_p = p

				# Plot fitted model and raw data
				fig = plt.figure()
				fig.suptitle('Sample Number ' + sample_number)
				plt.plot(time_data, conduct_data)
				plt.plot(time_data, cond_model(best_p, time_data))

				pdf.savefig(fig)
				
				# Entering info into tinydb
				p_names = ['theta', 'tau', 'beta', 'm']

				for pn in p_names:
					entry = {'equipment_name': 'thermomat', 
							 'sample_number': int(sample_number),
							 'data_type': pn,
							 'value': best_p[pn].value}
					db.insert(entry)

				db.insert({'equipment_name': 'thermomat', 
						   'sample_number': int(sample_number),
						   'data_type': 'int_of_abs_err',
						   'value': smallest_err})
				
				split_tm = tm() - split_tm
				print 'Completed Fit', (j + 1), 'in', round(split_tm, 2), '(s)'
			else:
				print 'Skipped Fit', (j + 1)

	req_time = tm() - t
	print '******************'
	print 'Time required (min) =', round(req_time/60.0, 2)