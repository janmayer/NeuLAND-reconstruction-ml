import pathlib
import os

try:
    import ROOT

    ROOT.ROOT.EnableThreadSafety()
except:
    pass


def filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, what):
    path = pathlib.Path(__file__).parent.absolute().joinpath("data")
    name = f"{distance}m_{doubleplane}dp_{energy}AMeV_{erel}keV_{neutron}n.{physics}.{subrun:02d}.{what}"
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
