import discord
from discord.ext import commands

from gtts import gTTS

from collections import deque
import os

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

class Disctor:
    def __init__(self, bot):
        self.bot = bot

        self.voice = None

        self.text_channel = None
        self.read_channel = None

        self.message_queue = deque()
        self.max_messages_count = 10
        self.playing_message = None

    def tts_done(self):
        os.remove('runtime/' + self.playing_message + '.mp3')
        self.playing_message = None

        if len(self.message_queue) > 0:
            self.next_message()

    def next_message(self):
        message = self.message_queue.pop()
        path = 'runtime/' + message.id + '.mp3'

        tts  = gTTS(text=message.clean_content, lang='ru', slow=False)
        tts.save(path)

        player = self.voice.create_ffmpeg_player(path, after=self.tts_done)
        self.playing_message = message.id
        player.start()

    async def queue_tts(self, message : discord.Message):
        if len(self.message_queue) < self.max_messages_count:
            self.message_queue.appendleft(message)

            print('Queued TTS ' + message.clean_content)

            if len(self.message_queue) == 1 and not self.playing_message:
                self.next_message()
        else:
            await self.say('Can not say the message "' + message.clean_content + '". Too many queued already. This message is skipped.')

    async def join_voice_channel(self, channel : discord.Channel):
        self.voice = await self.bot.join_voice_channel(channel)
        await self.say('Joined voice channel "' + channel.name + '".')

        return True

    async def set_text_channel(self, channel : discord.Channel):
        self.text_channel = channel

        await self.say('Set default text channel to "' + channel.name + '".')

        return True

    async def set_read_channel(self, channel : discord.Channel):
        self.read_channel = channel

        await self.say('Set default read channel to "' + channel.name + '".')

        return True

    async def say(self, message : str):
        if self.text_channel:
            return await self.bot.send_message(self.text_channel, message)
        else:
            return await self.bot.say(message)

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx, channel_type : str):
        if channel_type == 'voice':
            summoned_channel = ctx.message.author.voice_channel
            if summoned_channel is None:
                await self.say('You are not in a voice channel.')
                return False

            return await self.join_voice_channel(summoned_channel)
        elif channel_type == 'text':
            return await self.set_text_channel(ctx.message.channel)
        elif channel_type == 'read':
            return await self.set_read_channel(ctx.message.channel)
        else:
            await self.say('Unknown channel type.')
            return False

    @commands.command(pass_context=True, no_pm=True)
    async def channel(self, ctx, channel_type : str, channel : discord.Channel):
        if channel_type == 'voice':
            return await self.join_voice_channel(channel)
        elif channel_type == 'text':
            return await self.set_text_channel(channel)
        elif channel_type == 'read':
            return await self.set_read_channel(channel)
        else:
            await self.say('Unknown channel type.')

            return False

    async def on_message(self, message):
        # Skip messages sent by the bot
        if self.bot.user == message.author:
            return False

        # Skip messages in not read channel
        if not self.read_channel or self.read_channel != message.channel:
            return False

        prefix = None
        if type(self.bot.command_prefix) is str:
            prefix = self.bot.command_prefix
        else:
            prefix = self.bot.command_prefix(self.bot, message)

        # Skip commands
        if message.content.startswith(prefix):
            return False

        await self.queue_tts(message)
