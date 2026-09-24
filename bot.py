import os
os.system("pip uninstall --yes discord.py py-cord")
os.system("pip install --no-input py-cord")

import discord
import json
import logging
import wavelink
import time
import requests
import asyncio
from dotenv import load_dotenv
from openrouter import OpenRouter

from discord import SlashCommandGroup

load_dotenv('./.env')

BOT_KEY = os.getenv("BOT_KEY")
assert BOT_KEY is not None, "BOT_KEY is not set in the environment variables"

EXAROTON_KEY = os.getenv("EXAROTON_KEY")
EXAROTON_SERVER_ID = os.getenv("EXAROTON_SERVER_ID")

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
queue = wavelink.Queue()

activelfg = {}
#print(EXAROTON_SERVER_ID)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await connect_nodes()

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Wavelink node ready!")

async def get_message_context(message: discord.Message) -> list[dict[str, str]]:
    result = []
    if message.reference:
        replied = await message.channel.fetch_message(message.reference.message_id)
        result.extend(await get_message_context(replied))

    # We want the newest message to be last in the context, since the model will read the messages in order.
    result.append({ "role": "user", "content": f"<@{message.author.id}> {message.content}" })
    return result

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
                {"role": "system", "content": "You are chatting in a Discord server. Each user message is prefixed with a mention tag like <@123456789> identifying who sent it."},
                {"role": "system", "content": "Keep responses short and casual — a sentence or two is usually enough. Only give longer, more detailed answers when the question genuinely calls for it."},
                *messages
            ],
            stream=False
        )

        await message.reply(
            response.choices[0].message.content,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=[message.author])
        )


async def connect_nodes():
    await bot.wait_until_ready()
    node = wavelink.Node(uri='ws://lavalinkv4.serenetia.com:80', password="https://seretia.link/discord")
    await wavelink.Pool.connect(client=bot, nodes=[node])

@bot.slash_command(name="ping", guild_ids=[608476415825936394, 1117615350503190549, 1540164753698332673])
async def ping(ctx):
    await ctx.respond("Pong!")

async def get_landmark_by_name(ctx: discord.AutocompleteContext):
    with open("landmarks.json", "r") as f:
        landmarks = json.load(f)
        return [landmark["name"] for landmark in landmarks["landmarks"]]

@bot.slash_command(name="getlandmark", guild_ids=[608476415825936394, 1117615350503190549, 1540164753698332673])
async def get_landmark(ctx, name: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_landmark_by_name), required=True)):
    try:
        with open("landmarks.json", "r") as f:
            landmarks = json.load(f)
            for landmark in landmarks["landmarks"]:
                if landmark["name"] == name:
                    embed = discord.Embed(title=landmark["name"], description=landmark["description"], color=0x00ff00)
                    embed.add_field(name="Coordinates", value=f"{landmark['x']}, {landmark['y']}, {landmark['z']}", inline=False)                    
                    embed.set_thumbnail(url=landmark["img"])
                    await ctx.respond(embed=embed)
                    return
            await ctx.respond(f"Could not find {name}. Try adding it with /landmark add!")
    except:
        await ctx.respond("Something went wrong! Please try again.")

@bot.slash_command(name="directory", guild_ids=[608476415825936394, 1117615350503190549, 1540164753698332673])
async def directory(ctx):
    try:
        with open("landmarks.json", "r") as f:
            landmarks = json.load(f)
            embed = discord.Embed(title="Directory", description="Here are all the landmarks that have been added.", color=0x00ff00)
            for landmark in landmarks["landmarks"]:
                embed.add_field(name=landmark["name"], value=f"Coordinates: {landmark['x']}, {landmark['y']}, {landmark['z']}", inline=False)
            await ctx.respond(embed=embed)
    except:
        await ctx.respond("Something went wrong! Please try again.")

music = bot.create_group(name="music", description="Commands for playing music.")

@music.command(name="play", guild_ids=[608476415825936394, 1117615350503190549, 1540164753698332673])
async def play(ctx, songname: str):
    await ctx.defer()
    message = await ctx.followup.send("Searching for song...", wait=True)

    vc = ctx.voice_client

    if ctx.author.voice is None:
        await message.edit("You must be in a voice channel!")
        return

    if not vc:
        vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        vc.autoplay = wavelink.AutoPlayMode.partial
    
    if ctx.author.voice.channel.id != vc.channel.id:
        await message.edit("You have to be in the same voice channel as Minibug!")
        return
    
    songs = await wavelink.Playable.search(songname)

    if not songs:
        return await message.edit("We couldn't find a song with that name!")
    
    if len(vc.queue._items) <= 0 and not vc.playing:
        await vc.play(songs[0])
        await message.edit(f"Playing {songs[0].title}!")
    else:
        await vc.queue.put_wait(songs[0])
        await message.edit(f"Added {songs[0].title} to the queue!")

@music.command(name="stop", guild_ids=[608476415825936394, 1117615350503190549, 1540164753698332673])
async def stop(ctx):
    vc = ctx.voice_client

    if ctx.author.voice is None:
        await ctx.respond("You must be in a voice channel!")
        return
    
    if not vc:
        return await ctx.respond("Minibug is not in a voice channel!")
    
    if ctx.author.voice.channel.id != vc.channel.id:
        return await ctx.respond("You have to be in the same voice channel as Minibug!")
    
    await vc.stop()
    vc.queue.clear()
    await ctx.respond("Stopped!")

@music.command(name="pause", guild_ids=[608476415825936394, 1117615350503190549, 1540164753698332673])
async def pause(ctx):
    vc = ctx.voice_client

    if ctx.author.voice is None:
        await ctx.respond("You must be in a voice channel!")
        return

    if not vc:
        return await ctx.respond("Minibug is not in a voice channel!")
    
    if ctx.author.voice.channel.id != vc.channel.id:
        return await ctx.respond("You have to be in the same voice channel as Minibug!")
    
    await vc.pause(not vc.paused)
    await ctx.respond("Paused!")

@music.command(name="resume", guild_ids=[608476415825936394, 1117615350503190549, 1540164753698332673])
async def resume(ctx): 
    vc = ctx.voice_client

    if ctx.author.voice is None:
        await ctx.respond("You must be in a voice channel!")
        return
    
    if not vc:
        return await ctx.respond("Minibug is not in a voice channel!")
    
    if ctx.author.voice.channel.id != vc.channel.id:
        return await ctx.respond("You have to be in the same voice channel as Minibug!")
    
    await vc.pause(not vc.paused)
    await ctx.respond("Resumed!")

@music.command(name="skip", guild_ids=[608476415825936394, 1117615350503190549, 1540164753698332673])
async def skip(ctx):
    vc = ctx.voice_client

    if ctx.author.voice is None:
        await ctx.respond("You must be in a voice channel!")
        return
    
    if not vc:
        return await ctx.respond("Minibug is not in a voice channel!")
    
    if ctx.author.voice.channel.id != vc.channel.id:
        return await ctx.respond("You have to be in the same voice channel as Minibug!")
    
    await vc.play(vc.queue.get())
    await ctx.respond("Skipped!")

@music.command(name="viewqueue", guild_ids=[608476415825936394, 1117615350503190549, 1540164753698332673])
async def viewqueue(ctx):
    vc = ctx.voice_client

    if ctx.author.voice is None:
        await ctx.respond("You must be in a voice channel!")
        return
    
    if not vc:
        return await ctx.respond("Minibug is not in a voice channel!")
    
    if ctx.author.voice.channel.id != vc.channel.id:
        return await ctx.respond("You have to be in the same voice channel as Minibug!")
    
    embed = discord.Embed(title="Queue", description="Here are the songs in the queue.", color=0x00ff00)
    for song in vc.queue._items:
        embed.add_field(name=song.title, value=f"{song.author}", inline=False)
    await ctx.respond(embed=embed)

@music.command(name="repeat", guild_ids=[608476415825936394, 1117615350503190549, 1540164753698332673])
async def repeat(ctx, mode: discord.Option(str, "Choose a repeat mode.", choices=["Off", "Song", "All"], required=True)):
    vc = ctx.voice_client

    if ctx.author.voice is None:
        await ctx.respond("You must be in a voice channel!")
        return
    
    if not vc:
        return await ctx.respond("Minibug is not in a voice channel!")
    
    if ctx.author.voice.channel.id != vc.channel.id:
        return await ctx.respond("You have to be in the same voice channel as Minibug!")
    
    if mode == "Off":
        vc.queue.mode = wavelink.QueueMode.normal
    elif mode == "Song":
        vc.queue.mode = wavelink.QueueMode.loop
    elif mode == "All":
        vc.queue.mode = wavelink.QueueMode.loop_all

    await ctx.respond(f"Repeat mode set to {mode}!")

profile = SlashCommandGroup("profile", "Commands relating to server profiles.")

@profile.command(name="view", guild_ids=[608476415825936394, 1117615350503190549])
async def view(ctx, user: discord.Member = None):
    if user is None:
        user = ctx.author
    
    with open("profiles.json", "r+") as f:
        profiles = json.load(f)
        for profile in profiles["profiles"]:
            if profile["id"] == user.id:
                embed = discord.Embed(title=f"{profile['name']}", color=0x00ff00)
                embed.set_thumbnail(url=user.avatar.url)
                embed.add_field(name="Pronouns", value=profile["pronouns"], inline=False)
                gamelist = ""
                for game in profile["games"]:
                    gamelist += game + "\n"
                embed.add_field(name="Games", value=gamelist, inline=False)
                await ctx.respond(embed=embed)
                return
        newprofile = {"name": user.display_name, "id": user.id, "pronouns": "", "games": []}
        profiles["profiles"].append(newprofile)
        f.seek(0)
        json.dump(profiles, f, indent=4)
        f.truncate()
        embed = discord.Embed(title=f"{newprofile['name']}", color=0x00ff00)
        embed.set_thumbnail(url=user.avatar.url)
        embed.add_field(name="Pronouns", value=newprofile["pronouns"], inline=False)
        gamelist = ""
        for game in newprofile["games"]:
            gamelist += game + "\n"
        embed.add_field(name="Games", value=gamelist, inline=False)
        await ctx.respond(embed=embed)

edit = profile.create_subgroup(name="edit", description="Edit your profile.")

@edit.command(name="pronouns", guild_ids=[608476415825936394, 1117615350503190549])
async def pronouns(ctx, pronouns: discord.Option(str, "Add your pronouns to your profile.", required=True)):
    with open("profiles.json", "r+") as f:
        profiles = json.load(f)
        for profile in profiles["profiles"]:
            if profile["id"] == ctx.author.id:
                profile["pronouns"] = pronouns
                f.seek(0)
                json.dump(profiles, f, indent=4)
                f.truncate()
                await ctx.respond("Pronouns updated!")
                return
        await ctx.respond("You don't have a profile! Use /view create to create one!")

@edit.command(name="game", guild_ids=[608476415825936394, 1117615350503190549])
async def games(ctx, game: discord.Option(str, "Add a game to your profile.", required=True)):
    with open("profiles.json", "r+") as f:
        profiles = json.load(f)
        for profile in profiles["profiles"]:
            if profile["id"] == ctx.author.id:
                profile["games"].append(game)
                f.seek(0)
                json.dump(profiles, f, indent=4)
                f.truncate()
                await ctx.respond("Games updated!")
                return
        await ctx.respond("You don't have a profile! Use /view create to create one!")

@edit.command(name="name", guild_ids=[608476415825936394, 1117615350503190549])
async def name(ctx, name: discord.Option(str, "Edit your name on your profile.", required=True)):
    with open("profiles.json", "r+") as f:
        profiles = json.load(f)
        for profile in profiles["profiles"]:
            if profile["id"] == ctx.author.id:
                profile["name"] = name
                f.seek(0)
                json.dump(profiles, f, indent=4)
                f.truncate()
                await ctx.respond("Name updated!")
                return
        await ctx.respond("You don't have a profile! Use /view create to create one!")

class NewLandmarkModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Name", placeholder="Enter the name of this landmark."))
        self.add_item(discord.ui.InputText(label="Description", placeholder="What is this landmark?", style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Coordinates", placeholder="Enter the coordinates here."))

    async def callback(self, interaction: discord.Interaction):
        try:
            cords = self.children[2].value.split(", ")
            new_data = {
                'name': self.children[0].value, 
                'x': cords[0], 
                'y': cords[1], 
                'z': cords[2], 
                'description': self.children[1].value, 
                'img': ''
            }
            with open("landmarks.json", "r+") as f:
                landmarks = json.load(f)
                landmarks["landmarks"].append(new_data)
                f.seek(0)
                json.dump(landmarks, f, indent=4)
            embed = discord.Embed(title=self.children[0].value, description=self.children[1].value, color=0x00ff00)
            embed.add_field(name="Coordinates", value=f"{cords[0]}, {cords[1]}, {cords[2]}", inline=False)

            await interaction.response.send_message(f"{self.children[0].value} has been added! Here is what it looks like:", embed=embed)
            #embed.set_thumbnail(url=image.url)
        except Exception as e:
            print(e.with_traceback())
            await interaction.respond("Something went wrong! Please try again.")

landmarks = SlashCommandGroup("landmarks", "Commands for managing landmarks.")

@landmarks.command(name="add", guild_ids=[608476415825936394, 1117615350503190549])
async def add_landmark(ctx):
    modal = NewLandmarkModal(title="Add a new landmark!")
    await ctx.send_modal(modal)

@landmarks.command(name="view", guild_ids=[608476415825936394, 1117615350503190549])
async def get_landmark(ctx, 
                       name: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_landmark_by_name), required=True),
                       hide_response: discord.Option(bool, description="Hide the response message.", required=False)
                       ):
    try:
        with open("landmarks.json", "r") as f:
            landmarks = json.load(f)
            for landmark in landmarks["landmarks"]:
                if landmark["name"] == name:
                    embed = discord.Embed(title=landmark["name"], description=landmark["description"], color=0x00ff00)
                    embed.add_field(name="Coordinates", value=f"{landmark['x']}, {landmark['y']}, {landmark['z']}", inline=False)                    
                    embed.set_thumbnail(url=landmark["img"])
                    await ctx.respond(embed=embed, ephemeral=hide_response)
                    return
            await ctx.respond(f"Could not find {name}. Try adding it with /landmark add!", ephemeral=True)
    except:
        await ctx.respond("Something went wrong! Please try again.", ephemeral=True)

@landmarks.command(name="remove", guild_ids=[608476415825936394, 1117615350503190549])
async def remove_landmark(ctx, 
                          name: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_landmark_by_name), required=True),
                          hide_response: discord.Option(bool, description="Hide the response message.", required=False)
                          ):
    with open("landmarks.json", "r+") as f:
        landmarks = json.load(f)
        for landmark in landmarks["landmarks"]:
            if landmark["name"] == name:
                landmarks["landmarks"].remove(landmark)
                f.seek(0)
                json.dump(landmarks, f, indent=4)
                f.truncate()
                await ctx.respond(f"{name} has been removed!", ephemeral=hide_response)
                return
        await ctx.respond(f"Could not find {name} in the directory!", ephemeral=True)

lfg = bot.create_group(name="lfg", description="Commands for looking for groups.")

class LFGView(discord.ui.View):
    async def on_timeout(self):
        self.disable_all_items()
        await self.message.edit(embed=self.message.embeds[0].add_field(name="This LFG has ended.", value=f"Use /lfg create to start a new post", inline=False))

    @discord.ui.button(label="I'm Interested!", style=discord.ButtonStyle.blurple)
    async def interested(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id in activelfg[self.id]:
            await interaction.response.send_message("You have already joined!", ephemeral=True)
            return
        with open("lfg.json", "r+") as f:
            lfgs = json.load(f)
            for lfg in lfgs["lfg"]:
                if lfg["id"] == self.id:
                    lfg["players"].append(interaction.user.id)
                    f.seek(0)
                    json.dump(lfgs, f, indent=4)
                    f.truncate()
                    playersstr = ""
                    for player in lfg["players"]:
                        playersstr += f"<@{player}>\n"
                    await self.message.edit(embed=self.message.embeds[0].set_field_at(1, name="Players Interested", value=playersstr, inline=True))
                    await interaction.response.send_message("Thanks for responding, you'll be notified at the event start time!", ephemeral=True)
                    activelfg[self.id].append(interaction.user.id)

class NewLFGModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Game", placeholder="Enter the game you want to play."))
        self.add_item(discord.ui.InputText(label="Description", placeholder="What are you looking for?", required=False, style=discord.InputTextStyle.long))
        self.add_item(discord.ui.InputText(label="Players", placeholder="How many players are you looking for?", required=False, style=discord.InputTextStyle.short))
        self.add_item(discord.ui.InputText(label="Time", placeholder="Please format like this: 11:00PM", required=False, style=discord.InputTextStyle.short))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            view = LFGView()
            activelfg.update({view.id: []})
            new_data = {
                'id': view.id,
                'game': self.children[0].value, 
                'description': self.children[1].value, 
                'playercap': self.children[2].value,
                'players': [],
                'time': self.children[3].value
            }
            with open("lfg.json", "r+") as f:
                lfgs = json.load(f)
                lfgs["lfg"].append(new_data)
                f.seek(0)
                json.dump(lfgs, f, indent=4)
            embed = discord.Embed(title=new_data['game'], description=new_data['description'], color=0x00ff00)
            embed.add_field(name="Time", value=new_data['time'], inline=False)
            embed.add_field(name="Players Interested", value='', inline=False)

            await interaction.channel.send(f"<@{interaction.user.id}> is looking people to play {self.children[0].value}! @everyone", embed=embed, view=view)
            await interaction.respond("Your post is up!", ephemeral=True)
        except Exception as e:
            print(e.with_traceback())
            await interaction.respond("Something went wrong! Please try again.")

@lfg.command(name="create", guild_ids=[608476415825936394, 1117615350503190549])
async def create_lfg(ctx):
    modal = NewLFGModal(title="Create a new LFG post!")
    await ctx.send_modal(modal)

server = bot.create_group(name="server", description="Commands for server management.")

@server.command(name="geyserupdate", guild_ids=[608476415825936394, 1117615350503190549])
async def geyserupdate(ctx: discord.ApplicationContext):
    if not EXAROTON_KEY or not EXAROTON_SERVER_ID:
        await ctx.respond("Exaroton is not configured. Set EXAROTON_KEY and EXAROTON_SERVER_ID in .env.", ephemeral=True)
        return
    
    await ctx.defer()
    message = await ctx.followup.send("Checking server status...", wait=True)
    try:
        headers = {"Authorization": f"Bearer {EXAROTON_KEY}"}
        response = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}", headers=headers)
        server = response.json()
        print(server)
        status = server["data"]["status"]
        print("Checking server status...")
        print(status)
        while status != 0 and status != 1:
            await message.edit(content="Server is processing, waiting...")
            print("Server is processing, waiting...")
            time.sleep(15)
            server = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}", headers=headers)
            status = server.json()["data"]["status"]
        if status == 1:       
            server = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}", headers=headers)
            onlineplayers = server.json()["data"]["players"]["count"]
            
            if onlineplayers != 0:
                for i in range(1, 6):
                    command = f"/say §cATTENTION: The server needs to perform an update and will stop in {6 - i} minutes. Please get to a safe spot and logout before this."
                    commandreq = requests.post(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}/command", headers=headers, json={"command": command})
                    print(commandreq.json())
                    await message.edit(content=f"The server is currently online. The server will stop in {6 - i} minutes to give time for players to logout.")
                    time.sleep(60)
                    server = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}", headers=headers)
                    onlineplayers = server.json()["data"]["players"]["count"]
                    if onlineplayers == 0:
                        break

            await message.edit(content="Server is online, stopping...")        
            print("Server is online, stopping...")
            stopreq = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}/stop", headers=headers)
            time.sleep(10)
            server = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}", headers=headers)
            status = server.json()["data"]["status"]
            while status != 0:
                await message.edit(content="Server is still online, waiting...")
                print("Server is still online, waiting...")
                time.sleep(15)
                server = requests.get(f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}", headers=headers)
                status = server.json()["data"]["status"]

        await message.edit(content="Server is offline, downloading Geyser update file...")
        print("Server is offline, downloading Geyser update file")
        
        updateFile = requests.get("https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/spigot")
        if updateFile.status_code != 200:
            print("Failed to download file")
            await message.edit(content="Failed to download file! Please try again.")
            return
        
        print(updateFile.headers)
        await message.edit(content="Downloaded file, uploading to server...")
        print("Downloaded file, uploading to server...")
        
        response = requests.put(
            f"https://api.exaroton.com/v1/servers/{EXAROTON_SERVER_ID}/files/data/plugins/Geyser-Spigot.jar",
            data=updateFile.content,
            headers={
                "Authorization": f"Bearer {EXAROTON_KEY}",
                "Content-Type": "application/octet-stream"
            }
        )        
        if response.status_code != 200:
            print(response.json())
            print("Failed to upload file")
            await message.edit(content="Failed to upload file! Please try again.")
            return
        print("File uploaded successfully")
        await message.edit(content="Geyser updated!")
    except Exception as e:
        print(e.with_traceback())
        await message.edit(content="Something went wrong! Please try again.")
            



bot.add_application_command(profile)
bot.add_application_command(landmarks)

bot.run(BOT_KEY)
