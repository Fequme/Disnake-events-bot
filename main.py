
import os
from config import events
import disnake
from disnake.ext import commands
import config
from config import *
import os

guild = events['guild']

client = commands.Bot(command_prefix='s!123dlks', intents=disnake.Intents.all(
), test_guilds=[guild])
client.remove_command('help')

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")

client.run(events['token'])
    