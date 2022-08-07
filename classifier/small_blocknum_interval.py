from .base import Classifier


class SmallBlocknumIntervalClassifier(Classifier):
    def __init__(self, max_interval=6355):
        super().__init__()
        self.storage = {
            "deposit": [],
            "withdraw": [],
        }
        self.max_interval = max_interval

    def process(self, contract_address, hash_, txn, receipt):
        contract_address = contract_address.lower()
        func_hash = txn["input"][:10]
        account = txn["from"].lower()
        block_number = receipt["blockNumber"]

        data = {
            "address": account,
            "contract_address": contract_address,
            "block_number": block_number,
        }

        if func_hash == "0x21a0adb6":   # withdraw
            self.storage["withdraw"].append(data)
        elif func_hash == "0xb214faa5":     # deposit
            self.storage["deposit"].append(data)

    def classify(self, address):
        address = address.lower()

        ret = []

        all_deposits = [d for d in self.storage["deposit"] if d["address"] == address]
        all_withdraws = [w for w in self.storage["withdraw"] if w["address"] == address]
        interacted_contracts = []
        interacted_contracts.extend([d["contract_address"] for d in all_deposits if d["contract_address"] not in interacted_contracts])
        interacted_contracts.extend([w["contract_address"] for w in all_withdraws if w["contract_address"] not in interacted_contracts])
        for interacted_contract in interacted_contracts:
            num_deposits = len([d for d in all_deposits if d["contract_address"] == interacted_contract])
            num_withdraws = len([w for w in all_withdraws if w["contract_address"] == interacted_contract])
            if num_deposits == num_withdraws:
                continue
            if num_deposits > num_withdraws:
                max_blocknum = max([d["block_number"] for d in all_deposits if d["contract_address"] == interacted_contract])
                possible_withdraws = [
                    w["address"] for w in self.storage["withdraw"]
                    if w["contract_address"] == interacted_contract
                       and w["block_number"] - max_blocknum <= self.max_interval
                       and w["address"] != address
                       and w["address"] not in ret
                ]
                ret.extend(possible_withdraws)
            if num_deposits < num_withdraws:
                min_blocknum = min([w["block_number"] for w in all_withdraws if w["contract_address"] == interacted_contract])
                possible_deposits = [
                    d["address"] for d in self.storage["deposit"]
                    if d["contract_address"] == interacted_contract
                       and d["block_number"] - min_blocknum <= self.max_interval
                       and d["address"] != address
                       and d["address"] not in ret
                ]
                ret.extend(possible_deposits)

        return ret
