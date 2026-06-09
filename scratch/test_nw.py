import numpy as np
import pandas as pd
import statsmodels.api as sm
import scipy.stats as stats

def calculate_t_stat(r, n):
    if n <= 2 or abs(r) >= 1.0:
        return 0.0
    return r * np.sqrt((n - 2) / (1 - r**2))

def fast_newey_west_t(x, y, lags):
    n = len(x)
    if n <= 3:
        return 0.0
    X = np.column_stack((np.ones(n), x))
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    residuals = y - X @ beta
    
    omega = np.zeros((2, 2))
    for t in range(n):
        xt = X[t, :]
        et = residuals[t]
        omega += (et**2) * np.outer(xt, xt)
        
    for j in range(1, lags + 1):
        weight = 1.0 - (j / (lags + 1.0))
        for t in range(j, n):
            xt = X[t, :]
            xt_j = X[t - j, :]
            et = residuals[t]
            et_j = residuals[t - j]
            term = et * et_j * (np.outer(xt, xt_j) + np.outer(xt_j, xt))
            omega += weight * term
            
    var_beta = XtX_inv @ omega @ XtX_inv
    std_beta = np.sqrt(max(var_beta[1, 1], 1e-12))
    t_stat = beta[1] / std_beta
    return t_stat

# Test data
np.random.seed(42)
x = np.random.randn(100)
y = 0.5 * x + np.random.randn(100)
lags = 2

# Statsmodels
X_sm = sm.add_constant(x)
model = sm.OLS(y, X_sm).fit(cov_type='HAC', cov_kwds={'maxlags': lags})
sm_t = model.tvalues[1]

# Fast numpy
np_t = fast_newey_west_t(x, y, lags)

print("Statsmodels t-stat:", sm_t)
print("Numpy fast t-stat: ", np_t)
print("Diff:              ", abs(sm_t - np_t))
