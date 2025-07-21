import logging
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    filters, ConversationHandler, CallbackQueryHandler
)
import psycopg2
import config
import requests

# ===== LOGGING =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== DATABASE =====
conn = psycopg2.connect(config.POSTGRES_URI)
cur = conn.cursor()

# ===== WALLET ROTATION =====
wallets = {
    "USDT": [
        "TE8xvoVcW2hGtZVpLDGkuSqcE86hAMDxtb",
        "TYWXMr4aR8c8ZqXtcPGcjG6AHL2nEP8Avw",
        "TSVugiw9hLwsutXL1x35o56Joe5vk7xHPL",
        "TRTd6uUcBq93Uq32qJBCDZqvz6XyYH5nNo",
        "TQpEGuWJ3UTXXTVZ9jKp38Lrv1FoeKDz7J"
    ],
    "BTC": [
        "bc1q5qul3hvx0826qdn7lcw9lx6ttudhnmuhxj30wu4v3zlhmcm2yrgq78cyr7",
        "1A27g5qNxaFtw3oe4yvuqqPRohD3U4CUFY",
        "1MKhTQTbo7fP25BhRz9Sff3YJe1mFvZUYC",
        "bc1qgzewtna0f257xsyyq4qqq2cdq6cd458gs4uxvw",
        "bc1q6jxdeekzyr83v4awwee897whad97757kwzfl8d"
    ],
    "LTC": [
        "LgSdUeLztFxboLBhzWzLMbLsbePRnzPpXy",
        "ltc1qxpj6tqzp333ajemwlmufq5gr59wszqxz2hzv5shfsd5fh8g9mlvqk5kz58",
        "ltc1qgmssgawydpms6snglf9cvu40p4ed8r6gp8yn2n",
        "LcPd8DD9dbzT2sCnhZY7nxAwJs6WkGA8DJ",
        "ltc1q3kw7adr22pxgl3afd7tjhexhfaf4hltp5je4vc"
    ],
    "ETH": [
        "0xec5405877320d40ea07cc1952817f15ac560cfbd",
        "0x501986b6cc2328858aa8fe20d209438d2eb1dde5",
        "0x476ec054f39062c34ba5e678667f0de3068dd260",
        "0xc94510812dAe070843E2E2eAcC43C9553D17D9cA",
        "0x0c74Aa70c3Cca2770C195617582c17f34baCe509"
    ]
}
rotation_index = {"USDT": 0, "BTC": 0, "LTC": 0, "ETH": 0}

# ===== START COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *CoinHold Escrow Bot*\n"
        "Welcome! Use /buyer or /seller to start a deal.\n"
        "🌍 Use /language to change your language.\n"
        "💸 Earn by referring others: /referral",
        parse_mode="Markdown"
    )

# ===== BUYER COMMAND =====
async def buyer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Rotate wallet
    coin = "BTC"
    idx = rotation_index[coin]
    wallet = wallets[coin][idx]
    rotation_index[coin] = (idx + 1) % len(wallets[coin])
    await update.message.reply_text(
        f"🛒 *Buyer Role Activated*\n"
        f"Your deposit wallet: `{wallet}`\n\n"
        f"Send funds and wait for confirmation.",
        parse_mode="Markdown"
    )
    # Notify admin
    await context.bot.send_message(chat_id=config.ADMIN_ID,
                                   text=f"👤 Buyer {user.username} activated. Wallet: {wallet}")

# ===== SELLER COMMAND =====
async def seller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    coin = "BTC"
    idx = rotation_index[coin]
    wallet = wallets[coin][idx]
    rotation_index[coin] = (idx + 1) % len(wallets[coin])
    await update.message.reply_text(
        f"💰 *Seller Role Activated*\n"
        f"Your escrow wallet: `{wallet}`",
        parse_mode="Markdown"
    )
    await context.bot.send_message(chat_id=config.ADMIN_ID,
                                   text=f"👤 Seller {user.username} activated. Wallet: {wallet}")

# ===== VERIFY =====
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Transaction verified successfully!")

# ===== DISPUTE =====
async def dispute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot.send_message(chat_id=config.ADMIN_ID,
                                   text=f"⚠️ DISPUTE raised by @{user.username}")
    await update.message.reply_text("⚖️ Your dispute has been sent to admin. They will review it soon.")

# ===== REFERRAL =====
async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referral_link = f"https://t.me/{context.bot.username}?start={user.id}"
    await update.message.reply_text(
        f"🔗 Your referral link: {referral_link}\n"
        f"Invite friends and earn rewards!"
    )

# ===== RATING =====
async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⭐ Please rate your last deal (feature enabled only after a complete deal).")

# ===== HISTORY =====
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📜 Your past transactions will appear here.")

# ===== STATS =====
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 Analytics and stats coming soon!")

# ===== LANGUAGE =====
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en'),
         InlineKeyboardButton("🇫🇷 French", callback_data='lang_fr')],
        [InlineKeyboardButton("🇩🇪 German", callback_data='lang_de'),
         InlineKeyboardButton("🇹🇷 Turkish", callback_data='lang_tr')],
        [InlineKeyboardButton("🇮🇳 Hindi", callback_data='lang_in'),
         InlineKeyboardButton("🇪🇸 Spanish", callback_data='lang_es')],
        [InlineKeyboardButton("🇷🇼 Kinyarwanda", callback_data='lang_rw')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌍 Select your language:", reply_markup=reply_markup)

# ===== CALLBACK FOR LANGUAGE =====
async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f"✅ Language set successfully! ({query.data})")

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buyer", buyer))
    app.add_handler(CommandHandler("seller", seller))
    app.add_handler(CommandHandler("verify", verify))
    app.add_handler(CommandHandler("dispute", dispute))
    app.add_handler(CommandHandler("referral", referral))
    app.add_handler(CommandHandler("rating", rating))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("language", language))
    app.add_handler(CallbackQueryHandler(lang_callback))

    app.run_polling()

if __name__ == "__main__":
    main()
