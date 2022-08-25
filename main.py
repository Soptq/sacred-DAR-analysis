from typing import Union
import os
import pickle

import config
from tqdm import tqdm
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from web3 import Web3

from classifier import ManualGasPriceClassifier, BlocknumIntervalClassifier, SameSumTxnsClassifier, SameIPClassifier
from utils import get_transactions_by_etherscan
from config import INTERACTED_WITH_BLACKLIST

print("Connecting to Ethereum node...")
w3 = Web3(Web3.HTTPProvider(f'https://kovan.infura.io/v3/{config.INFURA_KEY}'))
print("Connected!")

def load_dataset():
    if not os.path.exists(os.path.join(config.DATASET_PATH, "dataset.pickle")):
        print("No dataset.pickle found. You might need to run `dataset_union.py first`. Exiting...")
        exit(0)

    with open(os.path.join(config.DATASET_PATH, "dataset.pickle"), "rb") as f:
        return pickle.load(f)


def init_classifiers():
    return [
        ManualGasPriceClassifier(threshold=10),
        BlocknumIntervalClassifier(),
        SameSumTxnsClassifier(),
        SameIPClassifier(),
    ]


classifiers = init_classifiers()

print("Loading transactions...")
dataset = load_dataset()
print("Loaded...")

for contract_address, transactions in dataset.items():
    for transaction_hash, data in tqdm(transactions.items()):
        for classifier in classifiers:
            classifier.process(contract_address, transaction_hash, data["txn"], data["receipt"], None)

app = FastAPI()


@app.get("/")
def index():
    html_content = """
        <html>
            <head>
                <title>Sacred DAR(Deposit Address Reuse) Analysis</title>
            </head>
            <body>
                <h1>Sacred DAR(Deposit Address Reuse) Analysis</h1>
                <p>This page will tell you addresses that is considered to be related with the address you input. The data source is Sacred Finance kovan testnet</p>
                <p>It currently contains 5 basic rules, including 1. manually set gas price 2. small interval between deposit and withdraw 3. applies the same address for depositing and withdrawing, 4. the same number of deposits and withdraws (e.g. a user deposits 10 times using address A1 and then withdraws 10 times using address B1, then A1 and B1 might be linked) and 5. the same IP address for depositing and withdrawing.</p>
                <strong>Check if the address is eligible to deposit</strong><br/><br/>
                <input type="text" id="check-address" placeholder="Enter a address">
                <button onclick="check_address()">Submit</button><br/>
                <div id="check_result"></div><br/><br/>
                <strong>Add a record to the dataset</strong><br/><br/>
                <input type="text" id="txid" placeholder="Enter a transaction hash">
                <button onclick="add_record()">Submit</button><br/>
                <div id="add_result"></div><br/><br/>
                <strong>Input an address to query</strong><br/><br/>
                <input type="text" id="address" placeholder="Enter an address">
                <button onclick="get_result()">Submit</button><br/><br/><br/>
                <strong>Related addresses</strong><br/><br/>
                <div id="result"></div>
                <script>
                    function check_address() {
                        var address = document.getElementById("check-address").value;
                        var xhr = new XMLHttpRequest();
                        xhr.open("GET", "/check/" + address, true);
                        xhr.send();
                        xhr.onreadystatechange = function() {
                            if (xhr.readyState == 4) {
                                document.getElementById("check_result").innerHTML = xhr.responseText;
                            }
                        }
                    }
                    function add_record() {
                        var txid = document.getElementById("txid").value;
                        var xhr = new XMLHttpRequest();
                        xhr.open("GET", "/log/" + txid, true);
                        xhr.send();
                        xhr.onreadystatechange = function() {
                            if (xhr.readyState == 4) {
                                document.getElementById("add_result").innerHTML = xhr.responseText;
                            }
                        }
                    }
                    function get_result() {
                        var address = document.getElementById("address").value;
                        var xhr = new XMLHttpRequest();
                        xhr.open("GET", "/classify/" + address, true);
                        xhr.send();
                        xhr.onreadystatechange = function() {
                            if (xhr.readyState == 4) {
                                var response = JSON.parse(xhr.responseText);
                                if (response["result"].length == 0) {
                                    document.getElementById("result").innerHTML = "No related addresses found";
                                } else {
                                    document.getElementById("result").innerHTML = response["result"].join("<br/>");
                                }
                            }
                        }
                    }
                </script>
            </body>
        </html>
        """
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/classify/{address}")
def classify(address: str, q: Union[str, None] = None):
    results = []
    for classifier in classifiers:
        results.extend(classifier.classify(address))
    return {"result": results}


@app.get("/check/{address}")
def check(address: str, q: Union[str, None] = None):
    blacklist = [addr.lower() for addr in INTERACTED_WITH_BLACKLIST]

    history_transactions = get_transactions_by_etherscan(address)
    for transaction in history_transactions:
        if transaction["to"].lower() in blacklist:
            return {"result": "false"}

    return {"result": "true"}


@app.get("/log/{txid}")
def log(txid: str, request: Request):
    print(f"logging {txid}, client IP {request.client.host}")
    txn = w3.eth.getTransaction(txid)
    receipt = w3.eth.getTransactionReceipt(txid)
    contract_address = receipt.to

    if txid not in dataset[contract_address]:
        for classifier in classifiers:
            classifier.process(contract_address, txid, txn, receipt, {"ip": request.client.host})
        return {"result": "ok"}

    return {"result": "duplicated"}
