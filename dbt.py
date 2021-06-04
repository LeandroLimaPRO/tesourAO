# bot.py
import os
import random
import sys
import logging
#from .Lib.Apialbion import AlbionAPI as Ao
from hurry.filesize import size, si
import discord
from discord.colour import Color
from dotenv import load_dotenv
from discord.ext import commands
import json
import requests
import pandas as pd
import asyncio
from Lib.data_json import *
from Lib.inits import *
from Lib.Adminds import Admin
from Lib.Toolsds import Tools
from Lib.Membrods import Membro



load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix=prefix)

@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} conectou ao discord!')
    logger.info(f'')
    atividade = random.choice(atividades)
    activity = discord.Game(name=atividade, type=3)
    await bot.change_presence(status=discord.Status.online, activity=activity)


bot.add_cog(Tools(bot))
bot.add_cog(Membro(bot))
bot.add_cog(Admin(bot))
bot.run(TOKEN)
