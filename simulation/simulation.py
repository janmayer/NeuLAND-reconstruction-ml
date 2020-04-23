import os
import sys
import subprocess
import random
import ROOT
sys.path.append("..")
from helpers import filename_for


def simulation_impl(distance, doubleplane, energy, erel, neutron, physics, subrun, overwrite):
    outfile = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, "simu.root")
    parfile = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, "para.root")

    if not overwrite and outfile.is_file():
        print(f"Output {outfile} exists and overwriting is disabled")
        return

    ROOT.ROOT.EnableThreadSafety()
    ROOT.FairLogger.GetLogger().SetLogVerbosityLevel("LOW")
    ROOT.FairLogger.GetLogger().SetLogScreenLevel("WARNING")

    vmcworkdir = os.environ["VMCWORKDIR"]
    os.environ["GEOMPATH"] = vmcworkdir + "/geometry"
    os.environ["CONFIG_DIR"] = vmcworkdir + "/gconfig"
    os.environ["PHYSICSLIST"] = f"QGSP_{physics.upper()}_HP"

    # Initialize Simulation
    run = ROOT.FairRunSim()
    run.SetName("TGeant4")
    run.SetStoreTraj(False)
    run.SetMaterials("media_r3b.geo")

    # Output
    run.SetSink(ROOT.FairRootFileSink(os.fspath(outfile)))

    # Primary Generator
    generator = ROOT.FairPrimaryGenerator()
    psg = ROOT.R3BPhaseSpaceGenerator()
    psg.SetBeamEnergyDistribution_AMeV(ROOT.R3BDistribution1D.Delta(energy))
    psg.SetErelDistribution_keV(ROOT.R3BDistribution1D.Delta(erel))
    psg.AddHeavyIon(50, 132 - neutron)
    for n in range(neutron):
        psg.AddParticle(2112)
    generator.AddGenerator(psg)
    run.SetGenerator(generator)

    # Geometry
    cave = ROOT.R3BCave("Cave")
    cave.SetGeometryFileName("r3b_cave_vacuum.geo")
    run.AddModule(cave)

    run.AddModule(ROOT.R3BNeutronWindowAndSomeAir(700, distance * 100))

    neuland_position = ROOT.TGeoTranslation(0.0, 0.0, distance * 100 + doubleplane * 10.0 / 2.0)
    neuland = ROOT.R3BNeuland(doubleplane, neuland_position)
    run.AddModule(neuland)

    magnetic_field = ROOT.R3BGladFieldMap("R3BGladMap")
    magnetic_field.SetScale(-0.6)
    run.SetField(magnetic_field)

    # Prepare to run
    run.Init()
    ROOT.TVirtualMC.GetMC().SetRandom(ROOT.TRandom3(random.randint(0, 10000)))
    ROOT.TVirtualMC.GetMC().SetMaxNStep(100000)

    # Runtime Database
    rtdb = run.GetRuntimeDb()
    parout = ROOT.FairParRootFileIo(True)
    parout.open(os.fspath(parfile))
    rtdb.setOutput(parout)
    rtdb.saveOutput()

    # Run
    run.Run(10000)


# Ugly hack, as FairRun (FairRunSim, FairRunAna) has some undeleteable, not-quite-singleton behavior.
# As a result, the same process can't be reused after the first run.
# Here, create a fully standalone process that is fully destroyed afterwards.
# TODO: Once/If this is fixed, remove this and rename the impl function
def simulation(distance, doubleplane, energy, erel, neutron, physics, subrun):
    logfile = filename_for(distance, doubleplane, energy, erel, neutron, physics, subrun, "simu.log")
    d = [
        "python",
        "simulation.py",
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
    simulation_impl(distance, doubleplane, energy, erel, neutron, physics, subrun, overwrite=False)
