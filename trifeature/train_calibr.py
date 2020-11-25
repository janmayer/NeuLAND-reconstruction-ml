import os
import sys
import subprocess
import ROOT

sys.path.append("..")
from helpers import filename_for


def train_impl(doubleplane, energy, nmax, physics, overwrite, label):
    outfile = f"models/{doubleplane}dp_{energy}AMeV_{nmax}n_{label}.train.root"
    parfile = f"models/{doubleplane}dp_{energy}AMeV_{nmax}n_{label}.ncut.root"

    if os.path.isfile(outfile):
        if overwrite:
            os.remove(outfile)
        else:
            print(f"Output {outfile} exists and overwriting is disabled")
            return

    if os.path.isfile(parfile):
        if overwrite:
            os.remove(parfile)
        else:
            print(f"Output {parfile} exists and overwriting is disabled")
            return        

    files = [
        filename_for(15, doubleplane, energy, 500, neutron, physics, subrun, "digi.root")
        for neutron in range(1, nmax + 1)
        for subrun in range(20)
    ]
    files = [os.fspath(file) for file in files if os.path.isfile(file)]
            
    ROOT.ROOT.EnableThreadSafety()
    ROOT.FairLogger.GetLogger().SetLogVerbosityLevel("LOW")
    ROOT.FairLogger.GetLogger().SetLogScreenLevel("INFO")

    run = ROOT.FairRunAna()
    ffs = ROOT.FairFileSource(files[0])
    for file in files[1:]:
        ffs.AddFile(file)
    run.SetSource(ffs)
    run.SetSink(ROOT.FairRootFileSink(outfile))

    # Connect Runtime Database
    rtdb = run.GetRuntimeDb()
    paro = ROOT.FairParRootFileIo(True)
    paro.open(os.fspath(parfile))
    rtdb.setOutput(paro)

    # Train tasks
    trn = ROOT.R3BNeulandMultiplicityCalorimetricTrain("NeulandClusters", "NeulandPrimaryTracks")
    use_hits = True if label is "nPH" else False
    trn.SetUseHits(use_hits)
    trn.SetEdepOpt(energy, 25, energy * 0.25, energy * 1.75)
    # trn.SetWeight(0.5)
    run.AddTask(trn)
    
    run.AddTask(ROOT.R3BNeulandMultiplicityBayesTrain("NeulandClusters", "NeulandPrimaryTracks"))

    run.Init()
    run.Run(0, 0)
    rtdb.writeContainers()
    rtdb.writeVersions()    
    rtdb.saveOutput()
    rtdb.print()
    rtdb.closeOutput()


# Ugly hack, as FairRun (FairRunSim, FairRunAna) has some undeleteable, not-quite-singleton behavior.
# As a result, the same process can't be reused after the first run.
# Here, create a fully standalone process that is fully destroyed afterwards.
# TODO: Once/If this is fixed, remove this and rename the impl function
def train(doubleplane, energy, nmax, physics, label):
    logfile = f"models/{doubleplane}dp_{energy}AMeV_{nmax}n_{label}.train.log"
    d = [
        "python",
        "train_calibr.py",
        str(doubleplane),
        str(energy),
        str(nmax),
        str(physics),
        str(label)
    ]
    with open(logfile, "w") as log:
        subprocess.run(d, stdout=log, stderr=log)


if __name__ == "__main__":
    doubleplane = int(sys.argv[1])
    energy = int(sys.argv[2])
    nmax = int(sys.argv[3])
    physics = sys.argv[4]
    label = sys.argv[5]
    overwrite = True
    train_impl(doubleplane, energy, nmax, physics, overwrite, label)
