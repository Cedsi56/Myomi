import discord
from discord.ext import commands
import yt_dlp
import asyncio
import urllib.parse, urllib.request, re
from constants import allowed_guilds

queues = {}
voice_clients = {}
youtube_base_url = 'https://www.youtube.com/'
youtube_results_url = youtube_base_url + 'results?'
youtube_watch_url = youtube_base_url + 'watch?v='
yt_dl_options = {"format": "wv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]", "cookiefile": "cookies.txt", "cookies": "cookies.txt", 'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
ytdl = yt_dlp.YoutubeDL(yt_dl_options)

ffmpeg_options = {}



class Music(commands.Cog):
    def __init__(self, setup_bot):  # this is a special method that is called when the cog is loaded
        self.bot = setup_bot

    async def play_next(self, ctx):
        if queues[ctx.guild.id]:
            link = queues[ctx.guild.id].pop(0)
            await self.play(ctx, link=link)


    @discord.slash_command(
      name="play",
      guild_ids=allowed_guilds,
      description="Lance la musique"
    )
    async def play(self, ctx, *, link):
        try:
            voice_client = await ctx.author.voice.channel.connect()
            voice_clients[voice_client.guild.id] = voice_client
        except Exception as e:
            print(e)

        try:

            if youtube_base_url not in link:
                query_string = urllib.parse.urlencode({
                    'search_query': link
                })

                content = urllib.request.urlopen(
                    youtube_results_url + query_string
                )

                search_results = re.findall(r'/watch\?v=(.{11})', content.read().decode())

                link = youtube_watch_url + search_results[0]
            print("aa")
            loop = asyncio.get_event_loop()
            print("bb")
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(link, download=True))
            print(data)
            my_data = data["requested_downloads"][0]["filepath"]
            print(f"----------- {my_data}")
            player = discord.FFmpegOpusAudio(my_data, **ffmpeg_options)

            voice_clients[ctx.guild.id].play(player,
                                             after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            print("ff")
            # await ctx.respond(f"Lancement de la musique {song}")
        except Exception as e:
            print(e)


    @discord.slash_command(
      name="clear_queue",
      guild_ids=allowed_guilds,
      description="Clear la liste des musiques en attente"
    )
    async def clear_queue(self, ctx):
        if ctx.guild.id in queues:
            queues[ctx.guild.id].clear()
            await ctx.send("Queue cleared!")
        else:
            await ctx.send("There is no queue to clear")


    @discord.slash_command(
      name="pause",
      guild_ids=allowed_guilds,
      description="Met la musique en pause"
    )
    async def pause(self, ctx):
        try:
            voice_clients[ctx.guild.id].pause()
            await ctx.respond(f"Mise en pause de la musique")
        except Exception as e:
            print(e)


    @discord.slash_command(
      name="resume",
      guild_ids=allowed_guilds,
      description="Relance la musique mise en pause"
    )
    async def resume(self, ctx):
        try:
            voice_clients[ctx.guild.id].resume()
            await ctx.respond(f"Relancement de la musique")
        except Exception as e:
            print(e)


    @discord.slash_command(
      name="stop",
      guild_ids=allowed_guilds,
      description="Arrête la musique et se déconnecte"
    )
    async def stop(self, ctx):
        try:
            voice_clients[ctx.guild.id].stop()
            await voice_clients[ctx.guild.id].disconnect()
            del voice_clients[ctx.guild.id]
            await ctx.respond(f"Bye!")
        except Exception as e:
            print(e)


    @discord.slash_command(
      name="queue",
      guild_ids=allowed_guilds,
      description="Ajout d'une musique dans la liste d'attente"
    )
    async def queue(self, ctx, *, url):
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []
        queues[ctx.guild.id].append(url)
        await ctx.respond("Musique ajoutée dans la liste d'attente!")

def setup(bot_setup):
    bot_setup.add_cog(Music(bot_setup))
