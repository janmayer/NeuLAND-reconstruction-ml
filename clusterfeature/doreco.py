import joblib
from reconstruct import reconstruct

joblib.Parallel(n_jobs=-1)(joblib.delayed(reconstruct)(15, 30, 600, 500, 4, "inclxx", subrun) for subrun in range(20))
