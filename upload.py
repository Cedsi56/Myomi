import os
import discord
from discord.ext import commands
from discord import option
import requests
image_formats = ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif")
from db_connector import make_connection, get_next_id, close_connection, insert_into_db


class Upload(commands.Cog):
    def __init__(self, setup_bot):  # this is a special method that is called when the cog is loaded
        self.bot = setup_bot

    def is_url_image(self, image_url):
       r = requests.head(image_url)
       print(r.headers["content-type"])
       if r.headers["content-type"] in image_formats:
          return True
       return False


    def save_url(self, image_url, ctx: discord.ApplicationContext, star = 1):
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
                fp.write(response.content)
            print("Image downloaded successfully.")
            insert_into_db(conn, user, file, star)
            conn.commit()
        else:
            print(f"Failed to download the image. Status code: {response.status_code}")

        close_connection(conn)


    @discord.slash_command(
      name="waifu_upload_url",
      description="Upload d'une image de waifu par URL"
    )
    async def waifu_upload_url(
            self,
            ctx: discord.ApplicationContext,
            url: discord.Option(input_type=discord.SlashCommandOptionType.string, description="URL de l'image", required=True),
            star: discord.Option(input_type=discord.SlashCommandOptionType.integer, description="Nombre d'étoiles", required=False)
    ):
        try:
            if self.is_url_image(url):
                self.save_url(url, ctx, star)
                await ctx.respond("Fichier uploadé!")
                return
        except Exception as e:
            print(e)
            pass
        await ctx.respond("Ton incompétence est vraiment digne des invalides. "
                          "Ajoute l'URL d'une image valide à ton message si tu veux qu'elle soit ajoutée.")




    @discord.slash_command(
      name="waifu_upload_file",
      description="Upload d'une image de waifu par fichier"
    )
    @option(
        "file",
        discord.Attachment,
        description="Fichier à upload",
        required=True,  # The default value will be None if the user doesn't provide a file.
    )
    async def waifu_upload_fichier(
            self,
            ctx: discord.ApplicationContext,
            file: discord.Attachment,
            star: discord.Option(input_type=discord.SlashCommandOptionType.integer, description="Nombre d'étoiles", required=False)
    ):
        try:
            if file:
                if file.content_type in image_formats:
                    self.save_url(file.url, ctx, star)
                    await ctx.respond("Fichier uploadé!")
                    return
        except:
            pass
        await ctx.respond("Ton incompétence est vraiment digne des invalides. "
                              "Attache une image valide à ton message si tu veux qu'elle soit ajoutée.")


def setup(bot_setup):
    bot_setup.add_cog(Upload(bot_setup))
