from __future__ import division
from __future__ import print_function
from datahandling import access_db
from tinydb import Query
from sklearn.preprocessing import StandardScaler, Imputer
from pandas import DataFrame, concat
from sklearn.decomposition import PCA
from datahandling import get_msrmnts


def pca_X(impute=False, exclude_inp=True):
    sv_db = access_db(0, True)

    Q = Query()

    # Extract data from db using pandas to construct X

    compositions = DataFrame(sv_db.search(Q.ingredient.exists()))
    compositions['name'] = compositions.data_type + ' ' + compositions.ingredient
    compositions = compositions[['name', 'sample_number', 'value']].pivot(index='sample_number', columns='name',
                                                                          values='value')

    measurements = get_msrmnts(sv_db, Q)

    alldata = concat([compositions, measurements], axis=1)

    # Database has missing values, missing values can either be
    # replaced by mean or the incomplete rows are excluded from X

    if not impute:
        measurements = measurements.dropna()
        alldata = alldata.dropna()

    if exclude_inp:
        use = measurements
    else:
        use = alldata

    X = use.values.tolist()

    if impute:
        imp = Imputer(missing_values='NaN', strategy='mean', axis=0)
        imp.fit(X)
        X = imp.transform(X)

    X_std = StandardScaler().fit_transform(X)

    #      X    ,df of data used
    return X_std, use


def pca():
    X, df = pca_X()
    my_pca = PCA(n_components=0.99)
    my_pca.fit(X)
    return my_pca
