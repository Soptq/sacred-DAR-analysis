from config import ETHERSCAN_API_KEY
import requests


def get_transactions_by_etherscan(address):
    url = f"https://api-kovan.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=10000&sort=asc&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    return response.json()["result"]