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

allowed_guilds = [1190980903296569395, 272125925896880129]

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


async def make_embed(ctx: discord.ApplicationContext, number, max_number, url, uploader):
    embed = discord.Embed(
        color=discord.Colour.purple(),  # Pycord provides a class with default colors you can choose from
    )
    embed.set_image(url=url)
    if uploader is not None:
        uploader_user = await bot.fetch_user(uploader)
        embed.set_author(name=f"Uploaded by {uploader_user.name}", icon_url=uploader_user.avatar)
    embed.set_footer(text=f"Waifu #{number}/{max_number}")
    return embed


# Add the guild ids in which the slash command will appear.
# If it should be in all, remove the argument, but note that
# it will take some time (up to an hour) to register the
# command if it's for all guilds.
@bot.slash_command(
  name="waifu_upload_url",
  guild_ids=allowed_guilds,
  description="Upload d'une image de waifu par URL"
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
  guild_ids=allowed_guilds,
  description="Upload d'une image de waifu par fichier"
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
  guild_ids=allowed_guilds,
  description="Waifu random"
)
async def random_waifu(
        ctx: discord.ApplicationContext
):
    nb_links = count_lines(conn)
    chosen_link = random.randint(1, nb_links)
    link,uploader = get_link(conn, chosen_link)
    uploader = None
    embed = await make_embed(ctx, chosen_link - 1, nb_links - 1, link, uploader)
    await ctx.respond(embed=embed)


@bot.slash_command(
  name="waifu_from_number",
  guild_ids=allowed_guilds,
  description="Waifu à partir d'un numéro"
)
async def waifu_from_number(
        ctx: discord.ApplicationContext,
        number: discord.Option(input_type=discord.SlashCommandOptionType.integer, description="Numéro de la waifu", required=True)
):
    try:
        link, uploader = get_link(conn, int(number) + 1)
        embed = await make_embed(ctx, number, count_lines(conn) - 1, link, uploader)
        await ctx.respond(embed=embed)
    except:
        await ctx.respond("Tant de nombres disponibles; et tu en choisis un qui n'est pas valide. C'est déplorable, mais digne de toi.")


@bot.slash_command(
  name="random_waifu_from_user",
  guild_ids=allowed_guilds,
  description="Waifu random d'un utilisateur"
)
async def random_waifu_from_user(
        ctx: discord.ApplicationContext,
        user: discord.Option(input_type=discord.SlashCommandOptionType.mentionable, description="@Utilisateur", required=True)
):
    user = str(user).split('>')[0].split('@')[1]
    nb_links = count_lines_user(conn, user)
    chosen_link = random.randint(1, nb_links)
    link = get_link_user(conn, chosen_link, user)

    embed = await make_embed(ctx, chosen_link, nb_links, link, user)
    await ctx.respond(embed=embed)


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
