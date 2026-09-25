import discord
import json

class LFG(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.activelfg = {}

    lfg = discord.SlashCommandGroup(name="lfg", description="Commands for looking for groups.")

    @lfg.command(name="create", guild_ids=[608476415825936394, 1117615350503190549])
    async def create_lfg(self, ctx):
        modal = NewLFGModal(title="Create a new LFG post!")
        await ctx.send_modal(modal)

class LFGView(discord.ui.View):
    async def on_timeout(self):
        self.disable_all_items()
        await self.message.edit(embed=self.message.embeds[0].add_field(name="This LFG has ended.", value=f"Use /lfg create to start a new post", inline=False))

    @discord.ui.button(label="I'm Interested!", style=discord.ButtonStyle.blurple)
    async def interested(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id in self.activelfg[self.id]:
            await interaction.response.send_message("You have already joined!", ephemeral=True)
            return
        with open("data/lfg.json", "r+") as f:
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
                    self.activelfg[self.id].append(interaction.user.id)

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
            self.activelfg.update({view.id: []})
            new_data = {
                'id': view.id,
                'game': self.children[0].value, 
                'description': self.children[1].value, 
                'playercap': self.children[2].value,
                'players': [],
                'time': self.children[3].value
            }
            with open("data/lfg.json", "r+") as f:
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
