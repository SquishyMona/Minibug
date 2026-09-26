import os

# on startup in Spakred Host, all packages will be pip installed every time.
# wavelink has discord.py as a dependency and will install it on startup.
# doing this conflicts with pycord, so after all packages are installed, we
# pip uninstall discord.py and pycord, then only install pycord, otherwise
# things will break
os.system("pip uninstall --yes discord.py py-cord")
os.system("pip install --no-input py-cord")

import discord
import logging
import wavelink
import asyncio
from dotenv import load_dotenv
from openrouter import OpenRouter

load_dotenv('./.env')

BOT_KEY = os.getenv("BOT_KEY")
assert BOT_KEY is not None, "BOT_KEY is not set in the environment variables"

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
openrouter = OPENROUTER_KEY and OpenRouter(api_key=OPENROUTER_KEY)

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)
bot.load_extension('cogs.music')
bot.load_extension('cogs.landmark')

queue = wavelink.Queue()

async def connect_nodes():
    await bot.wait_until_ready()
    node = wavelink.Node(uri='ws://lavalinkv4.serenetia.com:80', password="https://seretia.link/discord")
    await wavelink.Pool.connect(client=bot, nodes=[node])

async def get_message_context(message: discord.Message) -> list[dict[str, str]]:
    result = []
    if message.reference:
        replied = await message.channel.fetch_message(message.reference.message_id)
        result.extend(await get_message_context(replied))

    # We want the newest message to be last in the context, since the model will read the messages in order.
    result.append({ "role": "user", "content": f"<@{message.author.id}> {message.content}" })
    return result

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await connect_nodes()

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Wavelink node ready!")

@bot.event
async def on_message(message: discord.Message):
    if not openrouter or not OPENROUTER_MODEL or message.author.id == bot.user.id:
        return

    if not bot.user in message.mentions:
        return

    async with message.channel.typing():
        messages = await get_message_context(message)
        response = await asyncio.to_thread(
            openrouter.chat.send,
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": f"You are a helpful discord bot named {bot.user.name}."},
                {"role": "system", "content": "You are tasked with assisting users in a helpful and friendly manner."},
                {"role": "system", "content": "You are chatting in a Discord server. Each user message is prefixed with a mention tag like <@123456789> identifying who sent it. Do not include this mention tag in your response."},
                {"role": "system", "content": "Keep responses short and casual — a sentence or two is usually enough. Only give longer, more detailed answers when the question genuinely calls for it."},
                {"role": "system", "content": "Type your responses in lowercase unless the word is a proper noun, name of a person, or acronym."},
                *messages
            ],
            stream=False
        )

        await message.reply(
            response.choices[0].message.content,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=[message.author])
        )

@bot.slash_command(name="ping")
async def ping(ctx):
    await ctx.respond("Pong!")

bot.run(BOT_KEY)
