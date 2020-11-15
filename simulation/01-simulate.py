import joblib
from simulation import simulation


distances = [15]
doubleplanes = [12, 30]
energies = [600]
erels = [500]
neutrons = [1, 2, 3, 4, 5, 6]
physicss = ["inclxx"]
subruns = range(20)


# Parallel simulations
joblib.Parallel(n_jobs=-1, backend="loky", verbose=11)(
    joblib.delayed(simulation)(
        distance=distance,
        doubleplane=doubleplane,
        energy=energy,
        erel=erel,
        neutron=neutron,
        physics=physics,
        subrun=subrun)
    for distance in distances
    for energy in energies
    for doubleplane in doubleplanes
    for neutron in neutrons
    for erel in erels
    for physics in physicss
    for subrun in subruns
)
