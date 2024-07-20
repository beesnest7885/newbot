from nextcord.ext import commands
import nextcord
import json
import sys

class AdminCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.trusted_users = set()
        self.load_trusted_users()

    def load_trusted_users(self):
        """Load the trusted users from a JSON file."""
        try:
            with open('trusted_users.json', 'r') as f:
                self.trusted_users = set(json.load(f))
        except FileNotFoundError:
            pass

    def save_trusted_users(self):
        """Save the trusted users to a JSON file."""
        with open('trusted_users.json', 'w') as f:
            json.dump(list(self.trusted_users), f)

    async def cog_check(self, ctx):
        return ctx.author.id in self.trusted_users or ctx.author.guild_permissions.administrator


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addtrusted(self, ctx, user: nextcord.Member):
        self.trusted_users.add(user.id)
        self.save_trusted_users()
        await ctx.send(f"{user.mention} has been added to the trusted users list.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removetrusted(self, ctx, user: nextcord.Member):
        self.trusted_users.discard(user.id)
        self.save_trusted_users()
        await ctx.send(f"{user.mention} has been removed from the trusted users list.")

    @commands.command()
    async def adminonly(self, ctx):
        if ctx.author.guild_permissions.administrator:
            await ctx.send(f"Hello {ctx.author.mention}, you have access to admin-only commands!")
        else:
            await ctx.send("You do not have permission to use this command.")

    @commands.command()
    async def trustedonly(self, ctx):
        if ctx.author.id in self.trusted_users:
            await ctx.send(f"Hello {ctx.author.mention}, you have access to trusted-only commands!")
        else:
            await ctx.send("You are not a trusted user.")

    @commands.command()
    async def addsandwich(self, ctx, user: nextcord.Member, amount: int):
        if ctx.author.guild_permissions.administrator or ctx.author.id in self.trusted_users:
            profile_cog = self.client.get_cog('ProfileCog')
            if profile_cog:
                user_id = str(user.id)
                user_data = profile_cog.profiles.get(user_id, {})
                current_tokens = user_data.get('tokens', 0)
                user_data['tokens'] = current_tokens + amount
                profile_cog.save_profiles()
                await ctx.send(f"Added {amount} sandwich tokens to {user.mention}. New balance: {user_data['tokens']}")
        else:
            await ctx.send("You do not have permission to use this command.")

    @commands.command()
    async def removesandwich(self, ctx, user: nextcord.Member, amount: int):
        if ctx.author.guild_permissions.administrator or ctx.author.id in self.trusted_users:
            profile_cog = self.client.get_cog('ProfileCog')
            if profile_cog:
                user_id = str(user.id)
                user_data = profile_cog.profiles.get(user_id, {})
                current_tokens = user_data.get('tokens', 0)
                user_data['tokens'] = max(current_tokens - amount, 0)
                profile_cog.save_profiles()
                await ctx.send(f"Removed {amount} sandwich tokens from {user.mention}. New balance: {user_data['tokens']}")
        else:
            await ctx.send("You do not have permission to use this command.")

    @commands.command()
    async def load(self, ctx, extension):
        if ctx.author.id in self.trusted_users or ctx.author.guild_permissions.administrator:
            self.client.load_extension(f'cogs.{extension}')
            await ctx.send(f'Loaded {extension}.')
        else:
            await ctx.send("You do not have permission to use this command.")

    @commands.command()
    async def unload(self, ctx, extension):
        if ctx.author.id in self.trusted_users or ctx.author.guild_permissions.administrator:
            self.client.unload_extension(f'cogs.{extension}')
            await ctx.send(f'Unloaded {extension}.')
        else:
            await ctx.send("You do not have permission to use this command.")

    @commands.command()
    async def reload(self, ctx, extension):
        if ctx.author.id in self.trusted_users or ctx.author.guild_permissions.administrator:
            self.client.unload_extension(f'cogs.{extension}')
            self.client.load_extension(f'cogs.{extension}')
            await ctx.send(f'Reloaded {extension}.')
        else:
            await ctx.send("You do not have permission to use this command.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addtrusted(self, ctx, user: nextcord.Member):
        self.trusted_users.add(user.id)
        self.save_trusted_users()
        await ctx.send(f"{user.mention} has been added to the trusted users list.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removetrusted(self, ctx, user: nextcord.Member):
        self.trusted_users.discard(user.id)
        self.save_trusted_users()
        await ctx.send(f"{user.mention} has been removed from the trusted users list.")

    


    @commands.command(name="shutdown")
    @commands.has_permissions(administrator=True)  # optional, to ensure only administrators can use this
    async def shutdown(self, ctx):
        """Shutdown the bot"""
        await ctx.send("Shutting down...")
        await self.client.close()
        sys.exit(0)



    # ... [other code]


    @load.error
    @unload.error
    @reload.error
    @addtrusted.error
    @removetrusted.error
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use this command.")


def setup(client):
    client.add_cog(AdminCog(client))