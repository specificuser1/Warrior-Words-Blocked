import discord
from discord.ext import commands, tasks
import os
import json
from dotenv import load_dotenv
from collections import defaultdict
from datetime import timedelta

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)

# Warnings dictionary
warnings = defaultdict(int)

# ---------------- FILE LOAD ----------------
def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def load_extra_words():
    if not os.path.exists("block.txt"):
        return []
    with open("block.txt", "r") as f:
        return [line.strip().upper() for line in f if line.strip()]

def save_extra_words(words):
    with open("block.txt", "w") as f:
        for w in words:
            f.write(w + "\n")

config = load_config()

# ---------------- ACTIVITIES ----------------
activities = [
    "WARRIOR SYSTEM",
    "PROGRAMMED BY SUBHAN",
    "POWERED BY NOOB",
    "SAFE & SECURE",
    "WARRIOR ON TOP",
    "SERVER NOT ACTIVE"
    "www.warriorcheat.store"
]

@tasks.loop(seconds=20)
async def change_activity():
    activity = discord.Game(activities[change_activity.current_loop % len(activities)])
    await bot.change_presence(status=discord.Status.dnd, activity=activity)

# ---------------- PUBLIC LOG FUNCTION ----------------
async def send_log(guild, embed):
    log_channel_id = config.get("log_channel_id")
    if not log_channel_id:
        return
    channel = guild.get_channel(log_channel_id)
    if channel:
        await channel.send(embed=embed)

# ---------------- BOT READY ----------------
@bot.event
async def on_ready():
    print(f"Bot Ready: {bot.user}")
    change_activity.start()

# ---------------- MESSAGE FILTER ----------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    default_words = config["default_words"]
    extra_words = load_extra_words()
    blocked_words = [w.upper() for w in default_words + extra_words]
    msg = message.content.upper()

    for word in blocked_words:
        if word in msg:
            await message.delete()
            warnings[message.author.id] += 1
            warn_count = warnings[message.author.id]

            # Warning Embed
            warn_embed = discord.Embed(
                title="WARRIOR SYSTEM",
                description=f"Please don't use {word} this of word",
                color=discord.Color.red()
            )
            warn_embed.set_footer(text=f"{warn_count}/4 warning")
            await message.channel.send(
                content=message.author.mention,
                embed=warn_embed,
                delete_after=6
            )

            # Public Log
            log_embed = discord.Embed(
                title="WARRIOR SYSTEM LOG",
                color=discord.Color.red()
            )
            log_embed.add_field(name="User", value=f"{message.author}", inline=True)
            log_embed.add_field(name="Channel", value=f"{message.channel}", inline=True)
            log_embed.add_field(name="Blocked Word", value=word, inline=False)
            log_embed.add_field(name="Warnings", value=f"{warn_count}/4", inline=True)
            await send_log(message.guild, log_embed)

            # Timeout if 4 warnings
            if warn_count >= 4:
                try:
                    await message.author.timeout(
                        timedelta(days=7),
                        reason="4 warnings reached"
                    )
                    timeout_log = discord.Embed(
                        title="WARRIOR SYSTEM LOG",
                        description="User reached 4 warnings and received timeout.",
                        color=discord.Color.red()
                    )
                    timeout_log.add_field(name="User", value=f"{message.author}", inline=True)
                    timeout_log.add_field(name="Duration", value="7 days", inline=True)
                    await send_log(message.guild, timeout_log)
                except:
                    pass

            return

    await bot.process_commands(message)

# ---------------- COMMANDS ----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def addblock(ctx, *, word):
    word = word.upper()
    words = load_extra_words()
    if word in words:
        await ctx.send("Word already blocked.")
        return
    words.append(word)
    save_extra_words(words)
    await ctx.send(f"Blocked word added: {word}")

@bot.command()
@commands.has_permissions(administrator=True)
async def removeblock(ctx, *, word):
    word = word.upper()
    words = load_extra_words()
    if word not in words:
        await ctx.send("Word not found.")
        return
    words.remove(word)
    save_extra_words(words)
    await ctx.send(f"Blocked word removed: {word}")

@bot.command()
async def checkwords(ctx):
    default_words = config["default_words"]
    extra_words = load_extra_words()
    all_words = default_words + extra_words
    text = "\n".join(all_words)
    embed = discord.Embed(
        title="Blocked Words",
        description=text,
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="WARRIOR SYSTEM COMMANDS",
        description="""
!addblock <word>       → Add blocked word
!removeblock <word>    → Remove blocked word
!checkwords            → Show blocked words
!resetwarning <id>     → Reset warnings for member
!help                  → Show this help
""",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# ---------------- RESET WARNING COMMAND ----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def resetwarning(ctx, member_id: int):
    member = ctx.guild.get_member(member_id)
    if not member:
        await ctx.send("Member not found.")
        return

    warnings[member.id] = 0
    await ctx.send(f"Warnings reset for {member.mention}.")

    # Log the reset
    log_embed = discord.Embed(
        title="WARRIOR SYSTEM LOG",
        description=f"Warnings reset for {member}",
        color=discord.Color.red()
    )
    await send_log(ctx.guild, log_embed)

# ---------------- RUN BOT ----------------
bot.run(TOKEN)
