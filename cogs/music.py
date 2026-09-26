import discord
import wavelink

class Music(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    music = discord.SlashCommandGroup(name="music", description="Commands for playing music.")

    @music.command(name="play")
    async def play(self, ctx, songname: str):
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

    @music.command(name="stop")
    async def stop(self, ctx):
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

    @music.command(name="pause")
    async def pause(self, ctx):
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

    @music.command(name="resume")
    async def resume(self, ctx): 
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

    @music.command(name="skip")
    async def skip(self, ctx):
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

    @music.command(name="viewqueue")
    async def viewqueue(self, ctx):
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

    @music.command(name="repeat")
    async def repeat(self, ctx, mode: str = discord.Option(str, "Choose a repeat mode.", choices=["Off", "Song", "All"], required=True)):
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

def setup(bot):
    bot.add_cog(Music(bot))
