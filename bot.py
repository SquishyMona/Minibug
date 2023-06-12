import discord
import json
import logging

from discord.ext import commands

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
bot = commands.Bot()

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

bot.run("MTExNzgzMTUwNTA4Mzg5NTgxOQ.GLpeF0.Jtf9fFOck5RvPG4FDsf-y3ozLAyxTalN49XITE")