# Delay - задержка между аккаунтами в секундах
MIN_DELAY = 10000
MAX_DELAY = 50000

# Контроль Gwei
GAS_PRICE = 100000

# Сколько отправляем % от баланса
MIN_BALANCE = 0.1   # Например, 10%
MAX_BALANCE = 0.5   # Например, 50%

# RPC чейна отправления
RPC_URL = 'https://rpc.ankr.com/arbitrum'   # Замени на свою rpc чейна отправителя

# CHAIN ID чейна отправления
chainId_sent = 42161  # Укажи chain id, с которого будем отправлять бабки

# Random Chain получателя
RANDOM_RECIVE = True    # True / False

# Если используешь рандомного получателя - True (можешь выбрать используемые чейны)
# Если какой-то чейн не нужен, просто закомментируй его (#)
# Можешь сам добавлять любые чейны

chain_ids = {
    #42161: "ARB",
    10: "OP",
    534352: "SCROLL",
    42170: "ARB_NOVA",
    8453: "BASE",
    1: "ETH",
    1101: "ZKEVM",
    690: "REDSTONE",
    324: "ZKSYNC"
}

# Если используешь конкретного получателя - False (можешь выбрать используемые чейны)
chain_recive = {
    10: "OP"   # Пример замены: 10: "OP"
}

# ОЧЕНЬ ВАЖНО: При началом работы проверь на сайте, работает ли бридж в нужном тебе направлении - https://relay.link/
# ОЧЕНЬ ВАЖНО: При началом работы проверь на сайте, работает ли бридж в нужном тебе направлении - https://relay.link/
# ОЧЕНЬ ВАЖНО: При началом работы проверь на сайте, работает ли бридж в нужном тебе направлении - https://relay.link/