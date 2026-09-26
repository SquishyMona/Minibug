import discord
import json

class Profile(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    profile = discord.SlashCommandGroup(name="profile", description="Commands relating to server profiles.")

    @profile.command(name="view", guild_ids=[608476415825936394, 1117615350503190549])
    async def view(ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        
        with open("data/profiles.json", "r+") as f:
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
    async def pronouns(ctx, pronouns: str = discord.Option(str, "Add your pronouns to your profile.", required=True)):
        with open("data/profiles.json", "r+") as f:
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
    async def games(ctx, game: str = discord.Option(str, "Add a game to your profile.", required=True)):
        with open("data/profiles.json", "r+") as f:
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
    async def name(ctx, name: str = discord.Option(str, "Edit your name on your profile.", required=True)):
        with open("data/profiles.json", "r+") as f:
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