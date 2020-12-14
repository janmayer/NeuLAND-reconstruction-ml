import os
import sys
import subprocess
import ROOT

sys.path.append("..")
from helpers import filename_for


def reconstruct_impl(distance, doubleplane, energy, erel, neutron, physics, subrun, overwrite=True):
    inpfile = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, "digi.root")
    simfile = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, "simu.root")
    parfile = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, "para.root")
    outfile = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, "recotest.root")

    if not os.path.isfile(inpfile):
        print(f"Input {inpfile} does not exist")
        return

    if os.path.isfile(outfile):
        if overwrite:
            os.remove(outfile)
        else:
            print(f"Output {outfile} exists and overwriting is disabled")
            return

    ROOT.ROOT.EnableThreadSafety()
    ROOT.FairLogger.GetLogger().SetLogVerbosityLevel("LOW")
    ROOT.FairLogger.GetLogger().SetLogScreenLevel("WARNING")

    # I/O
    run = ROOT.FairRunAna()
    ffs = ROOT.FairFileSource(os.fspath(inpfile))
    ffs.AddFriend(os.fspath(simfile))
    run.SetSource(ffs)
    run.SetSink(ROOT.FairRootFileSink(os.fspath(outfile)))

    # Connect Runtime Database and Calorimetric Par file
    rtdb = run.GetRuntimeDb()
    pario = ROOT.FairParRootFileIo(False)
    pario.open(os.fspath(parfile))
    rtdb.setFirstInput(pario)
    rtdb.setOutput(pario)
    rtdb.saveOutput()

    # Cheating Muliplicity
    run.AddTask(ROOT.R3BNeulandMultiplicityCheat("NeulandPrimaryHits", "NeulandMultiplicityCheat"))

    
    # Perfect Reco
    run.AddTask(ROOT.R3BNeulandNeutronsCheat("NeulandMultiplicityCheat", "NeulandPrimaryHits", "NeulandNeutronsCheat"))
    run.AddTask(ROOT.R3BNeulandNeutronReconstructionMon("NeulandNeutronsCheat", "NeulandNeutronReconstructionMonCheat"))

    
    # RValue
    run.AddTask(
        ROOT.R3BNeulandNeutronsRValue(energy, "NeulandMultiplicityCheat", "NeulandClusters", "NeulandNeutronsRValue")
    )
    run.AddTask(
        ROOT.R3BNeulandNeutronReconstructionMon("NeulandNeutronsRValue", "NeulandNeutronReconstructionMonRValue")
    )

    
    # Scikit
    run.AddTask(
        ROOT.R3BNeulandNeutronsScikit(
            "models/15m_30dp_600AMeV_500keV_4n_AdaBoostClassifier.pkl",  # "models/15m_30dp_600AMeV_500keV_4n_RandomForestClassifier.pkl",
            "NeulandMultiplicityCheat",
            "NeulandClusters",
            "NeulandNeutronsScikit",
        )
    )
    run.AddTask(
        ROOT.R3BNeulandNeutronReconstructionMon("NeulandNeutronsScikit", "NeulandNeutronReconstructionMonScikit")
    )

    
    # Keras
    run.AddTask(
        ROOT.R3BNeulandNeutronsKeras(
            "models/keras-100-SM",
            "models/keras-scaler.pkl.gz",
            "NeulandMultiplicityCheat",
            "NeulandClusters",
            "NeulandNeutronsKeras",
        )
    )
    run.AddTask(
        ROOT.R3BNeulandNeutronReconstructionMon("NeulandNeutronsKeras", "NeulandNeutronReconstructionMonKeras")
    )
    
    
    run.Init()
    run.Run(0, 0)


# Ugly hack, as FairRun (FairRunSim, FairRunAna) has some undeleteable, not-quite-singleton behavior.
# As a result, the same process can't be reused after the first run.
# Here, create a fully standalone process that is fully destroyed afterwards.
# TODO: Once/If this is fixed, remove this and rename the impl function
# reconstruct(15, 30, 600, 500, 4, "inclxx", 0)
def reconstruct(distance, doubleplane, energy, erel, neutron, physics, subrun):
    logfile = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, "recotest.log")
    d = [
        "python",
        "reconstruct.py",
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
    distance = int(sys.argv[1])
    doubleplane = int(sys.argv[2])
    energy = int(sys.argv[3])
    erel = int(sys.argv[4])
    neutron = int(sys.argv[5])
    physics = sys.argv[6]
    subrun = int(sys.argv[7])
    overwrite = True
    reconstruct_impl(distance, doubleplane, energy, erel, neutron, physics, subrun, overwrite)
