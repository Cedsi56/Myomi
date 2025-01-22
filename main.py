# This example requires the 'message_content' intent.

import os

from discord import option
from dotenv import load_dotenv
import discord
from discord.ext import commands
import requests
import json
import random

from db_connector import *

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot()

image_formats = ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif")

links_file = "links.json"

allowed_guilds = [272125925896880129]

conn = make_connection()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


def is_url_image(image_url):
   r = requests.head(image_url)
   print(r.headers["content-type"])
   if r.headers["content-type"] in image_formats:
      return True
   return False


def save_url(image_url, ctx: discord.ApplicationContext):
    # make new data
    user = ctx.user.id
    insert_into_db(conn, user, image_url)
    conn.commit()


# Add the guild ids in which the slash command will appear.
# If it should be in all, remove the argument, but note that
# it will take some time (up to an hour) to register the
# command if it's for all guilds.
@bot.slash_command(
  name="waifu_upload_url",
  guild_ids=allowed_guilds
)
async def waifu_upload_url(
        ctx: discord.ApplicationContext,
        url: discord.Option(input_type=discord.SlashCommandOptionType.string, description="URL de l'image", required=True)
):
    try:
        print(url)
        if is_url_image(url):
            save_url(url, ctx)
            await ctx.respond("Fichier uploadé!")
            return
    except:
        pass
    await ctx.respond("Ton incompétence est vraiment digne des invalides. "
                      "Ajoute l'URL d'une image valide à ton message si tu veux qu'elle soit ajoutée.")




@bot.slash_command(
  name="waifu_upload_file",
  guild_ids=allowed_guilds
)
@option(
    "file",
    discord.Attachment,
    description="Fichier à upload",
    required=True,  # The default value will be None if the user doesn't provide a file.
)
async def waifu_upload_fichier(
        ctx: discord.ApplicationContext,
        file: discord.Attachment
):
    try:
        if file:
            if file.content_type in image_formats:
                save_url(file.url, ctx)
                await ctx.respond("Fichier uploadé!")
                return
    except:
        pass
    await ctx.respond("Ton incompétence est vraiment digne des invalides. "
                          "Attache une image valide à ton message si tu veux qu'elle soit ajoutée.")



@bot.slash_command(
  name="random_waifu",
  guild_ids=allowed_guilds
)
async def random_waifu(
        ctx: discord.ApplicationContext
):
    nb_links = count_lines(conn)
    chosen_link = random.randint(1, nb_links)
    link = get_link(conn, chosen_link)
    await ctx.respond(link)


@bot.slash_command(
  name="update_db",
  guild_ids=[272125925896880129]
)
async def update_db(
        ctx: discord.ApplicationContext
):
    user_id = ctx.user.id
    if user_id == 143350417093296128:
        with open(links_file, 'r+') as file:
            # First we load existing data into a dict.
            file_data = json.load(file)
            # Join new_data with file_data inside emp_details
            links = file_data["links"]

            for l in links:
                uploader, file_url = l["uploader"], l["file_url"]
                insert_into_db(conn, uploader, file_url)
            commit(conn)
            await ctx.respond("Done!")
    else:
        await ctx.respond("Je ne laisse pas n'importe qui semer la destruction.")

bot.run(TOKEN)

print("Execution is over")

close_connection(conn)
