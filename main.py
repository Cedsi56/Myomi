# This example requires the 'message_content' intent.

import os

from discord import option
from dotenv import load_dotenv
import discord
from discord.ext import commands
import requests
import json
import random

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot()

image_formats = ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif")

links_file = "links.json"

allowed_guilds = [1190980903296569395, 272125925896880129]

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
    new_data = {
        "uploader":user,
        "file_url":image_url
    }
    with open(links_file, 'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        file_data["links"].append(new_data)
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent=4)
    pass

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
    with open(links_file, 'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        links = file_data["links"]
        chosen_image = random.choice(links)

        await ctx.respond(chosen_image["file_url"])
bot.run(TOKEN)