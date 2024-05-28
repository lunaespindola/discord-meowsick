import discord
from discord.ext import commands
from discord.ui import Button, View

import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
import os
import datetime
from yt_dlp import YoutubeDL


async def setup(bot):
    await bot.add_cog(music_cog(bot))


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cwd = os.getcwd()
        self.names = {}

        self.is_playing = {}
        self.is_paused = {}
        self.musicQueue = {}
        self.queueIndex = {}

        self.YTDL_OPTIONS = {
            'format': 'bestaudio/best',
            'nonplaylist': 'True',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        self.embedBlue = 0x2c76dd
        self.embedRed = 0xdf1141
        self.embedGreen = 0x0eaa51
        self.embedDarkPink = 0x7d3243

        self.vc = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            id = int(guild.id)
            self.musicQueue[id] = []
            self.queueIndex[id] = 0
            self.vc[id] = None
            self.is_paused[id] = self.is_playing[id] = False

            botMember = await guild.fetch_member(self.bot.user.id)
            nickname = botMember.nick
            if nickname is None:
                nickname = botMember.name
            self.names[id] = nickname

    # Auto Leave

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        id = int(member.guild.id)
        if member.id == self.bot.user.id and before.channel is None and after.channel is not None:
            cooldownMinutes = 10
            time = 0
            while True:
                await asyncio.sleep(1)
                time += 1
                if self.is_playing[id] and not self.is_paused[id]:
                    time = 0
                if time == cooldownMinutes * 60:
                    self.is_playing[id] = False
                    self.is_paused[id] = False
                    self.musicQueue[id] = []
                    self.queueIndex[id] = 0
                    await self.vc[id].disconnect()
                if self.vc[id] is None or not self.vc[id].is_connected():
                    break
        if member.id != self.bot.user.id and before.channel is not None and after.channel != before.channel:
            remainingChannelMembers = before.channel.members
            if len(remainingChannelMembers) == 1 and remainingChannelMembers[0].id == self.bot.user.id and self.vc[id].is_connected():
                self.is_playing[id] = False
                self.is_paused[id] = False
                self.musicQueue[id] = []
                self.queueIndex[id] = 0
                await self.vc[id].disconnect()

    @commands.Cog.listener()
    async def on_message(self, message):
        with open('token.txt', 'r') as file:
            userID = int(file.readlines()[1])
        if '#poop' in message.content and message.author.id == userID:
            await message.channel.send("I gotcha fam ;)")
            ctx = await self.bot.get_context(message)
            await self.play(ctx, "https://youtu.be/AkJYdRGu14Y")
        os.chdir(self.cwd)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        print("[" + str(datetime.datetime.now()) + "] " + str(error))
        await ctx.send(embed=self.errorEmbedGen(error))

    def errorEmbedGen(self, error):
        embed = discord.Embed(
            title="ERROR :(",
            description="There was an error. You can likely keep using the bot as is, or just to be safe, you can ask your server administrator to use !reboot to reboot the bot.\n\nError:\n**`" +
            str(error) + "`**",
            colour=self.embedDarkPink
        )
        return embed

    def generate_embed(self, ctx, song, type):
        TITLE = song['title']
        LINK = song['link']
        THUMBNAIL = song['thumbnail']
        AUTHOR = ctx.author
        AVATAR = AUTHOR.avatar

        if type == 1:
            nowPlaying = discord.Embed(
                title="Now Playing",
                description=f'[{TITLE}]({LINK})',
                colour=self.embedBlue
            )
            nowPlaying.set_thumbnail(url=THUMBNAIL)
            nowPlaying.set_footer(
                text=f"Song added by: {str(AUTHOR)}", icon_url=AVATAR)
            return nowPlaying

        if type == 2:
            songAdded = discord.Embed(
                title="Song Added To Queue!",
                description=f'[{TITLE}]({LINK})',
                colour=self.embedRed
            )
            songAdded.set_thumbnail(url=THUMBNAIL)
            songAdded.set_footer(
                text=f"Song added by: {str(AUTHOR)}", icon_url=AVATAR)
            return songAdded

        if type == 4:
            songInserted = discord.Embed(
                title="Song Inserted Next In Queue!",
                description=f'[{TITLE}]({LINK})',
                colour=self.embedRed
            )
            songInserted.set_thumbnail(url=THUMBNAIL)
            songInserted.set_footer(
                text=f"Song inserted by: {str(AUTHOR)}", icon_url=AVATAR)
            return songInserted

        if type == 3:
            songRemoved = discord.Embed(
                title="Song Removed From Queue",
                description=f'[{TITLE}]({LINK})',
                colour=self.embedRed
            )
            songRemoved.set_thumbnail(url=THUMBNAIL)
            songRemoved.set_footer(
                text=f"Song added by: {str(AUTHOR)}", icon_url=AVATAR)
            return songRemoved

    async def join_VC(self, ctx, channel):
        id = int(ctx.guild.id)
        if self.vc[id] is None or not self.vc[id].is_connected():
            self.vc[id] = await channel.connect()

            if self.vc[id] is None:
                await ctx.send("Could not connect to the voice channel.")
                return
        else:
            await self.vc[id].move_to(channel)

    def get_YT_title(self, VideoID):
        params = {"format": "json",
                  "url": "https://www.youtube.com/watch?v=%s" % VideoID}
        url = "https://www.youtube.com/oembed"
        query_string = parse.urlencode(params)
        url = url + "?" + query_string
        with request.urlopen(url) as response:
            response_text = response.read()
            data = json.loads(response_text.decode())
            return data['title']

    def search_YT(self, search):
        queryString = parse.urlencode({'search_query': search})
        htmContent = request.urlopen(
            'http://www.youtube.com/results?' + queryString)
        searchResults = re.findall(
            '/watch\?v=(.{11})', htmContent.read().decode())
        return searchResults[0:10]

    def extract_YT(self, url):
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except:
                return False
        return {
            'link': 'https://www.youtube.com/watch?v=' + url,
            'thumbnail': info['thumbnails'][-1]['url'],
            'source': info['url'],
            'title': info['title']
        }

    def play_next(self, ctx):
        id = int(ctx.guild.id)
        if not self.is_playing[id]:
            return
        if self.queueIndex[id] + 1 < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.queueIndex[id] += 1

            song = self.musicQueue[id][self.queueIndex[id]][0]
            message = self.generate_embed(ctx, song, 1)
            coro = ctx.send(embed=message)
            fut = run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass

            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            coro = ctx.send("You have reached the end of the queue!")
            fut = run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass
            print("Play_next error")
            self.queueIndex[id] += 1
            self.is_playing[id] = False

    async def play_music(self, ctx):
        id = int(ctx.guild.id)
        if self.queueIndex[id] < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.is_paused[id] = False

            song = self.musicQueue[id][self.queueIndex[id]][0]
            message = self.generate_embed(ctx, song, 1)
            await ctx.send(embed=message)

            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            self.is_playing[id] = False

    @commands.command(name="play")
    async def play(self, ctx, *args):
        query = " ".join(args)
        id = int(ctx.guild.id)

        voiceChannel = ctx.author.voice.channel
        if voiceChannel is None:
            await ctx.send("Join a voice channel to play music.")
        else:
            song = self.extract_YT(self.search_YT(query)[0])
            if type(song) == type(True):
                await ctx.send("Could not download song. Try a different keyword.")
            else:
                await self.join_VC(ctx, voiceChannel)
                if self.is_playing[id] or self.is_paused[id]:
                    self.musicQueue[id].append([song, ctx.author])
                    await ctx.send(embed=self.generate_embed(ctx, song, 2))
                else:
                    self.musicQueue[id].append([song, ctx.author])
                    await self.play_music(ctx)

    @commands.command(name="skip")
    async def skip(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] != None and self.vc[id]:
            self.vc[id].stop()
            await self.play_music(ctx)

    @commands.command(name="queue")
    async def queue(self, ctx):
        id = int(ctx.guild.id)
        retval = ""
        for i in range(0, len(self.musicQueue[id])):
            retval += f"{i + 1}. " + self.musicQueue[id][i][0]['title'] + "\n"

        print(retval)
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue.")

    @commands.command(name="pause")
    async def pause(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] != None and self.vc[id]:
            if self.is_paused[id]:
                await ctx.send("Already paused.")
            else:
                self.is_paused[id] = True
                self.is_playing[id] = False
                self.vc[id].pause()
                await ctx.send("Paused.")

    @commands.command(name="resume")
    async def resume(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] != None and self.vc[id]:
            if self.is_paused[id]:
                self.is_paused[id] = False
                self.is_playing[id] = True
                self.vc[id].resume()
                await ctx.send("Resumed.")
            else:
                await ctx.send("Music is not paused.")

    @commands.command(name="remove")
    async def remove(self, ctx, index):
        id = int(ctx.guild.id)
        if self.vc[id] != None and self.vc[id]:
            try:
                s = self.musicQueue[id].pop(int(index) - 1)
                await ctx.send(embed=self.generate_embed(ctx, s[0], 3))
            except:
                await ctx.send("Invalid index.")

    @commands.command(name="clear")
    async def clear(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] != None and self.vc[id]:
            self.is_paused[id] = False
            self.is_playing[id] = False
            self.musicQueue[id] = []
            self.queueIndex[id] = 0
            self.vc[id].stop()
            await ctx.send("Cleared queue.")

    @commands.command(name="leave")
    async def leave(self, ctx):
        id = int(ctx.guild.id)
        self.is_playing[id] = False
        self.is_paused[id] = False
        self.musicQueue[id] = []
        self.queueIndex[id] = 0
        await self.vc[id].disconnect()

    @commands.command(name="insert")
    async def insert(self, ctx, *args):
        query = " ".join(args)
        id = int(ctx.guild.id)

        voiceChannel = ctx.author.voice.channel
        if voiceChannel is None:
            await ctx.send("Join a voice channel to play music.")
        else:
            song = self.extract_YT(self.search_YT(query)[0])
            if type(song) == type(True):
                await ctx.send("Could not download song. Try a different keyword.")
            else:
                await self.join_VC(ctx, voiceChannel)
                if self.is_playing[id] or self.is_paused[id]:
                    self.musicQueue[id].insert(self.queueIndex[id] + 1, [song, ctx.author])
                    await ctx.send(embed=self.generate_embed(ctx, song, 4))
                else:
                    self.musicQueue[id].append([song, ctx.author])
                    await self.play_music(ctx)

    @commands.command(name="move")
    async def move(self, ctx, old_index: int, new_index: int):
        id = int(ctx.guild.id)
        if old_index < 1 or new_index < 1 or old_index > len(self.musicQueue[id]) or new_index > len(self.musicQueue[id]):
            await ctx.send("Invalid index.")
            return

        song = self.musicQueue[id].pop(old_index - 1)
        self.musicQueue[id].insert(new_index - 1, song)
        await ctx.send(f"Moved {song[0]['title']} from position {old_index} to {new_index}.")

    @commands.command(name="play_button")
    async def play_button(self, ctx, *args):
        query = " ".join(args)
        id = int(ctx.guild.id)
        voiceChannel = ctx.author.voice.channel
        if voiceChannel is None:
            await ctx.send("Join a voice channel to play music.")
            return

        song = self.extract_YT(self.search_YT(query)[0])
        if type(song) == type(True):
            await ctx.send("Could not download song. Try a different keyword.")
            return

        await self.join_VC(ctx, voiceChannel)
        self.musicQueue[id].append([song, ctx.author])
        if not self.is_playing[id] and not self.is_paused[id]:
            await self.play_music(ctx)

        buttons = View()
        skip_button = Button(label="Skip", style=discord.ButtonStyle.primary)
        pause_button = Button(label="Pause", style=discord.ButtonStyle.primary)
        resume_button = Button(label="Resume", style=discord.ButtonStyle.primary)
        leave_button = Button(label="Leave", style=discord.ButtonStyle.danger)

        async def skip_callback(interaction):
            await self.skip(ctx)

        async def pause_callback(interaction):
            await self.pause(ctx)

        async def resume_callback(interaction):
            await self.resume(ctx)

        async def leave_callback(interaction):
            await self.leave(ctx)

        skip_button.callback = skip_callback
        pause_button.callback = pause_callback
        resume_button.callback = resume_callback
        leave_button.callback = leave_callback

        buttons.add_item(skip_button)
        buttons.add_item(pause_button)
        buttons.add_item(resume_button)
        buttons.add_item(leave_button)

        await ctx.send(embed=self.generate_embed(ctx, song, 2), view=buttons)
