import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta, timezone
from aiohttp import web
import os
import asyncio

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

#ALLOWED_ROLE_ID = 1466580088333271334

TOKEN = os.getenv("BOT_TOKEN")

TRIGGER_WORD = "よあくんOD"
EVENTS_FILE = "events.json"

JST = timezone(timedelta(hours=9))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- util ----------
def load_events():
    if not os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "w") as f:
            json.dump({"count": 0}, f)
    with open(EVENTS_FILE, "r") as f:
        return json.load(f)

def save_events(data):
    with open(EVENTS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- discord ----------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    daily_reset.start()
    for guild in bot.guilds:
        print(guild.name, guild.icon.url if guild.icon else None)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # ロールチェック
    #if not any(role.id == ALLOWED_ROLE_ID for role in message.author.roles):
        #return

    if TRIGGER_WORD in message.content:
        data = load_events()
        data["count"] += 1
        save_events(data)

        # 毎回
        await message.channel.send("ｺﾞｯｸﾝ💊")

        # 10回刻み
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
        data = load_events()
        count = data["count"]

        if count > 0:
            channel = bot.get_all_channels()
            for ch in channel:
                if isinstance(ch, discord.TextChannel):
                    await ch.send(f"今日は💊 {count}回飲みました笑笑")
                    break

        save_events({"count": 0})

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
