import discord
import json

def get_self_assignable_roles(guild_id: str):
    try:
        with open("data/roles.json", "r") as file:
            data = json.load(file)
            return data[str(guild_id)]
    except Exception as ex:
        print(f'Error opening roles file: ${ex.with_traceback}')

class RoleSelect(discord.ui.Select):
    def __init__(self, roles, mode):
        self.roles = roles
        self.mode = mode
        options = []
        for role_id in roles:
            options.append(discord.SelectOption(label=roles[role_id], value=role_id))
        
        super().__init__(
            placeholder="Choose your roles...",
            min_values=0,
            max_values=len(roles),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user = interaction.user

        added = []
        removed = []

        for role_id in self.values:
            role = interaction.guild.get_role(int(role_id))
            if role not in user.roles and self.mode == 'get':
                await user.add_roles(role)
                added.append(role.mention)
            if role in user.roles and self.mode == 'drop':
                await user.remove_roles(role)
                removed.append(role.mention)

        response = "Your roles have been updated!\n"
        if added:
            response += f"**Added:** {', '.join(added)}\n"
        if removed:
            response += f"**Removed:** {', '.join(removed)}\n"
        if not added and not removed:
            response = "No changes were made."

        await interaction.followup.send(response, ephemeral=True)

class RoleView(discord.ui.View):
    def __init__(self, roles, mode):
        super().__init__(timeout=None)
        self.add_item(RoleSelect(roles, mode))

class Role(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    roles = discord.SlashCommandGroup(name="roles", description="Commands for assigning and removing roles")

    @roles.command(name="get")
    async def get(self, ctx: discord.ApplicationContext):
        roles = get_self_assignable_roles(ctx.interaction.guild_id)
        await ctx.respond("Select all the roles you'd like from the dropdown!", view=RoleView(roles, 'get'), ephemeral=True)

    @roles.command(name="drop")
    async def get(self, ctx: discord.ApplicationContext):
        roles = get_self_assignable_roles(ctx.interaction.guild_id)
        await ctx.respond("Select all the roles you'd like remove from yourself", view=RoleView(roles, 'drop'), ephemeral=True)

def setup(bot):
    bot.add_cog(Role(bot))
        
