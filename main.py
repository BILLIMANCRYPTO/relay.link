import random
import logging
import requests
import time
from settings import MIN_DELAY, MAX_DELAY, GAS_PRICE, MIN_BALANCE, MAX_BALANCE, RPC_URL, chainId_sent, chain_ids, RANDOM_RECIVE, chain_recive
from datetime import datetime
from web3 import Web3
from eth_account import Account
from colorama import init, Fore

# Инициализация Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Загрузка приватных ключей из файла
with open('keys.txt', 'r') as file:
    private_keys = [line.strip() for line in file]

# Генерация кошельков из приватных ключей
wallets = [Account.from_key(private_key).address for private_key in private_keys]


# Переменная для использования случайного выбора цепочки
use_random_chain = RANDOM_RECIVE

# Функция для получения текущей цены газа через RPC
def get_current_gas_price():
    ankr_web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
    return ankr_web3.eth.gas_price

# Функция для проверки и ожидания снижения цены газа
def wait_for_gas_price_below(threshold_gwei):
    while True:
        gas_price = get_current_gas_price()
        gas_price_gwei = Web3.from_wei(gas_price, 'gwei')
        if gas_price_gwei <= threshold_gwei:
            break
        print(f'{gas_price_gwei:.2f} GWEI > {threshold_gwei} GWEI')
        time.sleep(60)  # Подождать 60 секунд перед следующей проверкой

# Функция для отправки запроса и выполнения транзакции
def redstone_bridge(wallet_address, private_key, web3, i):
    balance = web3.eth.get_balance(wallet_address)
    if balance <= 0:
        logging.error(f"Insufficient balance in wallet {wallet_address}")
        return None

    # Вычисление суммы в диапазоне от MIN_BALANCE до MAX_BALANCE баланса
    min_amount = balance * MIN_BALANCE
    max_amount = balance * MAX_BALANCE
    amount = random.uniform(min_amount, max_amount)
    amount_str = str(int(amount))  # Преобразование суммы в целое число и строку

    # Выбор destinationChainId и его названия
    if use_random_chain:
        destination_chain_id, chain_name = random.choice(list(chain_ids.items()))
    else:
        destination_chain_id, chain_name = next(iter(chain_recive.items()))  # Использовать первую цепочку в списке

    url = "https://api.relay.link/execute/bridge"
    payload = {
        "user": wallet_address,
        "recipient": wallet_address,
        "originChainId": chainId_sent,
        "destinationChainId": destination_chain_id,
        "currency": "eth",
        "amount": amount_str,
        "source": "relay.link",
        "useForwarder": False,
        "usePermit": False,
        "useExternalLiquidity": False
    }

    headers = {'Content-Type': 'application/json'}

    # Максимальное количество попыток
    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                data = response_data["steps"][0]["items"][0]["data"]
                to_address = web3.to_checksum_address(data["to"])
                value = int(data["value"])
                gas_price = get_current_gas_price()
                gas_limit = web3.eth.estimate_gas({
                    'from': wallet_address,
                    'to': to_address,
                    'value': value,
                    'data': data["data"]
                })

                # Проверка цены газа и ожидание, если она выше порогового значения
                wait_for_gas_price_below(GAS_PRICE)

                # Получение текущей даты и времени
                current_time = datetime.now()

                print(
                    f'{current_time.date()} {current_time.time()} | [{i}/{len(wallets)}] | {wallet_address} | Module: Relay | SENT {web3.from_wei(value, "ether")} to {chain_name}')

                try:
                    tx_params = {
                        'nonce': web3.eth.get_transaction_count(wallet_address),
                        'gasPrice': gas_price,
                        'gas': gas_limit,
                        'to': to_address,
                        'value': value,
                        'data': data["data"],
                        'chainId': chainId_sent,  # ID сети ETH
                    }

                    signed_tx = web3.eth.account.sign_transaction(tx_params, private_key)
                    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

                    # Ожидание подтверждения транзакции
                    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                    if tx_receipt.status == 1:
                        # Получение текущего баланса эфира на кошельке
                        balance_after_tx = web3.eth.get_balance(wallet_address)

                        print(
                            f'{current_time.date()} {current_time.time()} | [{i}/{len(wallets)}] | {wallet_address} | Relay TX INFO | Wallet Balance: {web3.from_wei(balance_after_tx, "ether")} ETH')

                        print(
                            f'{current_time.date()} {current_time.time()} | [{i}/{len(wallets)}] | {wallet_address} | {tx_hash.hex()}')
                    else:
                        print(
                            f'{current_time.date()} {current_time.time()} | [{i}/{len(wallets)}] | {wallet_address} | {tx_hash.hex()} - Failed')

                    return tx_hash.hex()

                except ValueError as e:
                    if 'insufficient funds' in str(e):
                        logging.error(f'Insufficient funds for gas * price + value: {wallet_address}')
                        break
                    logging.error(f'Error occurred for wallet {wallet_address}: {e}')
                    logging.exception("Exception occurred", exc_info=True)
                    return None

            else:
                logging.error(f"Failed to fetch data from API: {response.text}")
                if response.status_code == 504:
                    logging.info(f"Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(2 ** attempt)  # Экспоненциальное увеличение времени ожидания
                    continue
                return None
        except requests.RequestException as e:
            logging.error(f"Request exception: {e}")
            return None
        except ValueError as e:
            if 'insufficient funds' in str(e):
                logging.error(f'Insufficient funds for gas * price + value: {wallet_address}')
                break
            logging.error(f'Error occurred for wallet {wallet_address}: {e}')
            logging.exception("Exception occurred", exc_info=True)
            return None

# Пример использования функции для всех кошельков
gas_price_threshold_gwei = GAS_PRICE
for i, (wallet_address, private_key) in enumerate(zip(wallets, private_keys), start=1):
    try:
        redstone_bridge(wallet_address, private_key, web3, i)
    except ValueError as e:
        if 'insufficient funds' in str(e):
            logging.error(f'Skipping wallet {wallet_address} due to insufficient funds.')
        else:
            raise e
    delay = random.randint(MIN_DELAY, MAX_DELAY)
    current_time = datetime.now()
    print(
        f'{current_time.date()} {current_time.time()} | [{i}/{len(wallets)}] | {wallet_address} | Wait {delay} seconds')
    time.sleep(delay)
