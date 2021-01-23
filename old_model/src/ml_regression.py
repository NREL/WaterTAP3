import numpy as np

# import wntr
import matplotlib.pyplot as plt
import itertools
import pandas as pd

# import pyomo.environ as env
import ast
from ast import literal_eval
import datetime
import time
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LassoCV
from sklearn.linear_model import Lasso
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn import datasets
from sklearn.linear_model import LassoCV
from sklearn import ensemble
from scipy.optimize import curve_fit

import matplotlib.pyplot as plt
import numpy as np
from sklearn import datasets, ensemble
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

import statsmodels.api as sm


def make_df_for_ml(df1):

    poly2 = PolynomialFeatures(3, include_bias=False)
    # X1=np.array(10*np.random.randn(37,3)) test
    df1 = df1.copy(deep=True)
    df1 = df1.T
    X = []
    for column_name in df1.columns:
        X.append(list(df1[column_name]))
        X2 = np.array(X)

    X_poly = poly2.fit_transform(X2)
    X_poly_feature_name = poly2.get_feature_names(
        ["Feature" + str(l) for l in range(1, 4)]
    )

    df_poly = pd.DataFrame(X_poly, columns=X_poly_feature_name)

    return df_poly


def make_simple_poly(df, y_value):

    from sklearn.preprocessing import PolynomialFeatures

    df["y"] = df[y_value]
    del df[y_value]

    n = 0
    for c_name in df.columns:
        if c_name != "y":
            n = n + 1
            df[("Feature%s" % n)] = df[c_name]
            del df[c_name]

    poly2 = PolynomialFeatures(3, include_bias=False)
    # X1=np.array(10*np.random.randn(37,3)) test
    df1 = df.copy(deep=True)
    del df1["y"]
    df1 = df1.T
    X = []
    for column_name in df1.columns:
        X.append(list(df1[column_name]))
        X2 = np.array(X)

    X_poly = poly2.fit_transform(X2)
    X_poly_feature_name = poly2.get_feature_names(
        ["Feature" + str(l) for l in range(1, 4)]
    )

    df_poly = pd.DataFrame(X_poly, columns=X_poly_feature_name)

    poly = PolynomialFeatures(3, include_bias=False)

    # X1=np.array(10*np.random.randn(37,3)) test
    df1 = df.copy(deep=True)
    del df1["y"]
    df1 = df1.T
    X = []
    for column_name in df1.columns:
        X.append(list(df1[column_name]))
        X2 = np.array(X)

    X_poly = poly.fit_transform(X2)
    X_poly_feature_name = poly.get_feature_names(
        ["Feature" + str(l) for l in range(1, 4)]
    )

    df_poly = pd.DataFrame(X_poly, columns=X_poly_feature_name)
    df_poly["y"] = df["y"]

    X_train = df_poly.drop("y", axis=1)
    y_train = df_poly["y"]

    poly = LinearRegression(normalize=True)

    model_poly = poly.fit(X_train, y_train)
    y_poly = poly.predict(X_train)
    RMSE_poly = np.sqrt(np.sum(np.square(y_poly - y_train)))
    # print("Root-mean-square error of simple polynomial model:",RMSE_poly)
    # print ("R2 value of simple polynomial model:",model_poly.score(X_train,y_train))

    coeff_poly = pd.DataFrame(
        model_poly.coef_,
        index=df_poly.drop("y", axis=1).columns,
        columns=["Coefficients"],
    )

    return poly, coeff_poly


def get_linear_regression(x_values, y_values, variable=None):
    # print('nonlinear did not work, trying linear for:', variable)

    from sklearn.linear_model import LinearRegression

    X = np.array(x_values).reshape(-1, 1)
    y = np.array(y_values).reshape(-1, 1)
    reg = LinearRegression().fit(X, y)
    # print('linear score for:', variable, reg.score(X, y))

    # a_list=[0] -> NOT SURE WHY THIS WAS HERE
    a = reg.coef_[0]
    b = reg.intercept_
    # threshold_temp=[0]

    return a[0], b[0]

def power_law(x, a, b):
    return a*np.power(x, b)


def get_cost_curve_coefs(data_id = None):
    
    df = pd.read_excel("../WaterTAP3CostCurves.xlsx", sheet_name="CostData")
    
    xs = df[((df.DataID == data_id) & (df.VariableID == 2))].Value.values
    
    ys = df[((df.DataID == data_id) & (df.VariableID == 1))].Value.values
    
    pars, cov = curve_fit(f=power_law, xdata=xs, ydata=ys)
    
    ys_new = pars[0] * xs ** pars[1] 
    
    r2_result = np.corrcoef(ys, ys_new)[0, 1]
    
    return pars, r2_result #, xs, ys

def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
