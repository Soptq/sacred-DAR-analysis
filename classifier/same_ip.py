from .base import Classifier


class SameIPClassifier(Classifier):
    def __init__(self):
        super().__init__()
        self.storage = {}

    def process(self, contract_address, hash_, txn, receipt, rest):
        if type(rest) != dict or "ip" not in rest or rest["ip"] is None:
            return

        client_ip = rest["ip"]

        contract_address = contract_address.lower()
        func_hash = txn["input"][:10]
        account = txn["from"].lower()

        if contract_address not in self.storage:
            self.storage[contract_address] = {
                "deposit": {},
                "withdraw": {},
            }

        if func_hash == "0x21a0adb6":  # withdraw
            self.storage[contract_address]["withdraw"][account] = client_ip
        elif func_hash == "0xb214faa5":  # deposit
            self.storage[contract_address]["deposit"][account] = client_ip

    def classify(self, address):
        address = address.lower()

        ret = []

        for contract_address, data in self.storage.items():
            deposit_ip = data["deposit"][address] if address in data["deposit"] else None
            withdraw_address_with_the_same_ip = [address for address, ip in data["deposit"] if ip == deposit_ip]

            withdraw_ip = data["withdraw"][address] if address in data["withdraw"] else None
            deposit_address_with_the_same_ip = [address for address, ip in data["withdraw"] if ip == withdraw_ip]

            ret.extend(withdraw_address_with_the_same_ip)
            ret.extend(deposit_address_with_the_same_ip)

        return ret
