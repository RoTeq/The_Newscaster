###############################
#                             #
#      Entry Point            #
#                             #
###############################

###############################
######## Imports ##############
###############################

import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
import json
import sqlite_inter as database


###############################
######## Load Env #############
###############################

#dotenv loading for token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
DB_FILE = "resources/oracle.db"

# setup intents
intents = discord.Intents.default()
intents.message_content = True

# Command prefix and bot setup
bot = commands.Bot(command_prefix="!", intents=intents)



# voicelines file
VOICELINES_FILE = "voicelines.json"
default_voicelines = { # fallback to default if not included
    "quotes": [
        "Come friends, The New York Oracle isn't just the news. It's a glimpse into the future!",
        "What calamities await New York? For five measly pennies, our prognostications can be yours!",
        "The New York Oracle, bringing the future to the present for over 20 years.",
    ]
}

# Load Voice Lines from JSON
def load_voicelines():
  if os.path.exists(VOICELINES_FILE):
    with open(VOICELINES_FILE, "r") as f:
      return json.load(f)
  return default_voicelines

voicelines_data = load_voicelines()



###############################
###### Basic Function #########
###############################

# Setup bot information
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

    # Load Cogs
    await bot.load_extension("cogs.ghoulcount")
    print("✅ Loaded Ghoul cog!")
    await bot.load_extension("cogs.roleplay")
    print("✅ Loaded Roleplay cog!")

    # Load Slash Commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")
    print("------")


@bot.hybrid_command(name="taxes", description="Does your taxes")
async def taxes(ctx):
    embed = discord.Embed(
           title="Tax Doer!",
           description="ITS YOU! DO YOUR OWN DAMN TAXES!",
           color=discord.Color.red()
        )
    avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    embed.set_footer(
    text=f"taxes done by {ctx.author.display_name}", icon_url=avatar_url
  )

    await ctx.send(embed=embed)

# Run the bot
bot.run(TOKEN.strip())