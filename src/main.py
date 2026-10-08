import os
from dotenv import load_dotenv
import json
import io
import discord
from discord.ext import commands
import random
import re

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


#JSON
DATA_FILE = "botdata.json"
default_datafile = {
   "wc": 0,
   "count_channel": None,
   "welcome_channel": None,
}

# load the json file
def load_data():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
      return json.load(f)
  # Default structure if file doesn't exist yet
  return default_datafile

# Save to the json file
def save_data():
    data = {
        "wc": WC, 
        "count_channel": count_channel, 
        "welcome_channel": welcome_channel
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# setup the datafile
saved_data = load_data()
THEWORD = "ghoul"
WC = saved_data.get("wc", 0)
welcome_channel = saved_data.get("welcome_channel", None)
count_channel = saved_data.get("count_channel", None)

# setup intents
intents = discord.Intents.default()
intents.message_content = True

# Command prefix
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

# Hello Command
@bot.command(name="hello", help="Says hello back to you!")
async def hello(ctx):
    # ctx stands for "context", containing info about who sent the message, the channel, etc.
    await ctx.send(f"Hello, {ctx.author.mention}!")

# addition command
@bot.command(name="add", help="Adds two numbers together")
async def add(ctx, a: int, b: int):
    result = a + b
    await ctx.send(f"The result is: {result}")

# setting the counter channel
@bot.command(name="setcounter", help="Sets the Ghoul Counter Channel")
async def set_counter_channel(ctx):
    global count_channel
    count_channel = ctx.channel.id
    save_data()
    await ctx.send(
      f"✅ Notification channel saved! I will send updates for **'{THEWORD}'**"
      " here."
    )

# setting the welcome channel
@bot.command(name="setwelcome", help="Sets the current channel as the welcome message target")
async def setwelcome(ctx):
  global welcome_channel
  welcome_channel = ctx.channel.id
  save_data()
  await ctx.send(f"✅ Welcome channel saved! New members will be greeted here.")

@bot.command(name="ghoul")
async def testembed(ctx):
    # 1. Create the embed object
    embed = discord.Embed(
        title="Ghoul Count!",
        description="Citizens of the Cursed apple here is the current ghoul count!",
        color=discord.Color.green(),  # You can use hex colors too, like 0x5865F2
    )


    # 3. Add fields (Name, Value, inline True/False)
    embed.add_field(name="Total 'Ghoul' Count", value=f"{WC} times", inline=True)

    embed.set_footer(text="Requested via !ghoul command")
    await ctx.send(embed=embed)

# deep debug command
@bot.command(name="inspect_ctx")
async def inspect_ctx(ctx):
  lines = []

  # Loop through every attribute/method available on the context object
  for attr in dir(ctx):
    if attr.startswith("_"):
      continue  # Skip internal dunder methods for readability

    try:
      val = getattr(ctx, attr)
      if callable(val):
        lines.append(f"{attr}() -> [Method]")
      else:
        lines.append(f"{attr} = {val!r}")
    except Exception as e:
      lines.append(f"{attr} = <Error retrieving value: {e}>")

  # Join everything together
  output = "\n".join(lines)

  # Send it as a file attachment so you can scroll through the whole thing
  file = discord.File(
      io.BytesIO(output.encode("utf-8")), filename="ctx_inspection.txt"
  )
  await ctx.send(
      "Here is the complete runtime dump of all attributes and methods inside"
      " `ctx`:",
      file=file,
  )


@bot.event
async def on_member_join(member):
  """Triggered automatically whenever a new user joins the server."""
  if welcome_channel:
    welc = member.guild.get_channel(welcome_channel)
    print(member.mention)
    if welc:
      await welc.send(
          f"Welcome to the server, {member.mention}! Glad to have you here 🎉"
      )
    else:
      print(f"Warning: Could not find welcome channel with ID {welcome_channel}.")
  else:
    # Fallback to the server's default system channel if no custom one is set
    if member.guild.system_channel:
      await member.guild.system_channel.send(
          f"Welcome to the server, {member.mention}! 🎉"
      )

@bot.command(name="roll", help="Rolls dice using notation like !roll 2d20+5")
async def roll(ctx, dice_str: str = "1d20"):
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

  # Perform the rolls
  individual_rolls = [random.randint(1, sides) for _ in range(count)]
  subtotal = sum(individual_rolls)
  total = subtotal + modifier

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

# Check for THE WORD
@bot.event
async def on_message(message):
    global WC
    global count_channel
    # Ignore messages sent by bots or messages in dms
    if message.author.bot or not message.guild:
        await bot.process_commands(message)
        return

    words = [w.strip(".,!?;:\"'").lower() for w in message.content.split()]

    # Checking for the word
    if THEWORD in words:
        WC += 1
        save_data()
        # get the target id
        notif_channel = bot.get_channel(count_channel)

        if notif_channel:
          # Send the notification to the other channel
          await notif_channel.send(
              f"📈 **'{THEWORD}'** has now been said **{WC}** times!"
          )
        else:
          print(
              f"Warning: Could not find channel with ID {count_channel}."
              " Make sure the bot has access to it!"
          )
    await bot.process_commands(message)

# run bot
bot.run(TOKEN.strip())