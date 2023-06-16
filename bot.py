import discord
import json
import logging
import wavelink

from discord import SlashCommandGroup

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
bot = discord.Bot()
queue = wavelink.Queue()

@bot.event
async def on_ready():
    await connect_nodes()

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Wavelink node {node.id} ready!")

async def connect_nodes():
    await bot.wait_until_ready()
    node = wavelink.Node(uri='narco.buses.rocks:2269', password='glasshost1984')
    await wavelink.NodePool.connect(client=bot, nodes=[node])

@bot.slash_command(name="ping", guild_ids=[608476415825936394, 1117615350503190549])
async def ping(ctx):
    await ctx.respond("Pong!")

@bot.slash_command(name="addlandmark", guild_ids=[608476415825936394, 1117615350503190549])
async def add_landmark(ctx, name: str, x: str, y: str, z: str, image: discord.Attachment):
    try:
        new_data = {'name': name, 'x': x, 'y': y, 'z': z, 'img': image.url}
        with open("landmarks.json", "r+") as f:
            landmarks = json.load(f)
            landmarks["landmarks"].append(new_data)
            f.seek(0)
            json.dump(landmarks, f, indent=4)

        await ctx.respond(f"{name} at {x}, {y}, {z} has been added! Here is what it looks like:")
        
        embed = discord.Embed(title=name, description=f"Coordinates: {x}, {y}, {z}", color=0x00ff00)
        embed.set_thumbnail(url=image.url)

        await ctx.respond(embed=embed)
    except:
        await ctx.respond("Something went wrong! Please try again.")

@bot.slash_command(name="getlandmark", guild_ids=[608476415825936394, 1117615350503190549])
async def get_landmark(ctx, name: str):
    try:
        with open("landmarks.json", "r") as f:
            landmarks = json.load(f)
            for landmark in landmarks["landmarks"]:
                if landmark["name"] == name:
                    embed = discord.Embed(title=name, description=f"Coordinates: {landmark['x']}, {landmark['y']}, {landmark['z']}", color=0x00ff00)
                    embed.set_thumbnail(url=landmark["img"])
                    await ctx.respond(embed=embed)
                    return
            await ctx.respond(f"Could not find {name}. Try adding it with /addlandmark!")
    except:
        await ctx.respond("Something went wrong! Please try again.")

@bot.slash_command(name="directory", guild_ids=[608476415825936394, 1117615350503190549])
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

@music.command(name="play", guild_ids=[608476415825936394, 1117615350503190549])
async def play(ctx, songname: str):
    vc = ctx.voice_client

    if ctx.author.voice is None:
        await ctx.respond("You must be in a voice channel!")
        return

    if not vc:
        vc = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    
    if ctx.author.voice.channel.id != vc.channel.id:
        await ctx.respond("You have to be in the same voice channel as Minibug!")
        return
    
    song = await wavelink.YouTubeTrack.search(songname)

    if not song:
        return await ctx.respond("We couldn't find a song with that name!")
    
    if queue.is_empty and not vc.is_playing():
        await vc.play(song[0])
        await ctx.respond(f"Playing {song[0].title}!")
    else:
        queue.put(song[0])
        await ctx.respond(f"Added {song[0].title} to the queue!")

@music.command(name="stop", guild_ids=[608476415825936394, 1117615350503190549])
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
    queue.clear()
    await ctx.respond("Stopped!")

@music.command(name="pause", guild_ids=[608476415825936394, 1117615350503190549])
async def pause(ctx):
    vc = ctx.voice_client

    if ctx.author.voice is None:
        await ctx.respond("You must be in a voice channel!")
        return

    if not vc:
        return await ctx.respond("Minibug is not in a voice channel!")
    
    if ctx.author.voice.channel.id != vc.channel.id:
        return await ctx.respond("You have to be in the same voice channel as Minibug!")
    
    await vc.pause()
    await ctx.respond("Paused!")

@music.command(name="resume", guild_ids=[608476415825936394, 1117615350503190549])
async def resume(ctx): 
    vc = ctx.voice_client

    if ctx.author.voice is None:
        await ctx.respond("You must be in a voice channel!")
        return
    
    if not vc:
        return await ctx.respond("Minibug is not in a voice channel!")
    
    if ctx.author.voice.channel.id != vc.channel.id:
        return await ctx.respond("You have to be in the same voice channel as Minibug!")
    
    await vc.resume()
    await ctx.respond("Resumed!")

@music.command(name="skip", guild_ids=[608476415825936394, 1117615350503190549])
async def skip(ctx):
    vc = ctx.voice_client

    if ctx.author.voice is None:
        await ctx.respond("You must be in a voice channel!")
        return
    
    if not vc:
        return await ctx.respond("Minibug is not in a voice channel!")
    
    if ctx.author.voice.channel.id != vc.channel.id:
        return await ctx.respond("You have to be in the same voice channel as Minibug!")
    
    await vc.play(queue.get())
    await ctx.respond("Skipped!")

@music.command(name="viewqueue", guild_ids=[608476415825936394, 1117615350503190549])
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
    for song in queue._queue:
        embed.add_field(name=song.title, value=f"Duration: {song.duration}", inline=False)
    await ctx.respond(embed=embed)

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

bot.add_application_command(profile)

bot.run("MTExNzgzMTUwNTA4Mzg5NTgxOQ.GLpeF0.Jtf9fFOck5RvPG4FDsf-y3ozLAyxTalN49XITE")