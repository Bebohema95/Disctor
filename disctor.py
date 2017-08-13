from gtts import gTTS

import discord
from discord.ext import commands

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

from Disctor import Disctor

bot = commands.Bot(command_prefix=commands.when_mentioned)

dt = Disctor(bot)
bot.add_cog(dt)

bot.run('token')
