from .base import Classifier


class ManualGasPriceClassifier(Classifier):
    def __init__(self, threshold=6):
        super().__init__()
        self.storage = {}
        self.counter = {}
        self.threshold = threshold

    def process(self, contract_address, hash_, txn, receipt, rest):
        contract_address = contract_address.lower()
        func_hash = txn["input"][:10]
        account = txn["from"].lower()
        gas_price = int(txn["gasPrice"])
        block_number = receipt["blockNumber"]

        if gas_price not in self.storage:
            self.storage[gas_price] = {
                "deposit": [],
                "withdraw": [],
                "count": 0,
            }

        if contract_address not in self.counter:
            self.counter[contract_address] = {}

        if account not in self.counter[contract_address]:
            self.counter[contract_address][account] = 0

        data = {
            "address": account,
            "contract_address": contract_address,
            "block_number": block_number,
        }

        if func_hash == "0x21a0adb6":   # withdraw
            self.storage[gas_price]["withdraw"].append(data)
            self.counter[contract_address][account] += 1
        elif func_hash == "0xb214faa5":     # deposit
            self.storage[gas_price]["deposit"].append(data)
            self.counter[contract_address][account] -= 1
        self.storage[gas_price]["count"] += 1

    def classify(self, address):
        address = address.lower()

        ret = []
        valid_contracts = []
        for contract_addresses, counter_data in self.counter.items():
            if address in counter_data and counter_data[address] == 0:
                continue
            valid_contracts.append(contract_addresses)

        for gas_price, data in self.storage.items():
            deposits, withdraws, count = data["deposit"], data["withdraw"], data["count"]
            deposit_addresses = [d["address"] for d in deposits]
            withdraw_addresses = [w["address"] for w in withdraws]
            if count > self.threshold:
                continue

            if address in deposit_addresses:
                min_block_number = min([d["block_number"] for d in deposits if d["address"] == address])
                contract_addresses = [
                    d["contract_address"] for d in deposits
                    if d["address"] == address and d["contract_address"] in valid_contracts
                ]
                filtered_withdraws = [
                    w["address"] for w in withdraws
                    if w["block_number"] > min_block_number
                       and w["contract_address"] in contract_addresses
                       and w["address"] != address
                       and w["address"] not in ret
                ]
                ret.extend(filtered_withdraws)

            if address in withdraw_addresses:
                max_block_number = max([w["block_number"] for w in withdraws if w["address"] == address])
                contract_addresses = [
                    w["contract_address"] for w in withdraws
                    if w["address"] == address and w["contract_address"] in valid_contracts
                ]
                filtered_deposits = [
                    d["address"] for d in deposits
                    if d["block_number"] < max_block_number
                       and d["contract_address"] in contract_addresses
                       and d["address"] != address
                       and d["address"] not in ret
                ]
                ret.extend(filtered_deposits)
        return ret
