from datahandling import alldatafiles, DataFile, file_parse
from time import time as tm
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from lmfit import Parameters, minimize, report_fit
from thermomat_functions import cond_model, f2min, find_cut_point, rand_ini_val, parameters
from os import path

def thermomat_sva():
	t = tm()

	sample_number_all = []
	stability_time_all = []

	int_abs_err_all = []
	ps_all = []

	with PdfPages('Test.pdf') as pdf:
		for j, f in enumerate(Files):
			split_tm = tm ()
			time_data, conduct_data = DataFile(f).simple_data()
		
			# Parsing filename
			sample_number = file_parse(f)
			sample_number_all.append(sample_number)
			
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
					
			int_abs_err_all.append(smallest_err)
			ps_all.append(best_p)
					
			# Plot fitted model and raw data
			fig = figure()
			fig.suptitle('Sample Number ' + sample_number)
			plot(time_data, conduct_data)
			plot(time_data, cond_model(best_p, time_data))
			
			pdf.savefig(fig)
			
			split_tm = tm() - split_tm
			print 'Completed Fit', (j + 1), 'in', round(split_tm, 2), '(s)'
	#         print 'Sample Number ', sample_number
	#         print '________________________'
			
	req_time = tm() - t
	print '******************'
	print 'Time required (min) =', round(req_time/60.0, 2)