from typing import Union
import os
import pickle

import config
from tqdm import tqdm
from fastapi import FastAPI

from classifier import ManualGasPriceClassifier, SmallBlocknumIntervalClassifier, SameSumTxnsClassifier


def load_dataset():
    if not os.path.exists(os.path.join(config.DATASET_PATH, "dataset.pickle")):
        print("No dataset.pickle found. You might need to run `dataset_union.py first`. Exiting...")
        exit(0)

    with open(os.path.join(config.DATASET_PATH, "dataset.pickle"), "rb") as f:
        return pickle.load(f)


def init_classifiers():
    return [
        ManualGasPriceClassifier(threshold=10),
        SmallBlocknumIntervalClassifier(),
        SameSumTxnsClassifier(),
    ]


classifiers = init_classifiers()

print("Loading transactions...")
dataset = load_dataset()
print("Loaded...")

for contract_address, transactions in dataset.items():
    if contract_address != "0xf43D169bd8feCc36344a08669620FB29490E677c":
        continue
    for transaction_hash, data in tqdm(transactions.items()):
        for classifier in classifiers:
            classifier.process(contract_address, transaction_hash, data["txn"], data["receipt"])

app = FastAPI()


@app.get("/classify/{address}")
def classify(address: str, q: Union[str, None] = None):
    results = []
    for classifier in classifiers:
        results.extend(classifier.classify(address))
    return {"result": results}
