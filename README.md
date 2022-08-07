# Sacred DAR Analysis

## Get Started
### Install

```
pip install -r requirements.txt
```

### Configuration

```
cp config.py.example config.py
```

and then fill your Infura API key and Etherscan API key to `config.py`.

### Generate Datasets

```
python dataset_union.py
```

This step will pre-fetch all transactions and receipts from the blockchain. Will probably take 10+ hours.

Here is a [generated dataset](https://drive.google.com/file/d/1ZWXeFg_GDjSB7Lw3YPsRB60s6pA57C6c/view?usp=sharing), you can download it and put it in the `dataset/kovan` folder.

### Start the server

```
uvicorn main:app --reload
```

## Project Structure

All heuristics are defined in the `classifier` folder, where each rule is inherited from `Classifier` class. After defining, rules must be enabled in `main.py`.

## APIs

```
http://127.0.0.1:8000/classify/{address}
```

This API will return a list containing addresses that are classified to be related with the provided address.
