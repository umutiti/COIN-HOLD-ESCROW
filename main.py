import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InputFile
import asyncpg
import aiohttp

# ======== ENVIRONMENT VARIABLES ========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7721248730"))
POSTGRES_URI = os.getenv("POSTGRES_URI")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

if not BOT_TOKEN or not POSTGRES_URI or not ETHERSCAN_API_KEY:
    raise ValueError("❌ Missing environment variables! Set BOT_TOKEN, POSTGRES_URI, and ETHERSCAN_API_KEY.")

# ======== LOGGING ========
logging.basicConfig(level=logging.INFO)

# ======== INIT BOT & DB ========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# global rotating index
wallet_index = {
    "BTC": 0,
    "ETH": 0,
    "USDT": 0,
    "LTC": 0
}

wallets = {
    "BTC": [
        "bc1q5qul3hvx0826qdn7lcw9lx6ttudhnmuhxj30wu4v3zlhmcm2yrgq78cyr7",
        "1A27g5qNxaFtw3oe4yvuqqPRohD3U4CUFY",
        "1MKhTQTbo7fP25BhRz9Sff3YJe1mFvZUYC",
        "bc1qgzewtna0f257xsyyq4qqq2cdq6cd458gs4uxvw",
        "bc1q6jxdeekzyr83v4awwee897whad97757kwzfl8d"
    ],
    "ETH": [
        "0xec5405877320d40ea07cc1952817f15ac560cfbd",
        "0x501986b6cc2328858aa8fe20d209438d2eb1dde5",
        "0x476ec054f39062c34ba5e678667f0de3068dd260",
        "0xc94510812dAe070843E2E2eAcC43C9553D17D9cA",
        "0x0c74Aa70c3Cca2770C195617582c17f34baCe509"
    ],
    "USDT": [
        "TE8xvoVcW2hGtZVpLDGkuSqcE86hAMDxtb",
        "TYWXMr4aR8c8ZqXtcPGcjG6AHL2nEP8Avw",
        "TSVugiw9hLwsutXL1x35o56Joe5vk7xHPL",
        "TRTd6uUcBq93Uq32qJBCDZqvz6XyYH5nNo",
        "TQpEGuWJ3UTXXTVZ9jKp38Lrv1FoeKDz7J"
    ],
    "LTC": [
        "LgSdUeLztFxboLBhzWzLMbLsbePRnzPpXy",
        "ltc1qxpj6tqzp333ajemwlmufq5gr59wszqxz2hzv5shfsd5fh8g9mlvqk5kz58",
        "ltc1qgmssgawydpms6snglf9cvu40p4ed8r6gp8yn2n",
        "LcPd8DD9dbzT2sCnhZY7nxAwJs6WkGA8DJ",
        "ltc1q3kw7adr22pxgl3afd7tjhexhfaf4hltp5je4vc"
    ]
}

async def init_db():
    conn = await asyncpg.connect(POSTGRES_URI)
    # create tables
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions(
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            coin TEXT,
            wallet_address TEXT,
            tx_hash TEXT,
            status TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS disputes(
            id SERIAL PRIMARY KEY,
            tx_id INTEGER REFERENCES transactions(id),
            reason TEXT,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    await conn.close()

# ================== UTILITIES =======================
async def get_next_wallet(coin):
    idx = wallet_index[coin]
    wallet = wallets[coin][idx]
    # rotate
    wallet_index[coin] = (idx + 1) % len(wallets[coin])
    return wallet

async def verify_onchain(tx_hash):
    # Example using Etherscan (ETH) — adjust for other chains if needed
    url = f"https://api.etherscan.io/api?module=transaction&action=gettxreceiptstatus&txhash={tx_hash}&apikey={ETHERSCAN_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            status = data.get("result", {}).get("status")
            return status == "1"

# ================== COMMANDS ========================
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    banner = InputFile("assets/welcome_banner.jpg")
    await bot.send_photo(message.chat.id, banner, caption="👋 Welcome to CoinHold Escrow Bot!\n\nUse /escrow to start a new deal.")

@dp.message_handler(commands=['escrow'])
async def cmd_escrow(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("BTC", "ETH", "USDT", "LTC")
    await message.answer("Select coin for escrow:", reply_markup=kb)

@dp.message_handler(lambda msg: msg.text in ["BTC", "ETH", "USDT", "LTC"])
async def process_coin(message: types.Message):
    coin = message.text
    wallet = await get_next_wallet(coin)
    await message.answer(f"💳 Send {coin} to:\n`{wallet}`\n\nAfter sending, reply with your transaction hash.")
    # store user and waiting state in DB if needed

@dp.message_handler(commands=['verify'])
async def cmd_verify(message: types.Message):
    # assume tx_hash after /verify <hash>
    try:
        tx_hash = message.text.split()[1]
    except:
        await message.reply("❌ Usage: /verify <tx_hash>")
        return

    ok = await verify_onchain(tx_hash)
    if ok:
        await message.reply("✅ Transaction confirmed on-chain!")
        await bot.send_message(ADMIN_ID, f"✅ New confirmed escrow deposit!\nHash: {tx_hash}\nUser: {message.from_user.id}")
    else:
        await message.reply("⏳ Waiting for 1 confirmation…")

@dp.message_handler(commands=['dispute'])
async def cmd_dispute(message: types.Message):
    await message.reply("⚖️ Please describe your dispute. An admin will contact you shortly.")
    await bot.send_message(ADMIN_ID, f"⚠️ Dispute initiated by {message.from_user.id}")

@dp.message_handler(commands=['history'])
async def cmd_history(message: types.Message):
    # fetch from DB
    await message.reply("📜 Transaction history feature under development…")

@dp.message_handler(commands=['stats'])
async def cmd_stats(message: types.Message):
    # fetch aggregated stats
    await message.reply("📊 Stats feature under development…")

# ================== ADMIN PANEL (simplified) =====================
@dp.message_handler(commands=['adminpanel'])
async def cmd_adminpanel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ You are not admin.")
    await message.reply("🔧 Admin Panel:\n/stats\n/history\n(extend as needed)")

# ================== MAIN =====================
async def on_startup(_):
    await init_db()
    logging.info("✅ Bot started and DB initialized")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
