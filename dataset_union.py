import os
import csv
import pickle

from web3 import Web3
from tqdm import tqdm

import config

print("Connecting to Ethereum node...")
w3 = Web3(Web3.HTTPProvider(f'https://kovan.infura.io/v3/{config.INFURA_KEY}'))
print("Connected!")

allTransactions = {}

for filename in os.listdir(config.DATASET_PATH):
    if filename.endswith(".csv"):
        contract_address = filename.split(".")[0].split("-")[1]
        if contract_address not in allTransactions:
            allTransactions[contract_address] = set()

        with open(os.path.join(config.DATASET_PATH, filename), "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row[0].startswith("0x"):
                    continue
                allTransactions[contract_address].add(row[0])
    else:
        continue

dataset = {}
try:
    for contract_address, transactions in allTransactions.items():
        print(f"Fetching metadatas for transactions in contract {contract_address}...")
        if contract_address not in dataset:
            dataset[contract_address] = {}
        for transaction in tqdm(transactions):
            if transaction not in dataset[contract_address]:
                dataset[contract_address][transaction] = {
                    "txn": w3.eth.getTransaction(transaction),
                    "receipt": w3.eth.getTransactionReceipt(transaction),
                }
except Exception as e:
    print(e)
    print("Error fetching metadata. Saving current dataset...")

with open("dataset/kovan/dataset.pickle", "wb") as f:
    pickle.dump(dataset, f)

