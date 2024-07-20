import nextcord
from nextcord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

import sqlite3

def setup_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        user_id TEXT PRIMARY KEY, 
        races_won INT DEFAULT 0,
        races_lost INT DEFAULT 0,
        challenges_won INT DEFAULT 0,
        challenges_lost INT DEFAULT 0,
        fights_won INT DEFAULT 0,
        fights_lost INT DEFAULT 0,
        tokens INT DEFAULT 0,
        xp INT DEFAULT 0,
        rank TEXT,
        inventory TEXT,
        has_active_charm INT DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()

setup_database()


load_dotenv()  # This will load the .env file
TOKEN = os.getenv('DISCORD_TOKEN')  # Read token from environment variables

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set or is empty.")

intents = nextcord.Intents.default()
intents.message_content = True  # Enable the message content intent
client = commands.Bot(command_prefix="?", intents=intents)

def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            cog_name = filename[:-3]
            print(f"Loading {cog_name}")
            client.load_extension(f"cogs.{cog_name}")

@commands.command()
async def reload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    client.load_extension(f"cogs.{extension}")
    await ctx.send(f"{extension} has been reloaded")

# Load the cogs before running the bot
load_cogs()

@client.event
async def on_ready():
    print("Bot is ready.")
    await client.change_presence(activity=nextcord.Game(name=".help for commands"))

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found!")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the necessary permissions.")
    # Add more error checks as necessary
    else:
        await ctx.send("An error occurred while processing the command.")
        raise error  # This will send the error to the console.


client.run(TOKEN)
