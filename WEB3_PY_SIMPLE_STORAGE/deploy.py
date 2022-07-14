import json
from web3 import Web3
import os
from dotenv import load_dotenv
from solcx import compile_standard, install_solc

install_solc("0.6.0")

load_dotenv()

with open("./SimpleStorage.sol", "r") as file:
    simple_storage_file = file.read()


compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"SimpleStorage.sol": {"content": simple_storage_file}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.6.0",
)

with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)

# get bytecode
bytecode = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["evm"][
    "bytecode"
]["object"]

# get abi
abi = json.loads(
    compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["metadata"]
)["output"]["abi"]

w3 = Web3(
    Web3.HTTPProvider("https://rinkeby.infura.io/v3/40aa2943f090452b89381305547942a2")
)
chain_id = 4
my_address = "0x3DDaB58B218460Db7aE3D0450c05915581Bd86Cf"
private_key = os.getenv("PRIVATE_KEY")

SimpleStorage = w3.eth.contract(abi=abi, bytecode=bytecode)

nonce = w3.eth.getTransactionCount(my_address)


# 1. Criando a transação

transaction = SimpleStorage.constructor().buildTransaction(
    {
        "gasPrice": w3.eth.gas_price,
        "chainId": chain_id,
        "from": my_address,
        "nonce": nonce,
    }
)

# 2. Assinando a transação
signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
print("Implantando contrato!")

# 2. Enviando a transação
tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

print(tx_hash)

print("Esperando a transação terminar...")
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Prontinho! Contrato implantado em: {tx_receipt.contractAddress}")

# Trabalhando com contratos implantados
simple_storage = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
print(f"Valor inicial {simple_storage.functions.retrieve().call()}")
greeting_transaction = simple_storage.functions.store(15).buildTransaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce + 1,
    }
)
signed_greeting_txn = w3.eth.account.sign_transaction(
    greeting_transaction, private_key=private_key
)
tx_greeting_hash = w3.eth.send_raw_transaction(signed_greeting_txn.rawTransaction)
print("Atualizando o valor armazenado...")
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_greeting_hash)

print(simple_storage.functions.retrieve().call())
