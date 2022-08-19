from .base import Classifier


class SameSumTxnsClassifier(Classifier):
    def __init__(self, min_sum=10):
        super().__init__()
        self.storage = {}
        self.min_sum = min_sum

    def process(self, contract_address, hash_, txn, receipt, rest):
        contract_address = contract_address.lower()
        func_hash = txn["input"][:10]
        account = txn["from"].lower()

        if contract_address not in self.storage:
            self.storage[contract_address] = {
                "deposit": {},
                "withdraw": {},
            }

        if func_hash == "0x21a0adb6":   # withdraw
            if account not in self.storage[contract_address]["withdraw"]:
                self.storage[contract_address]["withdraw"][account] = 0
            self.storage[contract_address]["withdraw"][account] += 1
        elif func_hash == "0xb214faa5":     # deposit
            if account not in self.storage[contract_address]["deposit"]:
                self.storage[contract_address]["deposit"][account] = 0
            self.storage[contract_address]["deposit"][account] += 1

    def classify(self, address):
        address = address.lower()

        ret = []

        for contract_address, data in self.storage.items():
            num_deposit = data["deposit"][address] if address in data["deposit"] else 0
            num_withdraw = data["withdraw"][address] if address in data["withdraw"] else 0
            if num_deposit == num_withdraw:
                continue

            if num_deposit > num_deposit:
                if num_deposit < self.min_sum:
                    continue

                for withdraw_address, num_withdraw in data["withdraw"].items():
                    if withdraw_address == address:
                        continue
                    if withdraw_address in ret:
                        continue

                    if num_withdraw == num_deposit:
                        ret.append(withdraw_address)

            if num_withdraw > num_deposit:
                if num_withdraw < self.min_sum:
                    continue
                for deposit_address, num_deposit in data["deposit"].items():
                    if deposit_address == address:
                        continue
                    if deposit_address in ret:
                        continue

                    if num_withdraw == num_deposit:
                        ret.append(deposit_address)

        return ret
