import os
import sys
import subprocess
import ROOT
sys.path.append("..")
from helpers import filename_for


def digitization_impl(distance, doubleplane, energy, erel, neutron, physics, subrun, overwrite):
    inpfile = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, "simu.root")
    parfile = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, "para.root")
    outfile = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, "digi.root")

    if not inpfile.is_file():
        print(f"Input {inpfile} does not exist")
        return

    if outfile.is_file():
        if overwrite:
            os.remove(outfile)
        else:
            print(f"Output {outfile} exists and overwriting is disabled")
            return

    ROOT.ROOT.EnableThreadSafety()
    ROOT.FairLogger.GetLogger().SetLogVerbosityLevel("LOW")
    ROOT.FairLogger.GetLogger().SetLogScreenLevel("WARNING")

    run = ROOT.FairRunAna()
    run.SetSource(ROOT.FairFileSource(os.fspath(inpfile)))
    run.SetSink(ROOT.FairRootFileSink(os.fspath(outfile)))

    # Connect Runtime Database
    rtdb = run.GetRuntimeDb()
    pario = ROOT.FairParRootFileIo(False)
    pario.open(os.fspath(parfile))
    rtdb.setFirstInput(pario)
    rtdb.setOutput(pario)
    rtdb.saveOutput()

    # Digitize data to hit level and create respective histograms
    run.AddTask(ROOT.R3BNeulandDigitizer())

    # Build clusters and create respective histograms
    run.AddTask(ROOT.R3BNeulandClusterFinder())

    # Find the actual primary interaction points and their clusters
    run.AddTask(ROOT.R3BNeulandPrimaryInteractionFinder())
    run.AddTask(ROOT.R3BNeulandPrimaryClusterFinder())

    # Create spectra
    run.AddTask(ROOT.R3BNeulandMCMon())
    run.AddTask(ROOT.R3BNeulandHitMon())
    run.AddTask(ROOT.R3BNeulandClusterMon("NeulandPrimaryClusters", "NeulandPrimaryClusterMon"))
    run.AddTask(ROOT.R3BNeulandClusterMon())

    run.Init()
    run.Run(0, 0)
    run.TerminateRun()


# Ugly hack, as FairRun (FairRunSim, FairRunAna) has some undeleteable, not-quite-singleton behavior.
# As a result, the same process can't be reused after the first run.
# Here, create a fully standalone process that is fully destroyed afterwards.
# TODO: Once/If this is fixed, remove this and rename the impl function
def digitization(distance, doubleplane, energy, erel, neutron, physics, subrun):
    logfile = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, "digi.log")
    d = [
        "python",
        "digitization.py",
        str(distance),
        str(doubleplane),
        str(energy),
        str(erel),
        str(neutron),
        str(physics),
        str(subrun)
    ]
    with open(logfile, "w") as log:
        subprocess.run(d, stdout=log, stderr=log)


if __name__ == "__main__":
    distance = int(sys.argv[1])  # 15
    doubleplane = int(sys.argv[2])  # 30
    energy = int(sys.argv[3])  # 600
    erel = int(sys.argv[4])  # 100
    neutron = int(sys.argv[5])  # 4
    physics = sys.argv[6]  # "inclxx"
    subrun = int(sys.argv[7])  # 1
    digitization_impl(distance, doubleplane, energy, erel, neutron, physics, subrun, overwrite=True)
