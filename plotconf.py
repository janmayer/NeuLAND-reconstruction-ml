import logging
import matplotlib as mpl
import palettable

logging.getLogger("matplotlib").setLevel(logging.WARNING)

mpl.use("pgf")

# https://matplotlib.org/users/customizing.html
mpl.rcParams.update({
    "pgf.texsystem": "lualatex",
    "pgf.preamble": "\n".join([
        r"\usepackage{fontspec, unicode-math, isotope}",
        r"\setmainfont{Libertinus Serif}",
        r"\setsansfont{Libertinus Sans}",
        r"\setmonofont[Scale=MatchLowercase]{Source Code Pro}",
        r"\setmathfont{Libertinus Math}",
        r"\renewcommand{\familydefault}{\sfdefault}"
    ]),
    "text.usetex": True,
    "font.size": 20,
    "font.family": "sans",
    "font.serif": "Libertinus Serif",
    "font.sans-serif": "Libertinus Sans",
    "font.monospace": "Source Code Pro",
    "axes.spines.left": True,
    "axes.spines.bottom": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.fancybox": False,
    "legend.edgecolor": "#FFFFFF",
    "xtick.top": False,
    "xtick.minor.visible": True,
    "ytick.right": False,
    "ytick.minor.visible": True,
})

import matplotlib.pyplot as plt
import seaborn as sns