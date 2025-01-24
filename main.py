# This example requires the 'message_content' intent.

import os
from datetime import datetime

from discord import option
from discord.ui import Item, Button
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

ESSENCE_GAIN = [0, 10, 20, 50, 100, 200]
ESSENCE_COST = [10000, 40, 80, 200, 500, 1000]

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


def is_url_image(image_url):
   r = requests.head(image_url)
   print(r.headers["content-type"])
   if r.headers["content-type"] in image_formats:
      return True
   return False


def save_url(image_url, ctx: discord.ApplicationContext, star = 1):
    # make new data
    conn = make_connection()
    user = ctx.user.id

    # download the file before continuing
    response = requests.get(image_url)


    if response.status_code == 200:
        next_id = get_next_id(conn)
        r = requests.head(image_url)
        file_ext = r.headers["content-type"].split("/")[1]
        file = f"images/{next_id}.{file_ext}"
        directory = os.path.dirname(file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(file, "wb") as fp:
            print("test")
            fp.write(response.content)
        print("Image downloaded successfully.")
        insert_into_db(conn, user, file, star)
        conn.commit()
    else:
        print(f"Failed to download the image. Status code: {response.status_code}")

    close_connection(conn)


async def make_embed(ctx: discord.ApplicationContext, number, max_number, star_rating, uploader):
    etoiles = "⭐" * star_rating
    print(etoiles)
    embed = discord.Embed(
        title=etoiles,
        color=discord.Colour.purple(),  # Pycord provides a class with default colors you can choose from
    )
    embed.set_image(url="attachment://image.png")
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
        url: discord.Option(input_type=discord.SlashCommandOptionType.string, description="URL de l'image", required=True),
        star: discord.Option(input_type=discord.SlashCommandOptionType.integer, description="Nombre d'étoiles", required=False)
):
    try:
        print(url)
        if is_url_image(url):
            save_url(url, ctx, star)
            await ctx.respond("Fichier uploadé!")
            return
    except Exception as e:
        print(e)
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
        file: discord.Attachment,
        star: discord.Option(input_type=discord.SlashCommandOptionType.integer, description="Nombre d'étoiles", required=False)
):
    try:
        if file:
            if file.content_type in image_formats:
                save_url(file.url, ctx, star)
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
    conn = make_connection()
    nb_links = count_lines(conn)
    chosen_link = random.randint(1, nb_links)
    link,uploader,star = get_link(conn, chosen_link)
    uploader = None
    embed = await make_embed(ctx, chosen_link - 1, nb_links - 1, star, uploader)
    close_connection(conn)
    file = discord.File(link, filename="image.png")
    await ctx.respond(file=file, embed=embed)



class MyView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
    def __init__(self, number, max_number, *items: Item):
        super().__init__(*items)
        self.number = int(number)
        self.max_number = int(max_number)
        self.set_button_states()

    def set_button_states(self):
        button1 = self.get_item("left")
        button1.disabled = False
        button2 = self.get_item("right")
        button2.disabled = False
        if self.number == 0:
            button1.disabled = True
        if self.number == self.max_number:
            button2.disabled = True

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⬅️", custom_id="left", disabled=True)
    async def first_button_callback(self, button, interaction):
        self.number -= 1
        self.set_button_states()

        conn = make_connection()
        link, uploader, star = get_link(conn, int(self.number) + 1)
        max_number = count_lines(conn) - 1
        embed = await make_embed(None, self.number, max_number, star, uploader)
        file = discord.File(link, filename="image.png")
        close_connection(conn)
        await self.message.edit(file=file, embed=embed, view=MyView(self.number, max_number))
        await interaction.response.edit_message(view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="➡️", custom_id="right", disabled=True)
    async def second_button_callback(self, button, interaction):
        self.number += 1
        self.set_button_states()
        conn = make_connection()
        link, uploader, star = get_link(conn, int(self.number) + 1)
        max_number = count_lines(conn) - 1
        embed = await make_embed(None, self.number, max_number, star, uploader)
        file = discord.File(link, filename="image.png")
        close_connection(conn)
        await self.message.edit(file=file, embed=embed, view=MyView(self.number, max_number))
        await interaction.response.edit_message(view=self)


@bot.slash_command(
  name="waifu_from_number",
  guild_ids=allowed_guilds,
  description="Waifu à partir d'un numéro"
)
async def waifu_from_number(
        ctx: discord.ApplicationContext,
        number: discord.Option(input_type=discord.SlashCommandOptionType.integer, description="Numéro de la waifu", required=True)
):
    conn = make_connection()
    try:
        link, uploader, star = get_link(conn, int(number) + 1)
        max_number = count_lines(conn) - 1
        embed = await make_embed(ctx, number, max_number, star, uploader)
        file = discord.File(link, filename="image.png")
        await ctx.respond(file=file, embed=embed, view=MyView(number, max_number))
        close_connection(conn)
    except Exception as e:
        print(e)
        close_connection(conn)
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
    conn = make_connection()
    user = str(user).split('>')[0].split('@')[1]
    nb_links = count_lines_user(conn, user)
    chosen_link = random.randint(1, nb_links)
    link, star = get_link_user(conn, chosen_link, user)

    close_connection(conn)
    embed = await make_embed(ctx, chosen_link, nb_links, star, user)
    file = discord.File(link, filename="image.png")
    await ctx.respond(file=file, embed=embed)


@bot.slash_command(
  name="update_db",
  guild_ids=[272125925896880129]
)
async def update_db(
        ctx: discord.ApplicationContext
):
    conn = make_connection()
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
    close_connection(conn)


def get_pull(current_pity, current_4star_pity):
    pull = random.randint(1, 1001)

    from_pity = False
    if current_pity >= 60:
        pull = 1  # guaranteed 5 star
        from_pity = True
    elif current_4star_pity >= 20:
        pull = 60  # guaranteed 4 star
        from_pity = True

    fivestar_base = 19
    fourstar_base = 60
    threestar_base = 120
    twostar_base = 300
    onestar_base = 500

    fivestar_actual = fivestar_base + 0.2 * current_pity
    fourstar_actual = fivestar_actual + 3 * current_4star_pity + fourstar_base
    threestar_actual = fourstar_actual + threestar_base
    twostar_actual = threestar_actual + twostar_base - 0.2 * current_pity
    onestar_actual = twostar_actual + onestar_base - 3 * current_4star_pity  # always = 999

    print(f"Fivestar threshold : {fivestar_actual}")
    print(f"Fourstar threshold : {fourstar_actual}")
    print(f"Threestar threshold : {threestar_actual}")
    print(f"Pull : {pull}")

    if pull <= fivestar_actual:
        ret = 5
    elif pull <= fourstar_actual:
        ret = 4
    elif pull <= threestar_actual:
        ret = 3
    elif pull <= twostar_actual:
        ret = 2
    elif pull <= onestar_actual:
        ret = 1
    else:
        ret = 0
    return ret, from_pity


async def make_pull_embed(ctx: discord.ApplicationContext, number, max_number, star_rating, message):
    etoiles = "⭐" * star_rating
    print(etoiles)
    embed = discord.Embed(
        title=etoiles,
        color=discord.Colour.purple(),  # Pycord provides a class with default colors you can choose from
        description=message
    )
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text=f"Waifu #{number}/{max_number}")
    return embed



@bot.slash_command(
  name="pull",
  guild_ids=allowed_guilds,
  description="Pull 1 waifu"
)
async def pull_waifu(
        ctx: discord.ApplicationContext
):
    conn = make_connection()
    user = ctx.user.id
    pulls, last_pull, current_pity, current_4star_pity, essence = get_user(conn, user)
    print(pulls)
    print(last_pull)
    print(current_pity)
    print(current_4star_pity)
    print(essence)
    if pulls is None:
        reset_pulls(conn, user)
    last_pull_today = last_pull == datetime.now().date()
    if not last_pull_today:
        reset_pulls(conn, user)
        pulls = DAILY_PULLS
    if pulls == 0:
        await ctx.respond("Plus de pulls disponible aujourd'hui.")
    else:
        pull_rarity, from_pity = get_pull(current_pity, current_4star_pity)
        print(pull_rarity)
        nb_links = count_lines_rarity(conn, pull_rarity)
        chosen_link = random.randint(1, nb_links)
        link, star, link_id = get_link_rarity(conn, chosen_link, pull_rarity)

        lose_pull(conn, user, pulls)

        # INCREASE PITY COUNT BASED ON PULL RARITY
        if pull_rarity == 5:
            current_pity = 0
        else:
            current_pity += 1
        if pull_rarity == 4:
            current_4star_pity = 0
        else:
            current_4star_pity += 1

        update_pity(conn, user, current_4star_pity, current_pity)

        already_has = check_user_already_has(conn, user, link_id)
        if already_has:
            # gain essence based on rarity
            gained_essence = ESSENCE_GAIN[pull_rarity]
            print(f"Pull rarity : {pull_rarity}, essence gained : {gained_essence}")
            new_total = essence + gained_essence
            gain_essence(conn, user, new_total)
            message = f"Tu avais déjà cette waifu, tu gagnes donc à la place {gained_essence} essences!"
            if from_pity:
                message += "\nWaifu obtenue par hard pity"
            embed = await make_pull_embed(ctx, chosen_link, nb_links, star, message)
            file = discord.File(link, filename="image.png")
            await ctx.respond(file=file, embed=embed)
        else:
            register_pull(conn, user, link_id)
            message = f"Voici la waifu que tu as pull!"
            if from_pity:
                message += "\nWaifu obtenue par hard pity"
            embed = await make_pull_embed(ctx, chosen_link, nb_links, star, message)
            file = discord.File(link, filename="image.png")
            await ctx.respond(file=file, embed=embed)
    close_connection(conn)


bot.run(TOKEN)



print("Execution is over")

