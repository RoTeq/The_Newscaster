import csv
import io
import discord
from discord import app_commands
from discord.ext import commands, tasks
import requests
from sqlite_inter import oracleDB


class SheetCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = oracleDB("resources/oracle.db")
        # Replace with your actual Google Sheet ID
        self.sheet_id = "1Ku5oJGMfuP4gjtJD7i0G2xkbxPRsOSuzpMFXlgfVPJ4"

        self.allowed_columns = [2, 6, 7]

        # Start the 24-hour background loop when the cog loads
        self.auto_post_sheet.start()

    def cog_unload(self):
        # Safely cancel the loop if the cog is unloaded/reloaded
        self.auto_post_sheet.cancel()

    # --- SHARED HELPER: Deletes old messages & chunks new ones across multiple messages ---
    async def post_or_update_sheet(self, channel: discord.TextChannel):
        lines = self.fetch_sheet_lines()
        if not lines:
            return False

        # 1. Delete previous multi-part update messages if stored in database
        old_ids_str = self.db.get_global_stat("last_sheet_message_ids")
        if old_ids_str:
            for old_id in old_ids_str.split(","):
                try:
                    old_msg = await channel.fetch_message(int(old_id))
                    await old_msg.delete()
                except (discord.NotFound, discord.HTTPException, ValueError):
                    pass
            
        # 2. Chunk formatted lines into groups that fit safely under Discord's ~1900 char limit
        chunks = []
        current_chunk = []
        current_length = 0

        for line in lines:
            line_len = len(line) + 1
            if current_length + line_len > 1800:
                chunks.append(current_chunk)
                current_chunk = [line]
                current_length = line_len
            else:
                current_chunk.append(line)
                current_length += line_len

        if current_chunk:
            chunks.append(current_chunk)

        # 3. Send each chunk as a separate message and collect their IDs
        new_message_ids = []
        for idx, chunk in enumerate(chunks):
            part_label = (
                f" (Part {idx + 1}/{len(chunks)})" if len(chunks) > 1 else ""
            )
            content = (
                f"```\n"
                + "\n".join(chunk)
                + "\n```"
            )
    
            sent_msg = await channel.send(content)
            new_message_ids.append(str(sent_msg.id))
    
        # 4. Save comma-separated list of message IDs to SQLite
        self.db.upsert_global("last_sheet_message_ids", ",".join(new_message_ids))
        return True

    # --- BACKGROUND TASK (Runs every 1 hour) ---
    @tasks.loop(hours=1)
    async def auto_post_sheet(self):
        channel_id_str = self.db.get_global_stat("sheet_channel_id")
        if not channel_id_str:
            return

        channel = self.bot.get_channel(int(channel_id_str))
        if channel:
            await self.post_or_update_sheet(channel)

    @auto_post_sheet.before_loop
    async def before_auto_post_sheet(self):
        # Wait until the bot is fully booted and connected before starting the loop timer
        await self.bot.wait_until_ready()

    # --- HELPER: Pulls CSV, filters columns, pads text, and returns formatted lines ---
    def fetch_sheet_lines(self):
      url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?format=csv"
      try:
        response = requests.get(url)
        if response.status_code != 200:
          return None
    
        decoded_content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(decoded_content))
        rows = list(reader)
    
        if not rows:
          return ["Sheet is empty."]
    
        # 1. Filter rows based on allowed columns
        filtered_rows = []
        for row in rows:
          filtered_row = [row[i] for i in self.allowed_columns if i < len(row)]
          if filtered_row:
            filtered_rows.append(filtered_row)
    
        if not filtered_rows:
          return ["Sheet has no valid data after filtering."]
    
        # 2. Find maximum character length for each column across ALL rows
        num_cols = len(self.allowed_columns)
        col_widths = [0] * num_cols
    
        for row in filtered_rows:
          for idx, cell in enumerate(row):
            if idx < num_cols:
              col_widths[idx] = max(col_widths[idx], len(str(cell)))
    
        # 3. Build padded lines for every row
        formatted_lines = []
        for row_idx, row in enumerate(filtered_rows):
          padded_cells = []
          for idx, cell in enumerate(row):
            if idx < num_cols:
              padded_cells.append(str(cell).ljust(col_widths[idx]))
    
          formatted_lines.append(" | ".join(padded_cells))
    
          # Add a neat divider line right underneath the header
          if row_idx == 0:
            divider = "-+-".join(["-" * width for width in col_widths])
            formatted_lines.append(divider)
    
        return formatted_lines
      except Exception as e:
        print(f"Error fetching Google Sheet lines: {e}")
        return None

    # --- ADMIN COMMAND: Set the channel ---
    @app_commands.command(name="set_sheet_channel", description="Set the channel for Google Sheet updates")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_sheet_channel(self, interaction: discord.Interaction):
        channel_id = str(interaction.channel.id)
        self.db.upsert_global("sheet_channel_id", channel_id)

        await interaction.response.send_message(
            f"✅ This channel (<#{channel_id}>) has been set to receive the daily"
            " Google Sheet updates!",
            ephemeral=True,
        )

    # --- ADMIN COMMAND: Test & Force Update (Deletes Previous) ---
    @app_commands.command(name="test_sheet",description=("Manually pull the sheet, delete the old update, and post the new one."),)
    @app_commands.checks.has_permissions(administrator=True)
    async def test_sheet(self, interaction: discord.Interaction):
        channel_id_str = self.db.get_global_stat("sheet_channel_id")
        if not channel_id_str:
            await interaction.response.send_message(
                "❌ No sheet channel configured yet! Run `/set_sheet_channel` first.",
                ephemeral=True,
            )
            return

        channel = self.bot.get_channel(int(channel_id_str))
        if not channel:
            await interaction.response.send_message(
                "❌ Could not locate the configured channel.", ephemeral=True
            )
            return

        # Defer response since network requests can take a split second
        await interaction.response.defer(ephemeral=True)

        success = await self.post_or_update_sheet(channel)
        if success:
            await interaction.followup.send(
                "✅ Sheet successfully refreshed! The old message was deleted and a"
                " new one posted.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "❌ Failed to fetch data from the Google Sheet URL.", ephemeral=True
            )

    # Error handler for admin check
    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need Administrator permissions to use this command.",
                ephemeral=True,
            )
        else:
            raise error



async def setup(bot):
    await bot.add_cog(SheetCog(bot))