# Ghoulcount file with the information for the ghoulcount subprogram

###############################
######## Imports ##############
###############################

import discord
from discord import app_commands
from discord.ext import commands
import re
from sqlite_inter import oracleDB

###############################
######## Load Env #############
###############################

THEWORD = "ghoul"

###############################
###### Ghoul Cog  #############
###############################

class GhoulCog(commands.Cog):
    def __init__(self, bot):
       self.bot = bot
       self.db = oracleDB("resources/oracle.db")


    # embed count check
    @commands.hybrid_command(name="ghoul", description="checks the count of ghouls")
    @app_commands.choices(ghoul_count=[
        app_commands.Choice(name="Server", value="server"),
        app_commands.Choice(name="Me", value="me")
    ])
    async def ghoul(self, ctx, server:str="server"):

        match server:
            case "server":
                count = self.db.get_global_stat("ghoul_count",0)
                embed = discord.Embed(
                    title="Ghoul Count!",
                    description="Citizens of the Cursed Apple here is the current ghoul count!",
                    color=discord.Color.green()
                )
                # Add fields (Name, Value, inline True/False)
                embed.add_field(name="Total 'Ghoul' Count", value=f"{count} times", inline=True)
                embed.set_footer(text="Requested via !ghoul command")
            case "me":
                count = self.db.get_user_stat(ctx.author.id)
                embed = discord.Embed(
                    title="Ghoul Count!",
                    description="Citizen of the Cursed Apple here is your current ghoul count!",
                    color=discord.Color.green()
                )
                # Add fields (Name, Value, inline True/False)
                embed.add_field(name="Total 'Ghoul' Count", value=f"{count[1]} times", inline=True)
                embed.set_footer(text="Requested via !ghoul command")


        # Create the embed object
        await ctx.send(embed=embed)

    @app_commands.command(name="set_ghoul_count", description="set the ghoul count channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_ghoul_count(self, interaction: discord.Interaction):
        count_channel = interaction.channel.id
        self.db.upsert_global("count_channel",count_channel)
        await interaction.response.send_message(
          f"✅ Notification channel saved! I will send updates for **'{THEWORD}'**"
          " here.",
          ephemeral=True
        )

    @app_commands.command(name="ghoul_leaderboard", description="set the ghoul count channel")
    async def ghoul_leaderboard(self, interaction: discord.Interaction):
        top_ghouls = self.db.get_top_ghouls(limit=10)
        embed = discord.Embed(title="👻 Ghoul Leaderboard", color=discord.Color.blue())
        i = 1
        for ghoul in top_ghouls:
            embed.add_field(name=F"Ghouler #{i}", value=f"{ghoul[0]}  | `{ghoul[1]}`", inline=False)
            i+= 1
        embed.set_footer(text= "Brought to you by the streets of New York!")
        await interaction.response.send_message(embed=embed)

    # listener for ghoul
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or message.content.startswith("!"):
            return
        pattern = re.compile(r"ghoul", re.IGNORECASE) # create regex


        if pattern.search(message.content):
            current = int(self.db.get_global_stat("ghoul_count","0"))
            new_count = current + 1
            hundred = True if (new_count % 100) == 0 else False # get the modulo to check 100s
            self.db.upsert_global("ghoul_count", str(new_count))
            self.db.upsert_user(message.author.id, message.author.display_name, ghoul_increment=1)
            notif_channel = self.bot.get_channel(int(self.db.get_global_stat("count_channel")))
            if notif_channel and hundred:
                # Send the notification to the other channel
                await notif_channel.send(
                    f"📈 **'{THEWORD}'** has now been said **{new_count}** times!"
                )

        await self.bot.process_commands(message) # backwards compatibility

    #check for command errors
    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ):
      if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You do not have the required permissions (Administrator) to run"
            " this command.",
            ephemeral=True,
        )
      elif isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "❌ You are not authorized to use this command.", ephemeral=True
        )
      else:
        # Let other unexpected errors bubble up normally
        raise error
            

async def setup(bot):
    await bot.add_cog(GhoulCog(bot))
