import sys

import numpy as np
import pandas as pd
import sklearn.preprocessing
import pyarrow as pa
import pyarrow.parquet as pq
from tensorflow.keras.utils import to_categorical, Sequence
from tensorflow.keras.utils import to_categorical

sys.path.append("..")
from helpers import filename_for


class DataGeneratorBarsJITScaling(Sequence):
    def __init__(self, config):
        self.c = config

        self.cols_tri = ["nHits", "nClus", "Edep"]
        self.cols_e = [str(i) for i in range(0, self.c["doubleplane"] * 100 * 2, 2)]
        self.cols_t = [str(i + 1) for i in range(0, self.c["doubleplane"] * 100 * 2, 2)]

        self.labels = []
        self.features = []

        self.scaler_tri = sklearn.preprocessing.MaxAbsScaler()
        self.scaler_e = sklearn.preprocessing.MaxAbsScaler()
        self.scaler_t = sklearn.preprocessing.MaxAbsScaler()

        file = filename_for(
            self.c["distance"],
            self.c["doubleplane"],
            self.c["energy"],
            self.c["erel"],
            self.c["neutrons"][0],
            "inclxx",
            self.c["subruns"][0],
            "bars.parquet",
        )
        data = pd.read_parquet(file)
        rows = len(data.index)
        del data

        self.batches_per_subrun = (rows * len(self.c["neutrons"])) // self.c["batch_size"]
        self.batches_per_cache = self.batches_per_subrun * self.c["subrun_cache_size"]
        self.len = self.batches_per_subrun * len(self.c["subruns"])

        self.cache_subruns = [
            self.c["subruns"][i : i + self.c["subrun_cache_size"]]
            for i in range(0, len(self.c["subruns"]), self.c["subrun_cache_size"])
        ]
        self.current_cache = -1

        print(f"Rows in one file: {rows}")
        print(f"{self.batches_per_subrun} batches per subrun")
        print(f"{self.len} total batches in {self.cache_subruns} caches")

        self.fitscalers()
        self.load(0)

    def __len__(self):
        return self.len

    def __getitem__(self, index):
        cacheid = index // self.batches_per_cache
        i = index % (self.batches_per_cache)
        # print(f"{index} -> c{cacheid}-i{i}")

        if cacheid != self.current_cache:
            self.load(cacheid)

        a = i * self.c["batch_size"]
        b = (i + 1) * self.c["batch_size"]

        x = self.features[a:b]
        y = self.labels[a:b]
        return x, y

    def load(self, cacheid):
        subruns = self.cache_subruns[cacheid]
        print(f"Loading subruns {subruns} for cache {cacheid}")

        files = [
            filename_for(
                self.c["distance"],
                self.c["doubleplane"],
                self.c["energy"],
                self.c["erel"],
                n,
                "inclxx",
                subrun,
                "bars.parquet",
            )
            for n in self.c["neutrons"]
            for subrun in subruns
        ]
        data = pd.concat([pd.read_parquet(file) for file in files], ignore_index=True).sample(frac=1)
        data.loc[data["nHits"] == 0, self.c["label"]] = 0

        self.current_cache = cacheid

        if self.c["mode"] == "bars":
            self.features = np.concatenate(
                (
                    self.scaler_e.transform(data[self.cols_e].values.reshape(-1, 1)).reshape(
                        -1, len(self.cols_e)
                    ),
                    self.scaler_t.transform(data[self.cols_t].values.reshape(-1, 1)).reshape(
                        -1, len(self.cols_t)
                    ),
                ),
                axis=1,
            )
        elif self.c["mode"] == "barstri":
            self.features = np.concatenate(
                (
                    self.scaler_tri.transform(data[self.cols_tri]),
                    self.scaler_e.transform(data[self.cols_e].values.reshape(-1, 1)).reshape(
                        -1, len(self.cols_e)
                    ),
                    self.scaler_t.transform(data[self.cols_t].values.reshape(-1, 1)).reshape(
                        -1, len(self.cols_t)
                    ),
                ),
                axis=1,
            )
        else:
            raise

        self.labels = to_categorical(
            data[[self.c["label"]]].values.ravel(), num_classes=len(self.c["neutrons"]) + 1
        )
        del data

    def fitscalers(self):
        subruns = range(5)  # self.cache_subruns[0]
        files = [
            filename_for(
                self.c["distance"],
                self.c["doubleplane"],
                self.c["energy"],
                self.c["erel"],
                n,
                "inclxx",
                subrun,
                "bars.parquet",
            )
            for n in self.c["neutrons"]
            for subrun in subruns
        ]
        data = pd.concat([pd.read_parquet(file) for file in files], ignore_index=True)
        self.scaler_tri.fit(data[self.cols_tri])
        self.scaler_e.fit(data[self.cols_e].values.reshape(-1, 1))
        self.scaler_t.fit(data[self.cols_t].values.reshape(-1, 1))
        del data


class DataGeneratorBars(Sequence):
    def __init__(self, config):
        self.c = config
        

        self.cols_tri = ["nHits", "nClus", "Edep"]
        self.cols_e = [str(i) for i in range(0, self.c["doubleplane"] * 100 * 2, 2)]
        self.cols_t = [str(i + 1) for i in range(0, self.c["doubleplane"] * 100 * 2, 2)]

        self.labels = []
        self.features = []

        file = filename_for(
            self.c["distance"],
            self.c["doubleplane"],
            self.c["energy"],
            self.c["erel"],
            self.c["neutrons"][0],
            "inclxx",
            self.c["subruns"][0],
            self.c["suffix"],
        )
        data = pd.read_parquet(file)
        rows = len(data.index)
        del data

        self.batches_per_subrun = (rows * len(self.c["neutrons"])) // self.c["batch_size"]
        self.batches_per_cache = self.batches_per_subrun * self.c["subrun_cache_size"]
        self.len = self.batches_per_subrun * len(self.c["subruns"])

        self.cache_subruns = [
            self.c["subruns"][i : i + self.c["subrun_cache_size"]]
            for i in range(0, len(self.c["subruns"]), self.c["subrun_cache_size"])
        ]
        self.current_cache = -1

        print(f"Rows in one file: {rows}")
        print(f"{self.batches_per_subrun} batches per subrun")
        print(f"{self.len} total batches in {self.cache_subruns} caches")

        self.load(0)

    def __len__(self):
        return self.len

    def __getitem__(self, index):
        cacheid = index // self.batches_per_cache
        i = index % (self.batches_per_cache)
        # print(f"{index} -> c{cacheid}-i{i}")

        if cacheid != self.current_cache:
            self.load(cacheid)

        a = i * self.c["batch_size"]
        b = (i + 1) * self.c["batch_size"]

        if self.c["mode"] == "split":
            # TODO: Refactor maybe? list(zip()) == slow? Slice?
            x = [self.features[0][a:b], self.features[1][a:b]]
        else:
            x = self.features[a:b]
        y = self.labels[a:b]
        return x, y

    def load(self, cacheid):
        subruns = self.cache_subruns[cacheid]
        print(f"Loading subruns {subruns} for cache {cacheid}")

        files = [
            filename_for(
                self.c["distance"],
                self.c["doubleplane"],
                self.c["energy"],
                self.c["erel"],
                n,
                "inclxx",
                subrun,
                self.c["suffix"],
            )
            for n in self.c["neutrons"]
            for subrun in subruns
        ]
        data = pd.concat([pd.read_parquet(file) for file in files], ignore_index=True).sample(frac=1)
        data.loc[data["nHits"] == 0, ["nPN", "nPP", "nPH"]] = 0

        self.current_cache = cacheid

        if self.c["mode"] == "bars":
            self.features = data[self.cols_e + self.cols_t].to_numpy()
        elif self.c["mode"] == "barstri":
            self.features = data[self.cols_tri + self.cols_e + self.cols_t].to_numpy()
        elif self.c["mode"] == "split":
            self.features = [data[self.cols_tri].to_numpy(), data[self.cols_e + self.cols_t].to_numpy()]
        elif self.c["mode"] == "tri":
            self.features = data[self.cols_tri].to_numpy()
        else:
            raise

        self.labels = to_categorical(
            data[[self.c["label"]]].values.ravel(), num_classes=len(self.c["neutrons"]) + 1
        )
        del data
