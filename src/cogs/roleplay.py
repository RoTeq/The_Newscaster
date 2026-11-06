

import discord
from discord import app_commands
from discord.ext import commands
import random
import re
import requests
from sqlite_inter import oracleDB
import csv
import io

def dice_roll(dice:str)->tuple[list[int],int]:
    pattern = r"^(\d*)d(\d+)([+-]\d+)?$"
    match = re.match(pattern, dice)

    count_str, sides_str, mod_str = match.groups()
    
    # Default to 1 die if count is omitted (e.g., "d20" becomes 1 die)
    count = int(count_str) if count_str else 1
    sides = int(sides_str)
    modifier = int(mod_str) if mod_str else 0

    # Perform the rolls
    individual_rolls = [random.randint(1, sides) for _ in range(count)]
    subtotal = sum(individual_rolls)
    total = subtotal + modifier

    return individual_rolls, total




class RpCog(commands.Cog):
    def __init__(self, bot):
       self.bot = bot
       self.db = oracleDB("resources/oracle.db")

    @commands.hybrid_command(name="cf", description="Flips a coin heads or tails")
    async def cf(self, ctx):
        coin = random.randint(1,2)
        if coin == 1:
          await ctx.send(f"Rolled heads!")
          return
        await ctx.send(f"Rolled tails!")
        return



    @commands.hybrid_command(name="roll", description="Rolls dice using notation like !roll 2d20+5")
    async def roll(self, ctx, dice_str: str = "1d20"):
        # Clean up input by converting to lowercase and removing spaces
        dice_str = dice_str.lower().replace(" ", "")

        # Regex pattern to match format: [count]d[sides][+/-modifier]
        # Examples: 2d20+5, d6, 3d8-2, 10d10
        pattern = r"^(\d*)d(\d+)([+-]\d+)?$"
        match = re.match(pattern, dice_str)

        if not match:
            await ctx.send(
                "❌ **Invalid format!** Use standard notation like `!roll 2d20+5` or"
                " `!roll d6`."
            )
            return

        count_str, sides_str, mod_str = match.groups()

        # Default to 1 die if count is omitted (e.g., "d20" becomes 1 die)
        count = int(count_str) if count_str else 1
        sides = int(sides_str)
        modifier = int(mod_str) if mod_str else 0

        # Safety limits to prevent lag or crashing
        if count <= 0 or sides <= 0:
          await ctx.send("❌ Dice count and sides must be greater than 0!")
          return
        if count > 100:
          await ctx.send(
              "❌ Whoa there, Ritualist! You can't roll more than 100 dice at"
              " once."
          )
          return
        if sides > 10000:
          await ctx.send("❌ That die has too many sides! Keep it under 10,000.")
          return

        individual_rolls, total =dice_roll(dice_str)

        # Format the text for individual rolls (truncate if it gets massive)
        rolls_text = ", ".join(str(r) for r in individual_rolls)
        if len(rolls_text) > 900:
          rolls_text = rolls_text[:900] + "... (truncated)"

        mod_text = f" {modifier:+d}" if modifier != 0 else ""

        # Build a clean Embed output
        embed = discord.Embed(title="🎲 Dice Roll Results", color=discord.Color.gold())
        embed.add_field(name="Expression", value=f"`{dice_str}`", inline=False)
        embed.add_field(
            name="Roll Breakdown",
            value=f"[{rolls_text}]{mod_text}",
            inline=False,
        )
        embed.add_field(name="Final Total", value=f"**{total}**", inline=False)

        # Handle case where user doesn't have an avatar set
        avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        embed.set_footer(
            text=f"Rolled by {ctx.author.display_name}", icon_url=avatar_url
        )

        await ctx.send(embed=embed)

    #TODO Finish
    @app_commands.command(name="register_character", description="Registers a character using the google sheet with the stats on it")
    @app_commands.describe(
            character="The character id you want to register",
            sheet="the google sheet with your characters stats on it"
        )
    async def register_char(self, interaction:discord.Interaction, character:str, sheet:str):
       await interaction.response.send_message("Not Implemented, Sorry!")
       return

    @app_commands.command(name="skill_check", description="Registers a character using the google sheet with the stats on it")
    @app_commands.describe(
            character="The character id you want to roll with",
            skill="the skill that you want to check with"
        )
    @app_commands.choices(
        skill=[
            app_commands.Choice(name="Logic", value="logic")
        ]
    )
    async def skill_check(self, interaction:discord.Interaction, character:str, skill:str,):
        await interaction.response.send_message("Not Implemented, Sorry!")
        return
        sheet_id = self.db.get_character_sheet(ctx.author.id, character)
        URL = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&range=C3:C26"
        response = requests.get(URL)
        if response.status_code != 200:
          return None

        # Check sheet content into memory
        decoded_content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(decoded_content))
        rows = list(reader)
        if not rows:
            ctx.send("Sheet is Empty")
        

    


async def setup(bot):
    await bot.add_cog(RpCog(bot))