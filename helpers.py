import pathlib
import os
import multiprocessing
import functools
import numpy as np
import pandas as pd

try:
    import ROOT

    ROOT.ROOT.EnableThreadSafety()
except:
    pass


def filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, what):
    path = pathlib.Path(__file__).parent.absolute().joinpath("data")
    if isinstance(subrun, int):
        name = f"{distance}m_{doubleplane}dp_{energy}AMeV_{erel}keV_{neutron}n.{physics}.{subrun:02d}.{what}"
    else:
        name = f"{distance}m_{doubleplane}dp_{energy}AMeV_{erel}keV_{neutron}n.{physics}.{subrun}.{what}"
    return path.joinpath(name)


def processed_events(distance, doubleplane, energy, erel, neutron, physics, subrun, what):
    filename = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, what)
    if filename.is_file():
        try:
            tfile = ROOT.TFile.Open(os.fspath(filename))
            ttree = tfile.Get("evt")
            num_events = int(ttree.GetEntries())
            return (filename, num_events)
        except:
            pass
    return (filename, 0)


def with_timeout(timeout):
    def decorator(decorated):
        @functools.wraps(decorated)
        def inner(*args, **kwargs):
            pool = multiprocessing.pool.ThreadPool(1)
            async_result = pool.apply_async(decorated, args, kwargs)
            try:
                return async_result.get(timeout)
            except multiprocessing.TimeoutError:
                return

        return inner

    return decorator


def tridata(distance, doubleplane, energy, erel, nmax, physics):
    # Get filesnames, then read each file with pandas and concat into one large dataframe
    files = [
        filename_for(distance, doubleplane, energy, erel, n, physics, s, "trifeature.parquet")
        for n in range(1, nmax + 1)
        for s in range(20)
    ]
    dfs = [pd.read_parquet(file) for file in files]
    data = pd.concat(dfs, ignore_index=True).sample(frac=1)

    # Normalize: If there are no hits, there isn't anything to reconstruct.
    # Can happen if the neutrons just fly through the detector
    data.loc[data["nHits"] == 0, ["nPP", "nPH"]] = 0

    # Split into Train and Test dataset.
    # Ensure presence of one zero-case in both sets
    msk = np.random.rand(len(data)) < 0.8
    msk[0] = True
    msk[1] = False
    data.loc[0] = data.loc[1] = [0, 0, 0, 0, 0, 0]

    traindata = data[msk]
    testdata = data[~msk]

    return traindata, testdata
