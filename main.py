from typing import Union
import os
import pickle

import config
from tqdm import tqdm
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from classifier import ManualGasPriceClassifier, BlocknumIntervalClassifier, SameSumTxnsClassifier


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
    ]


classifiers = init_classifiers()

print("Loading transactions...")
dataset = load_dataset()
print("Loaded...")

for contract_address, transactions in dataset.items():
    for transaction_hash, data in tqdm(transactions.items()):
        for classifier in classifiers:
            classifier.process(contract_address, transaction_hash, data["txn"], data["receipt"])

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
                <p>It currently contains 4 basic rules, including 1. manually set gas price 2. small interval between deposit and withdraw 3. applies the same address for depositing and withdrawing and 4. the same number of deposits and withdraws (e.g. a user deposits 10 times using address A1 and then withdraws 10 times using address B1, then A1 and B1 might be linked).</p>
                <strong>Input an address to query</strong><br/><br/>
                <input type="text" id="address" placeholder="Enter an address">
                <button onclick="get_result()">Submit</button><br/><br/><br/>
                <strong>Related addresses</strong><br/><br/>
                <div id="result"></div>
                <script>
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
