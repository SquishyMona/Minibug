import discord
from lib.odoo.cache import get_self_assignable_roles, invalidate_roles

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

    async def send_role_select(self, ctx: discord.ApplicationContext, mode: str, prompt: str):
        # the Odoo lookup can take longer than Discord's 3 second response window
        await ctx.defer(ephemeral=True)
        try:
            roles = await get_self_assignable_roles(ctx.interaction.guild_id)
        except Exception:
            await ctx.respond("Couldn't load the role list right now, try again in a bit.", ephemeral=True)
            return

        if not roles:
            await ctx.respond("There are no self assignable roles in this server.", ephemeral=True)
            return

        await ctx.respond(prompt, view=RoleView(roles, mode), ephemeral=True)

    @roles.command(name="get")
    async def get(self, ctx: discord.ApplicationContext):
        await self.send_role_select(ctx, 'get', "Select all the roles you'd like from the dropdown!")

    @roles.command(name="drop")
    async def drop(self, ctx: discord.ApplicationContext):
        await self.send_role_select(ctx, 'drop', "Select all the roles you'd like remove from yourself")

    @roles.command(name="refresh", description="Reload the self assignable role list from Odoo")
    async def refresh(self, ctx: discord.ApplicationContext):
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.respond("You need the Manage Roles permission to do that.", ephemeral=True)
            return

        invalidate_roles(ctx.interaction.guild_id)
        await ctx.respond("Role list will be reloaded from Odoo on the next use.", ephemeral=True)

    @discord.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        invalidate_roles(after.guild.id)

    @discord.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        invalidate_roles(role.guild.id)

def setup(bot):
    bot.add_cog(Role(bot))
        
