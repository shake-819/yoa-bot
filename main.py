import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta, timezone
from aiohttp import web, ClientSession
import os
import asyncio
import base64

# ---------- config ----------
TOKEN = os.getenv("BOT_TOKEN")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_PATH = os.getenv("GITHUB_PATH", "events.json")

TRIGGER_WORD = "よあくんOD"
JST = timezone(timedelta(hours=9))

TEN_MESSAGES = {
    10: "まだイける",
    20: "ちょっとしんどい",
    30: "そろそろやめよ？",
    40: "気分悪くなってきた",
    50: "しんどい",
    60: "だいぶやばい",
    70: "吐きそう",
    80: "ｵｪｪｪェ゙ェ゙ｯ",
    90: "待って死ぬ",
    100: "@#%&▲◯■!!!"
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- GitHub util ----------
async def github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

async def load_events():
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"

    async with ClientSession() as session:
        async with session.get(url, headers=await github_headers()) as res:
            if res.status == 200:
                data = await res.json()
                content = base64.b64decode(data["content"]).decode("utf-8")
                return json.loads(content), data["sha"]

    return {"count": 0}, None

async def save_events(data, sha=None):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"

    body = {
        "message": "update events.json",
        "content": base64.b64encode(
            json.dumps(data, ensure_ascii=False, indent=2).encode()
        ).decode()
    }

    if sha:
        body["sha"] = sha

    async with ClientSession() as session:
        await session.put(
            url,
            headers=await github_headers(),
            json=body
        )

# ---------- discord ----------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    daily_reset.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if TRIGGER_WORD in message.content:
        data, sha = await load_events()
        data["count"] += 1
        await save_events(data, sha)

        await message.channel.send("ｺﾞｯｸﾝ💊")

        if data["count"] % 10 == 0:
            msg = TEN_MESSAGES.get(data["count"])
            if msg:
                await message.channel.send(
                    f"💊 {data['count']}回目\n{msg}"
                )

    await bot.process_commands(message)

# ---------- JST 0:00 reset ----------
@tasks.loop(minutes=1)
async def daily_reset():
    now = datetime.now(JST)
    if now.hour == 0 and now.minute == 0:
        data, sha = await load_events()
        count = data["count"]

        if count > 0:
            for ch in bot.get_all_channels():
                if isinstance(ch, discord.TextChannel):
                    await ch.send(f"今日は💊 {count}回飲みました笑笑")
                    break

        await save_events({"count": 0}, sha)

@daily_reset.before_loop
async def before_reset():
    await bot.wait_until_ready()

# ---------- web server ----------
async def health(request):
    return web.Response(text="OK")

async def start_web():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 3000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# ---------- main ----------
async def main():
    await start_web()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
