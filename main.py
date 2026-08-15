import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("telegramarchive")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID_RAW = os.getenv("ADMIN_CHAT_ID", "").strip()
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required")
if not ADMIN_CHAT_ID_RAW:
    raise RuntimeError("ADMIN_CHAT_ID environment variable is required")

try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID_RAW)
except ValueError as exc:
    raise RuntimeError("ADMIN_CHAT_ID must be a numeric Telegram chat ID") from exc


def parse_admin_ids(value: str) -> set[int]:
    result: set[int] = set()
    for item in value.replace("[", "").replace("]", "").split(","):
        item = item.strip().strip("'\"")
        if not item:
            continue
        try:
            result.add(int(item))
        except ValueError:
            logger.warning("Ignoring invalid ADMIN_IDS value: %r", item)
    return result


ADMIN_IDS = parse_admin_ids(ADMIN_IDS_RAW)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def is_admin(message: Message) -> bool:
    return not ADMIN_IDS or bool(message.from_user and message.from_user.id in ADMIN_IDS)


@dp.message(Command("start"))
async def start_handler(message: Message) -> None:
    if not is_admin(message):
        await message.answer("You are not authorized to use this bot.")
        return
    await message.answer(
        "🟢 TelegramArchive is running.\n\n"
        "Add the bot to an authorized group/channel. New messages that Telegram "
        "delivers to the bot will be forwarded to the configured admin chat.\n\n"
        "/id — show your Telegram ID\n"
        "/status — show bot status"
    )


@dp.message(Command("id"))
async def id_handler(message: Message) -> None:
    if message.from_user:
        await message.answer(f"Your Telegram ID: {message.from_user.id}")


@dp.message(Command("status"))
async def status_handler(message: Message) -> None:
    if not is_admin(message):
        return
    me = await bot.get_me()
    await message.answer(
        f"🟢 @{me.username or me.first_name}\n"
        f"Bot ID: {me.id}\n"
        f"Admin chat: {ADMIN_CHAT_ID}\n"
        "Polling: active"
    )


async def forward_message(message: Message) -> None:
    try:
        await message.forward(chat_id=ADMIN_CHAT_ID)
        logger.info(
            "Forwarded chat=%s message=%s to admin_chat=%s",
            message.chat.id,
            message.message_id,
            ADMIN_CHAT_ID,
        )
    except Exception:
        logger.exception(
            "Unable to forward chat=%s message=%s",
            message.chat.id,
            message.message_id,
        )


@dp.channel_post()
async def channel_post_handler(message: Message) -> None:
    await forward_message(message)


@dp.message()
async def group_message_handler(message: Message) -> None:
    if message.chat.type not in {"group", "supergroup"}:
        return
    if message.text and message.text.startswith("/"):
        return
    await forward_message(message)


async def main() -> None:
    me = await bot.get_me()
    logger.info("Starting @%s (id=%s)", me.username, me.id)
    logger.info("Admin chat: %s", ADMIN_CHAT_ID)
    logger.info("Admin IDs: %s", sorted(ADMIN_IDS) if ADMIN_IDS else "unrestricted")

    await bot.delete_webhook(drop_pending_updates=False)

    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "channel_post"],
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
