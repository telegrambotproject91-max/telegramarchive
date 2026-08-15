# TelegramArchive

Minimal Telegram bot for forwarding messages that Telegram legitimately delivers to the bot from authorized groups/channels to one administrator chat.

## Environment variables

```text
BOT_TOKEN=your_bot_token
ADMIN_IDS=6016750433,7163632964
ADMIN_CHAT_ID=-1004372433721
```

`ADMIN_IDS` is a comma-separated list of Telegram user IDs allowed to use bot commands. `ADMIN_CHAT_ID` is the destination chat/group.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Render

Use a **Background Worker**.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python main.py
```

The bot only processes updates Telegram provides to it. It does not bypass Telegram permissions, protected content, or private-chat access controls.
