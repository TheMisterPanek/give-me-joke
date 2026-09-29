import asyncio
import logging
import os

from telegram import LinkPreviewOptions, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from store import VectorStore
from reactions import load_scores
from retrieval import choose_joke

logger = logging.getLogger(__name__)


def split_reply(text: str, limit: int = 4000) -> list[str]:
    # Telegram counts UTF-16 code units; emoji can occupy two units.
    chunks, current, size = [], [], 0
    for char in text:
        units = len(char.encode("utf-16-le")) // 2
        if size + units > limit:
            chunks.append("".join(current))
            current, size = [], 0
        current.append(char)
        size += units
    if current:
        chunks.append("".join(current))
    return chunks


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            "Send a topic or message: I will find 15 jokes by meaning "
            "and pick a random one from the five with the best reactions."
        )


async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text or not message.text.strip():
        return
    try:
        text = await asyncio.to_thread(
            choose_joke, context.bot_data["store"], message.text.strip(),
            context.bot_data.get("reaction_scores", {}),
        )
    except Exception as error:
        # Avoid logging request URLs or credentials from exception messages.
        logger.error("Search unavailable: %s", type(error).__name__)
        await message.reply_text("Search is temporarily unavailable. Please try again later.")
        return
    for chunk in split_reply(text):
        await message.reply_text(chunk, link_preview_options=LinkPreviewOptions(is_disabled=True))


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Message handling error: %s", type(context.error).__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env")
    store = VectorStore.load()
    if not store:
        raise SystemExit("Index is empty: run python -m ingest.dataset <export.json>")
    app = Application.builder().token(token).build()
    app.bot_data["store"] = store
    app.bot_data["reaction_scores"] = load_scores()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))
    app.add_error_handler(on_error)
    logger.info("Loaded %s jokes", len(store))
    app.run_polling(allowed_updates=["message"], drop_pending_updates=False)


if __name__ == "__main__":
    main()
