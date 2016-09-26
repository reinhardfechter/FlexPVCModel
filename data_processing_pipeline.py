from datahandling import access_sv_db, get_equip_names
from rheomix_single_val_anal import rheomix_sva
from thermomat_single_val_anal import thermomat_sva
from MCC_single_val_anal import MCC_sva
from raw_to_db import raw_to_db, raw_to_db_conecal, raw_to_db_tensile, raw_to_db_massfrac

def preprocessing():
    # Runs all the functions that put raw data into the single values database
    sv_db = access_sv_db()
    
    equip_names =['rheomix',
                  'thermomat',
                  'colour',
                  'LOI',
                  'MCC',
                  'ConeCal',
                  'tensile',
                  'massfrac'
                 ]
    
    print '****************************'
    print 'Data Prepocessing'
    print ''

    for n in equip_names:
        print 'Processing', n
        print ''

        if n == 'rheomix':
            rheomix_sva(sv_db)
        elif n == 'thermomat':
            thermomat_sva(sv_db, False)
        elif n == 'colour':
            raw_to_db(sv_db, n, 'YI')
        elif n == 'LOI':
            raw_to_db(sv_db, n, 'Final')
        elif n == 'MCC':
            MCC_sva(sv_db)
        elif n == 'ConeCal':
            raw_to_db_conecal(sv_db)
        elif n == 'tensile':
            raw_to_db_tensile(sv_db)
        elif n == 'massfrac':
            raw_to_db_massfrac(sv_db)


        print '___________________________'

    print 'Data Preprocessing Complete'
    print '****************************'