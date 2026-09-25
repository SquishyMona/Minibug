import discord
import json

async def get_landmark_by_name(ctx: discord.AutocompleteContext):
    try:
        with open("data/landmarks.json", "r") as f:
            landmarks = json.load(f)
            return [landmark["name"] for landmark in landmarks["landmarks"]]
    except Exception:
        return []

class Landmark(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @discord.slash_command(name="getlandmark")
    async def get_landmark(self, ctx, name: str = discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_landmark_by_name), required=True)):
        try:
            with open("data/landmarks.json", "r") as f:
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

    @discord.slash_command(name="directory")
    async def directory(self, ctx):
        try:
            with open("data/landmarks.json", "r") as f:
                landmarks = json.load(f)
                embed = discord.Embed(title="Directory", description="Here are all the landmarks that have been added.", color=0x00ff00)
                for landmark in landmarks["landmarks"]:
                    embed.add_field(name=landmark["name"], value=f"Coordinates: {landmark['x']}, {landmark['y']}, {landmark['z']}", inline=False)
                await ctx.respond(embed=embed)
        except:
            await ctx.respond("Something went wrong! Please try again.")

    landmarks = discord.SlashCommandGroup(name="landmarks", description="Commands for managing landmarks.")

    @landmarks.command(name="add")
    async def add_landmark(self, ctx):
        modal = NewLandmarkModal(title="Add a new landmark!")
        await ctx.send_modal(modal)

    @landmarks.command(name="view")
    async def get_landmark(self, ctx, 
                        name: str = discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_landmark_by_name), required=True),
                        hide_response: str = discord.Option(bool, description="Hide the response message.", required=False)
                        ):
        try:
            with open("data/landmarks.json", "r") as f:
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

    @landmarks.command(name="remove")
    async def remove_landmark(self, ctx, 
                            name: str = discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_landmark_by_name), required=True),
                            hide_response: str = discord.Option(bool, description="Hide the response message.", required=False)
                            ):
        with open("data/landmarks.json", "r+") as f:
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
            with open("data/landmarks.json", "r+") as f:
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

def setup(bot):
    bot.add_cog(Landmark(bot))