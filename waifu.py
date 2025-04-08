from datetime import datetime
from discord.ext import commands
from discord.ui import Item, Button
import discord
import random
from db_connector import *
from constants import allowed_guilds, formula_calc_hp, formula_calc_stat, restricted_guilds

ESSENCE_GAIN = [1000, 10, 20, 50, 100, 200]
ESSENCE_COST = [10000, 40, 80, 200, 500, 1000]


class Waifu(commands.Cog):
    def __init__(self, setup_bot):  # this is a special method that is called when the cog is loaded
        self.bot = setup_bot

    async def make_embed(self, ctx: discord.ApplicationContext, number, max_number, star_rating, uploader,
                         hide_number = False):
        etoiles = "⭐" * int(star_rating)
        embed = discord.Embed(
            title=etoiles,
            color=discord.Colour.purple(),  # Pycord provides a class with default colors you can choose from
        )
        embed.set_image(url="attachment://image.png")
        print(uploader)
        if uploader is not None:
            uploader_user = await self.bot.fetch_user(uploader)
            print(uploader_user)
            embed.set_author(name=f"Uploaded by {uploader_user.name}", icon_url=uploader_user.avatar)
        if not hide_number:
            embed.set_footer(text=f"Waifu #{number}/{max_number}")
        return embed



    @discord.slash_command(
      name="random_waifu",
      guild_ids=allowed_guilds,
      description="Waifu random"
    )
    async def random_waifu(
            self,
            ctx: discord.ApplicationContext
    ):
        conn = make_connection()
        nb_links = count_lines(conn)
        chosen_link = random.randint(1, nb_links)
        link,uploader,star = get_link(conn, chosen_link)
        uploader = None
        embed = await self.make_embed(ctx, chosen_link, nb_links, star, uploader)
        close_connection(conn)
        file = discord.File(link, filename="image.png")
        await ctx.respond(file=file, embed=embed)



    class MyView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
        def __init__(self, waifu_instance, number, max_number, *items: Item):
            super().__init__(*items)
            self.number = int(number)
            self.max_number = int(max_number)
            self.set_button_states()
            self.waifu_instance = waifu_instance

        def set_button_states(self):
            button1 = self.get_item("left")
            button1.disabled = False
            button2 = self.get_item("right")
            button2.disabled = False
            if self.number == 1:
                button1.disabled = True
            if self.number == self.max_number:
                button2.disabled = True

        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⬅️", custom_id="left", disabled=True)
        async def first_button_callback(self, button, interaction):
            self.number -= 1
            self.set_button_states()

            conn = make_connection()
            link, uploader, star = get_link(conn, int(self.number))
            max_number = count_lines(conn)
            embed = await self.waifu_instance.make_embed(None, self.number, max_number, star, uploader)
            file = discord.File(link, filename="image.png")
            close_connection(conn)
            await self.message.edit(file=file, embed=embed, view=self.waifu_instance.MyView(self.waifu_instance, self.number, max_number))
            await interaction.response.edit_message(view=self)

        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="➡️", custom_id="right", disabled=True)
        async def second_button_callback(self, button, interaction):
            self.number += 1
            self.set_button_states()
            conn = make_connection()
            link, uploader, star = get_link(conn, int(self.number))
            max_number = count_lines(conn)
            embed = await self.waifu_instance.make_embed(None, self.number, max_number, star, uploader)
            file = discord.File(link, filename="image.png")
            close_connection(conn)
            await self.message.edit(file=file, embed=embed, view=self.waifu_instance.MyView(self.waifu_instance,
                                                                                            self.number, max_number))
            await interaction.response.edit_message(view=self)


    @discord.slash_command(
      name="waifu_from_number",
      guild_ids=allowed_guilds,
      description="Waifu à partir d'un numéro"
    )
    async def waifu_from_number(
            self,
            ctx: discord.ApplicationContext,
            number: discord.Option(input_type=discord.SlashCommandOptionType.integer, description="Numéro de la waifu", required=True)
    ):
        conn = make_connection()
        try:
            link, uploader, star = get_link(conn, int(number))
            max_number = count_lines(conn)
            embed = await self.make_embed(ctx, number, max_number, star, uploader)
            file = discord.File(link, filename="image.png")
            await ctx.respond(file=file, embed=embed, view=self.MyView(self, number, max_number))
            close_connection(conn)
        except Exception as e:
            print(e)
            close_connection(conn)
            await ctx.respond("Tant de nombres disponibles; et tu en choisis un qui n'est pas valide. C'est déplorable, mais digne de toi.")


    @discord.slash_command(
      name="random_waifu_from_user",
      guild_ids=allowed_guilds,
      description="Waifu random d'un utilisateur"
    )
    async def random_waifu_from_user(
            self,
            ctx: discord.ApplicationContext,
            user: discord.Option(input_type=discord.SlashCommandOptionType.mentionable, description="@Utilisateur", required=True)
    ):
        conn = make_connection()
        user = str(user).split('>')[0].split('@')[1]
        nb_links = count_lines_user(conn, user)
        chosen_link = random.randint(1, nb_links)
        link, star = get_link_user(conn, chosen_link, user)

        close_connection(conn)
        embed = await self.make_embed(ctx, chosen_link, nb_links, star, user)
        file = discord.File(link, filename="image.png")
        await ctx.respond(file=file, embed=embed)


    def get_pull(self, current_pity, current_4star_pity):
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


    async def make_pull_embed(self, ctx: discord.ApplicationContext, number, max_number, star_rating, message, pulls):
        etoiles = "⭐" * star_rating
        embed = discord.Embed(
            title=etoiles,
            color=discord.Colour.purple(),  # Pycord provides a class with default colors you can choose from
            description=message
        )
        embed.set_image(url="attachment://image.png")
        embed.set_footer(text=f"Waifu #{number}/{max_number}, nombre de pulls restants : {pulls}")
        return embed



    @discord.slash_command(
      name="pull",
      guild_ids=allowed_guilds,
      description="Pull 1 waifu"
    )
    async def pull_waifu(
            self,
            ctx: discord.ApplicationContext
    ):
        conn = make_connection()
        user = ctx.user.id
        pulls, last_pull, current_pity, current_4star_pity, essence = get_user(conn, user)
        if pulls is None:
            reset_pulls(conn, user)
        last_pull_today = last_pull == datetime.now().date()
        if not last_pull_today:
            reset_pulls(conn, user)
            pulls = DAILY_PULLS
        if pulls == 0:
            await ctx.respond("Plus de pulls disponible aujourd'hui.")
        else:
            pull_rarity, from_pity = self.get_pull(current_pity, current_4star_pity)
            nb_links = count_lines_rarity(conn, pull_rarity)
            chosen_link = random.randint(1, nb_links)
            link, star, link_id = get_link_rarity(conn, chosen_link, pull_rarity)
            pulls -= 1
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
                new_total = essence + gained_essence
                set_essence(conn, user, new_total)
                message = f"Tu avais déjà cette waifu, tu gagnes donc à la place {gained_essence} essences!"
                if from_pity:
                    message += "\nWaifu obtenue par hard pity"
                embed = await self.make_pull_embed(ctx, chosen_link, nb_links, star, message, pulls)
                file = discord.File(link, filename="image.png")
                await ctx.respond(file=file, embed=embed)
            else:
                register_pull(conn, user, link_id)
                message = f"Voici la waifu que tu as pull!"
                if from_pity:
                    message += "\nWaifu obtenue par hard pity"
                embed = await self.make_pull_embed(ctx, chosen_link, nb_links, star, message, pulls)
                file = discord.File(link, filename="image.png")
                await ctx.respond(file=file, embed=embed)
        close_connection(conn)


    class DexView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
        def __init__(self, waifu_instance, number, max_number, user, *items: Item):
            super().__init__(*items)
            self.number = int(number)
            self.max_number = int(max_number)
            self.user = user
            self.set_button_states()
            self.waifu_instance = waifu_instance

        def set_button_states(self):
            button1 = self.get_item("left")
            button1.disabled = False
            button2 = self.get_item("right")
            button2.disabled = False
            button_select = self.get_item("select")
            button_select.disabled = False
            button_party = self.get_item("party")
            button_party.disabled = False
            if self.number == 1:
                button1.disabled = True
            if self.number == self.max_number:
                button2.disabled = True
            print("aa")
            conn = make_connection()
            link, uploader, star, link_id = get_link_dex(conn, int(self.number), self.user)
            selected_id = get_currently_selected_waifu(conn, self.user)
            if selected_id == link_id:
                button_select.disabled = True
            party_waifus = get_waifu_in_current_party(conn, self.user)
            if check_user_in_dungeon(conn, self.user) or link_id in party_waifus or star <= 3:
                button_party.disabled = True
            close_connection(conn)

        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⬅️", custom_id="left", disabled=True)
        async def first_button_callback(self, button, interaction):
            self.number -= 1
            self.set_button_states()

            conn = make_connection()
            link, uploader, star, link_id = get_link_dex(conn, int(self.number), self.user)
            max_number = count_lines_dex(conn, self.user)
            embed = await self.waifu_instance.make_embed(None, self.number, max_number, star, uploader)
            file = discord.File(link, filename="image.png")
            close_connection(conn)
            await self.message.edit(file=file, embed=embed, view=self.waifu_instance.DexView(self.waifu_instance,
                                                                                             self.number,
                                                                                             max_number,
                                                                                             self.user))
            await interaction.response.edit_message(view=self)


        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⭐", custom_id="select", disabled=True)
        async def select_waifu_callback(self, button, interaction):
            await interaction.response.defer()
            if interaction.user.id == self.user:
                conn = make_connection()

                link, uploader, star, link_id = get_link_dex(conn, int(self.number), self.user)

                select_waifu(conn, link_id, self.user)

                self.set_button_states()

                max_number = count_lines_dex(conn, self.user)
                embed = await self.waifu_instance.make_embed(None, self.number, max_number, star, uploader)
                file = discord.File(link, filename="image.png")
                close_connection(conn)
                await interaction.edit_original_response(file=file, embed=embed,
                                                         view=self.waifu_instance.DexView(
                                                             self.waifu_instance,
                                                             self.number,
                                                             max_number,
                                                             self.user))

                await interaction.followup.send(f"Waifu sélectionnée!", ephemeral=True)
            else:
                await interaction.followup.send(f"Vous ne pouvez pas sélectionner une waifu pour quelqu'un d'autre!",
                                                ephemeral=True)


        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔰", custom_id="party", disabled=True)
        async def add_waifu_to_party_callback(self, button, interaction):
            await interaction.response.defer()
            if interaction.user.id == self.user:
                conn = make_connection()

                if not check_user_in_dungeon(conn, user=self.user):

                    link, uploader, star, link_id = get_link_dex(conn, int(self.number), self.user)

                    add_waifu_to_party(conn, link_id, self.user)

                    self.set_button_states()

                    max_number = count_lines_dex(conn, self.user)
                    embed = await self.waifu_instance.make_embed(None, self.number, max_number, star, uploader)
                    file = discord.File(link, filename="image.png")
                    close_connection(conn)
                    await interaction.edit_original_response(file=file, embed=embed,
                                                             view=self.waifu_instance.DexView(
                                                                 self.waifu_instance,
                                                                 self.number,
                                                                 max_number,
                                                                 self.user))

                    await interaction.followup.send(f"Waifu ajoutée au groupe!", ephemeral=True)
                else :
                    await interaction.followup.send(
                    f"Vous ne pouvez pas changer les waifus de votre groupe en plein donjon!",
                    ephemeral=True)
            else:
                await interaction.followup.send(f"Vous ne pouvez pas ajouter la waifu d'un autre joueur à votre groupe!",
                                                ephemeral=True)


        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="➡️", custom_id="right", disabled=True)
        async def second_button_callback(self, button, interaction):
            self.number += 1
            self.set_button_states()
            conn = make_connection()
            link, uploader, star, link_id = get_link_dex(conn, int(self.number), self.user)
            max_number = count_lines_dex(conn, self.user)
            embed = await self.waifu_instance.make_embed(None, self.number, max_number, star, uploader)
            file = discord.File(link, filename="image.png")
            close_connection(conn)
            await self.message.edit(file=file, embed=embed, view=self.waifu_instance.DexView(self.waifu_instance,
                                                                                             self.number, max_number,
                                                                                             self.user))
            await interaction.response.edit_message(view=self)


    @discord.slash_command(
      name="waifudex",
      guild_ids=allowed_guilds,
      description="Votre waifudex, à partir de ce que vous avez pull"
    )
    async def waifudex(
            self,
            ctx: discord.ApplicationContext,
            number: discord.Option(input_type=discord.SlashCommandOptionType.integer,
                                   description="Numéro de la waifu",
                                   required=False
                                   ) = 1
    ):
        conn = make_connection()
        try:
            user = ctx.user.id
            link, uploader, star, link_id = get_link_dex(conn, int(number), user)
            max_number = count_lines_dex(conn, user)
            embed = await self.make_embed(ctx, number, max_number, star, uploader)
            file = discord.File(link, filename="image.png")
            await ctx.respond(file=file, embed=embed, view=self.DexView(self, number, max_number, user))
            close_connection(conn)
        except Exception as e:
            print(e)
            close_connection(conn)
            await ctx.respond("Tant de nombres disponibles; et tu en choisis un qui n'est pas valide. C'est déplorable, mais digne de toi.")


    async def make_pull_embed_shop(self, ctx: discord.ApplicationContext, star_rating, message):
        etoiles = "⭐" * star_rating
        embed = discord.Embed(
            title=etoiles,
            color=discord.Colour.purple(),  # Pycord provides a class with default colors you can choose from
            description=message
        )
        embed.set_image(url="attachment://image.png")
        return embed



    class EssenceView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
        def __init__(self, waifu_instance, essence, user, *items: Item):
            super().__init__(*items)
            self.essence = int(essence)
            self.set_button_states()
            self.user = user
            self.waifu_instance = waifu_instance

        def set_button_states(self):
            button1 = self.get_item("5star")
            button1.disabled = False
            button2 = self.get_item("4star")
            button2.disabled = False
            button3 = self.get_item("3star")
            button3.disabled = False
            button4 = self.get_item("2star")
            button4.disabled = False
            button5 = self.get_item("1star")
            button5.disabled = False
            if self.essence < ESSENCE_COST[5]:
                button1.disabled = True
            if self.essence < ESSENCE_COST[4]:
                button2.disabled = True
            if self.essence < ESSENCE_COST[3]:
                button3.disabled = True
            if self.essence < ESSENCE_COST[2]:
                button4.disabled = True
            if self.essence < ESSENCE_COST[1]:
                button5.disabled = True


        async def handle_button(self, pull_rarity, interaction):
            if self.essence >= ESSENCE_COST[pull_rarity]:
                conn = make_connection()

                link_ids = get_all_link_rarity_unobtained(conn, pull_rarity, self.user)

                await interaction.response.defer()

                if len(link_ids) > 0:
                    chosen_link = random.choice(link_ids)

                    link_id, link_url = chosen_link

                    self.essence -= ESSENCE_COST[pull_rarity]

                    set_essence(conn, self.user, self.essence)

                    register_pull(conn, self.user, link_id)
                    message = f"Voici la waifu que tu as obtenu en dépensant tes {ESSENCE_COST[pull_rarity]} essences!"
                    embed = await self.waifu_instance.make_pull_embed_shop(None, pull_rarity, message)
                    file = discord.File(link_url, filename="image.png")
                    await interaction.followup.send(file=file, embed=embed)
                else:
                    await interaction.followup.send(f"Tu n'as plus de waifus de rareté {pull_rarity}⭐ à obtenir", ephemeral=True)

                display_embed = self.waifu_instance.shop_embed(self.essence)

                self.set_button_states()
                await interaction.edit_original_response(view=self, embed=display_embed)

                close_connection(conn)

        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⭐", custom_id="5star", disabled=True, label="5")
        async def five_star_callback(self, button, interaction):
            pull_rarity = 5
            await self.handle_button(pull_rarity, interaction)

        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⭐", custom_id="4star", disabled=True, label="4")
        async def four_star_callback(self, button, interaction):
            pull_rarity = 4
            await self.handle_button(pull_rarity, interaction)

        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⭐", custom_id="3star", disabled=True, label="3")
        async def three_star_callback(self, button, interaction):
            pull_rarity = 3
            await self.handle_button(pull_rarity, interaction)

        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⭐", custom_id="2star", disabled=True, label="2")
        async def two_star_callback(self, button, interaction):
            pull_rarity = 2
            await self.handle_button(pull_rarity, interaction)

        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⭐", custom_id="1star", disabled=True, label="1")
        async def one_star_callback(self, button, interaction):
            pull_rarity = 1
            await self.handle_button(pull_rarity, interaction)


    def shop_embed(self, essence_count):
        embed = discord.Embed(
            title="Shop à essences",
            color=discord.Colour.purple(),  # Pycord provides a class with default colors you can choose from
            description="Bienvenue dans le shop à essences, où tu peux dépenser les essences obtenues "
                        "lorsque tu pull une waifu en doublon, pour des pulls supplémentaires à rareté garantie!"
        )
        embed.add_field(name="**Pull ⭐⭐⭐⭐⭐**", value=f"{ESSENCE_COST[5]} essences", inline=True)
        embed.add_field(name="**Pull ⭐⭐⭐⭐**", value=f"{ESSENCE_COST[4]} essences", inline=True)
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="**Pull ⭐⭐⭐**", value=f"{ESSENCE_COST[3]} essences", inline=True)
        embed.add_field(name="**Pull ⭐⭐**", value=f"{ESSENCE_COST[2]} essences", inline=True)
        embed.add_field(name="**Pull ⭐**", value=f"{ESSENCE_COST[1]} essences", inline=False)

        embed.set_footer(text=f"Nombre d'essences en possession actuellement : {essence_count}")

        return embed


    @discord.slash_command(
      name="essence_shop",
      guild_ids=allowed_guilds,
      description="Magasin pour dépenser les essences obtenues par pull"
    )
    async def essence_shop(
            self,
            ctx: discord.ApplicationContext,
    ):
        conn = make_connection()
        try:
            user = ctx.user.id
            essence_count = get_essence_count(conn, user)

            embed = self.shop_embed(essence_count)

            await ctx.respond(view=self.EssenceView(self, essence_count, user), ephemeral=True, embed=embed)
            close_connection(conn)
        except Exception as e:
            print(e)
            close_connection(conn)
            await ctx.respond("Tant de nombres disponibles; et tu en choisis un qui n'est pas valide. C'est déplorable, mais digne de toi.")



    class RankedView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
        def __init__(self, waifu_instance, number, max_number, rank, *items: Item):
            super().__init__(*items)
            self.number = int(number)
            self.max_number = int(max_number)
            self.rank = rank
            self.set_button_states()
            self.waifu_instance = waifu_instance

        def set_button_states(self):
            button1 = self.get_item("left")
            button1.disabled = False
            button2 = self.get_item("right")
            button2.disabled = False
            if self.number == 1:
                button1.disabled = True
            if self.number == self.max_number:
                button2.disabled = True

        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⬅️", custom_id="left", disabled=True)
        async def first_button_callback(self, button, interaction):
            self.number -= 1
            self.set_button_states()

            conn = make_connection()
            link, uploader, link_id = get_link_rarity_uploader(conn, int(self.number), self.rank)
            max_number = count_lines_rarity(conn, self.rank)
            embed = await self.waifu_instance.make_embed(None, self.number, max_number, self.rank, uploader)
            file = discord.File(link, filename="image.png")
            close_connection(conn)
            await self.message.edit(file=file, embed=embed, view=self.waifu_instance.RankedView(self.waifu_instance,
                                                                                                self.number,
                                                                                                max_number, self.rank))
            await interaction.response.edit_message(view=self)

        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="➡️", custom_id="right", disabled=True)
        async def second_button_callback(self, button, interaction):
            self.number += 1
            self.set_button_states()
            conn = make_connection()
            link, uploader, link_id = get_link_rarity_uploader(conn, int(self.number), self.rank)
            max_number = count_lines_rarity(conn, self.rank)
            embed = await self.waifu_instance.make_embed(None, self.number, max_number, self.rank, uploader)
            file = discord.File(link, filename="image.png")
            close_connection(conn)
            await self.message.edit(file=file, embed=embed, view=self.waifu_instance.RankedView(self.waifu_instance,
                                                                                                self.number, max_number,
                                                                                                self.rank))
            await interaction.response.edit_message(view=self)


    @discord.slash_command(
      name="waifu_from_rank",
      guild_ids=allowed_guilds,
      description="Waifu à partir d'un nombre d'étoiles"
    )
    async def waifu_from_rank(
            self,
            ctx: discord.ApplicationContext,
            rank: discord.Option(
                input_type=discord.SlashCommandOptionType.integer, description="Nombre d'étoiles", required=True
            ),
            number: discord.Option(
                input_type=discord.SlashCommandOptionType.integer, description="Numéro de la waifu", required=False
            ) = 1
    ):
        conn = make_connection()
        try:
            link, uploader, link_id = get_link_rarity_uploader(conn, int(number), rank)
            max_number = count_lines_rarity(conn, rank)
            print("test")
            embed = await self.make_embed(ctx, number, max_number, rank, uploader)
            print("test2")
            file = discord.File(link, filename="image.png")
            await ctx.respond(file=file, embed=embed, view=self.RankedView(self, number, max_number, rank))
            close_connection(conn)
        except Exception as e:
            print(e)
            close_connection(conn)
            await ctx.respond("Tant de nombres disponibles; et tu en choisis un qui n'est pas valide. C'est déplorable, mais digne de toi.")





    async def make_trade_chat_embed(self, user1, user2, status1, status2):
        embed = discord.Embed(
            title="Accepter l'échange ?",
            color=discord.Colour.purple(),
            description=f"<@{user1}> \t : {status1}\n"
                        f"<@{user2}> \t : {status2}"
        )
        return embed


    async def make_trade_chat_embed_done(self, message):
        embed = discord.Embed(
            title="Échange terminé!",
            color=discord.Colour.purple(),
            description=message
        )
        return embed


    class TradeView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
        def __init__(self, waifu_instance, user1, user2, user1_accepted, user2_accepted, items_exist, *items: Item):
            super().__init__(*items)
            self.user1 = int(user1)
            self.user2 = int(user2)
            self.user1_accepted = user1_accepted
            self.user2_accepted = user2_accepted
            if not items_exist:
                self.clear_items()
            self.waifu_instance = waifu_instance


        def check_valid_user(self, interaction):
            return interaction.user.id in (self.user1, self.user2)


        def both_users_accepted(self):
            return self.user1_accepted and self.user2_accepted


        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="✅", custom_id="accept")
        async def accept(self, button, interaction):
            if self.check_valid_user(interaction):
                if interaction.user.id == self.user1:
                    self.user1_accepted = True
                else:
                    self.user2_accepted = True

                if self.both_users_accepted():
                    conn = make_connection()
                    waifu1 = get_currently_selected_waifu(conn, self.user1)
                    waifu2 = get_currently_selected_waifu(conn, self.user2)
                    register_pull(conn, self.user1, waifu2)
                    register_pull(conn, self.user2, waifu1)
                    remove_waifu_from_user(conn, self.user1, waifu1)
                    remove_waifu_from_user(conn, self.user2, waifu2)
                    select_waifu(conn, None, self.user1)
                    select_waifu(conn, None, self.user2)
                    close_connection(conn)

                    embed = await self.waifu_instance.make_trade_chat_embed_done("Les waifus ont été échangées.")

                    new_view = self.waifu_instance.TradeView(self.waifu_instance, self.user1, self.user2,
                                         self.user1_accepted, self.user2_accepted, False)

                    await self.message.edit(embed=embed,
                                            view=new_view)
                    await interaction.response.edit_message(view=new_view)
                else:
                    pending_message = "En attente"
                    validated_message = "Validé"
                    if self.user1_accepted:
                        message1 = validated_message
                    else:
                        message1 = pending_message

                    if self.user2_accepted:
                        message2 = validated_message
                    else:
                        message2 = pending_message
                    embed = await self.waifu_instance.make_trade_chat_embed(self.user1, self.user2, message1, message2)


                    new_view = self.waifu_instance.TradeView(self.waifu_instance, self.user1, self.user2,
                                         self.user1_accepted, self.user2_accepted, True)

                    await self.message.edit(embed=embed,
                                            view=new_view)
                    await interaction.response.edit_message(view=new_view)


        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="❌", custom_id="refuse")
        async def refuse(self, button, interaction):
            if self.check_valid_user(interaction):
                embed = await self.waifu_instance.make_trade_chat_embed_done("L'échange a été refusé.")

                new_view = self.waifu_instance.TradeView(self.waifu_instance, self.user1, self.user2,
                                                       self.user1_accepted, self.user2_accepted, False)

                await self.message.edit(embed=embed,
                                        view=new_view)
                await interaction.response.edit_message(view=new_view)

    async def make_trade_embed(self, star_rating, message):
        etoiles = "⭐" * star_rating
        embed = discord.Embed(
            title=etoiles,
            color=discord.Colour.purple(),
            description=message
        )
        embed.set_image(url="attachment://image.png")
        return embed


    @discord.slash_command(
      name="trade",
      guild_ids=allowed_guilds,
      description="Permet d'échanger des waifus avec un utilisateur"
    )
    async def trade(
            self,
            ctx: discord.ApplicationContext,
            pinged_user: discord.Option(input_type=discord.SlashCommandOptionType.mentionable,
                                 description="@Utilisateur",
                                 required=True)
    ):
        conn = make_connection()
        try:
            my_user_id = ctx.user.id
            pinged_user_id = str(pinged_user).split('>')[0].split('@')[1]

            my_selected = get_currently_selected_waifu(conn, my_user_id)

            if int(pinged_user_id) == my_user_id:
                await ctx.respond("Vous ne pouvez pas échanger avec vous-même!",
                                  ephemeral=True)
                return

            if my_selected is None:
                await ctx.respond("Sélectionnez une waifu dans votre waifudex avant de lancer cette commande!",
                                  ephemeral=True)
                return

            their_selected = get_currently_selected_waifu(conn, pinged_user_id)

            if their_selected is None:
                await ctx.respond("L'utilisateur mentionné n'a pas sélectionné de waifu dans son waifudex")
                return

            if check_user_already_has(conn, my_user_id, their_selected):
                await ctx.respond("Vous avez déjà la waifu sélectionnée par cette personne.",
                                  ephemeral=True)
                return

            if check_user_already_has(conn, pinged_user_id, my_selected):
                await ctx.respond("Cette personne a déjà la waifu que vous avez sélectionnée.",
                                  ephemeral=True)
                return

            my_waifu_url, my_waifu_star = get_waifu_by_id(conn, my_selected)

            message = f"Voici la waifu sélectionnée par <@{my_user_id}>"
            embed = await self.make_trade_embed(my_waifu_star, message)
            file = discord.File(my_waifu_url, filename="image.png")
            await ctx.respond(file=file, embed=embed)

            their_waifu_url, their_waifu_star = get_waifu_by_id(conn, their_selected)

            message = f"Voici la waifu sélectionnée par <@{pinged_user_id}>"
            embed = await self.make_trade_embed(their_waifu_star, message)
            file = discord.File(their_waifu_url, filename="image.png")
            await ctx.respond(file=file, embed=embed)

            default_status = "En attente"

            trade_chat_embed = await self.make_trade_chat_embed(my_user_id, pinged_user_id, default_status, default_status)

            await ctx.respond(embed=trade_chat_embed, view=self.TradeView(self,
                                                                     my_user_id,
                                                                     pinged_user_id,
                                                                     False,
                                                                     False,
                                                                     True))
        except Exception as e:
            print(e)
            await ctx.respond("Une erreur est survenue.",
                              ephemeral=True)
        finally:
            close_connection(conn)

    async def make_party_embed(self, star_rating, hp, atk, defense, speed, bonus_hit, bonus_dodge, dungeon_class, level):
        etoiles = "⭐" * star_rating
        if dungeon_class == 1:
            classe = "Healer"
        else:
            classe = "Mage"
        embed = discord.Embed(
            title=etoiles,
            color=discord.Colour.purple(),
            description=f"Classe : {classe} niveau {level}"
        )
        embed.add_field(name="HPs", value=hp)
        embed.add_field(name="Attaque", value=atk)
        embed.add_field(name="Défense", value=defense)
        embed.add_field(name="Vitesse", value=speed)
        embed.add_field(name="Bonus pour toucher", value=bonus_hit)
        embed.add_field(name="Bonus pour esquiver", value=bonus_dodge)
        embed.set_image(url="attachment://image.png")
        return embed

    @discord.slash_command(
        name="party",
        guild_ids=restricted_guilds,
        description="Affiche le groupe actuel"
    )
    async def party(
            self,
            ctx: discord.ApplicationContext
    ):
        conn = make_connection()
        try:
            user = ctx.user.id

            waifu_list = get_waifu_in_current_party_with_level(conn, user)

            if len(waifu_list) > 0:
                for waifu_id, waifu_level in waifu_list:
                    link, star, base_hp, base_atk, base_def, base_speed, bonus_hit, bonus_dodge, dungeon_class\
                        = get_party_waifu_by_id(conn, waifu_id)

                    hp, atk, defense, speed = (formula_calc_hp(base_hp, waifu_level),
                                               formula_calc_stat(base_atk, waifu_level),
                                               formula_calc_stat(base_def, waifu_level),
                                               formula_calc_stat(base_speed, waifu_level))

                    embed = await self.make_party_embed(star, hp, atk, defense, speed,
                                                        bonus_hit, bonus_dodge, dungeon_class, waifu_level)
                    file = discord.File(link, filename="image.png")
                    await ctx.respond(file=file, embed=embed)
            else:
                await ctx.respond("Vous n'avez pas de waifu dans votre groupe.", ephemeral=True)
            close_connection(conn)
        except Exception as e:
            print(e)
            close_connection(conn)


    class RevealUserView(discord.ui.View): # Create a class called RevealUserView that subclasses discord.ui.View
        def __init__(self, waifu_instance, number, max_number, uploader, *items: Item):
            super().__init__(*items)
            self.waifu_instance = waifu_instance
            self.number = number
            self.max_number = max_number
            self.uploader = uploader

        @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔎", custom_id="reveal", disabled=False)
        async def show_uploader(self, button, interaction):
            conn = make_connection()
            link, uploader, star = get_link(conn, int(self.number))
            embed = await self.waifu_instance.make_embed(None, self.number, self.max_number, star, self.uploader)
            file = discord.File(link, filename="image.png")
            close_connection(conn)
            await self.message.edit(file=file, embed=embed, view=None)

            await interaction.response.edit_message(view=None)


    @discord.slash_command(
        name="random_waifu_game",
        guild_ids=allowed_guilds,
        description="Jeu utilisant les waifus random"
    )
    async def random_waifu_game(
            self,
            ctx: discord.ApplicationContext
    ):
        conn = make_connection()
        nb_links = count_lines(conn)
        chosen_link = random.randint(1, nb_links)
        link, uploader, star = get_link(conn, chosen_link)
        embed = await self.make_embed(ctx, chosen_link, nb_links, star, None, True)
        close_connection(conn)
        file = discord.File(link, filename="image.png")
        await ctx.respond(file=file, embed=embed, view=self.RevealUserView(self, chosen_link, nb_links, uploader))


def setup(bot_setup):
    bot_setup.add_cog(Waifu(bot_setup))
