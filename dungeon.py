import math
import random

from discord.ext import commands
import discord
from discord.ui import Item, Select

from constants import *
from db_connector import *

DUNGEON_ROOMS=[
    (0, "Combat"),
    (1, "Combat difficile"),
    (2, "Coffre"),
    (3, "Coffre"), # MIMIC
    (4, "Piège magique"),
    (5, "Salle vide"),
    (6, "Évènement"),
    (7, "Boutique"), # [Uniquement si PO sur soi]
    (8, "Salle de boss") # [Fond du donjon uniquement]
]



async def dungeon_choice_embed(choice1, choice2 = None, choice3 = None, choice4 = None):
    if choice2 is None:
        nb_chemins = "trouve un chemin"
    elif choice3 is None:
        nb_chemins = "trouvent deux chemins"
    elif choice4 is None:
        nb_chemins = "trouvent trois chemins"
    else:
        nb_chemins = "trouvent quatre chemins"

    msg = f"Devant vous se {nb_chemins}.\n\n"
    if choice2 is None:
        msg += f"Dans ce seul chemin, vous trouverez {choice1}."
    else:
        msg += f"Dans le premier chemin, vous trouverez {choice1}.\n\n"
        msg += f"Dans le deuxième chemin, vous trouverez {choice2}.\n\n"
        if choice3 is not None:
            msg += f"Dans le troisième chemin, vous trouverez {choice3}.\n\n"
            if choice4 is not None:
                msg += f"Dans le quatrième chemin, vous trouverez {choice4}.\n\n"
    embed = discord.Embed(
        color=discord.Colour.purple(),
        description=msg
    )
    return embed



def calculate_seed(seed, n):
    mod = 1 + 2**16
    mult = 76
    inc = 74
    for i in range(n):
        seed = (mult * seed + inc) % mod
    return seed


def next_seed(seed):
    return calculate_seed(seed, 1)


def generate_choices(seed, floor, has_gold, has_scout):
    choice1, choice2, choice3, choice4 = None, None, None, None
    if floor == 5:
        choice1 = DUNGEON_ROOMS[8]
        room_count = 1
    else:
        choices = [None, None, None, None]
        num_rooms_visible = 2
        if has_scout:
            num_rooms_visible += 1

        actual_seed = calculate_seed(seed, floor)

        # Generate number of rooms

        lowest_digit = actual_seed % 10
        if lowest_digit < 2:
            room_count = 2
        elif lowest_digit < 5:
            room_count = 3
        else:
            room_count = 4

        # Generate rooms

        actual_seed = next_seed(actual_seed)

        generated_room = actual_seed % room_count

        has_generated_shop = False

        for i in range(room_count):
            actual_seed = next_seed(actual_seed)
            mod = 90
            if has_gold and not has_generated_shop:
                mod += 20
            lowest_digits = actual_seed % mod

            if lowest_digits < 40 :
                chosen_room = 0
            elif lowest_digits < 45:
                chosen_room = 1
            elif lowest_digits < 55:
                chosen_room = 2
            elif lowest_digits < 60:
                chosen_room = 3
            elif lowest_digits < 70:
                chosen_room = 4
            elif lowest_digits < 80:
                chosen_room = 5
            elif lowest_digits < 90:
                chosen_room = 6
            else:
                chosen_room = 7
                has_generated_shop = True

            actual_choice = DUNGEON_ROOMS[chosen_room]

            if num_rooms_visible > 0:
                num_rooms_visible -= 1
            else:
                actual_choice = (actual_choice[0], "quelque chose d'inconnu")

            choices[generated_room] = actual_choice


            generated_room = (generated_room + 1) % room_count

        choice1, choice2, choice3, choice4 = choices

    return choice1, choice2, choice3, choice4, room_count


async def make_initiative_embed(your_initiative, enemy_initiative):

    if your_initiative >= enemy_initiative:
        msg = "Vous frappez en premier!"
    else:
        msg = "Vous frappez en deuxième, préparez-vous à subir une attaque"

    embed = discord.Embed(
        color=discord.Colour.purple(),
        description=msg
    )
    embed.add_field(name="Votre initiative", value = your_initiative)
    embed.add_field(name="Initiative adverse", value=enemy_initiative)
    embed.set_image(url="attachment://image.png")
    return embed


async def make_turn_embed(enemy, party, msg):

    embed = discord.Embed(
        color=discord.Colour.purple(),
        description=msg
    )
    car_has_hp = "█"
    car_no_hp = "▒"
    max_car = 10

    percentage_health = enemy.cur_hp / enemy.max_hp
    num_has_hp_car = 1 + int(9 * percentage_health)
    num_no_hp_car = min(10, max_car - num_has_hp_car)
    msg_ennemi = car_has_hp * num_has_hp_car + car_no_hp * num_no_hp_car
    embed.add_field(name="HPs ennemi", value = msg_ennemi, inline=False)
    for p in party:
        p_class = CLASSES_EMOJIS[p.dungeon_class]
        percentage_health = p.cur_hp / p.max_hp
        if percentage_health > 0:
            num_has_hp_car = 1 + int(9 * percentage_health)
            num_no_hp_car = min(10, max_car - num_has_hp_car)
        else:
            num_has_hp_car = 0
            num_no_hp_car = 10
        msg_p = car_has_hp * num_has_hp_car + car_no_hp * num_no_hp_car
        embed.add_field(name=f"HPs {p_class}", value=msg_p, inline=False)
    return embed


def calculate_initative(enemy, party, seed):
    cumulative_speed = 0
    for w in party:
        cumulative_speed += w.speed

    print(cumulative_speed)
    your_initiative_bonus = int(math.sqrt(cumulative_speed) + cumulative_speed / 30)
    seed = next_seed(seed)
    if seed % 15 < cumulative_speed % 15:
        your_initiative_bonus += 1

    enemy.speed *= 3
    enemy_initiative_bonus = int(math.sqrt(enemy.speed) + enemy.speed / 30)
    seed = next_seed(seed)
    if seed % 15 < enemy.speed % 15:
        enemy_initiative_bonus += 1

    seed = next_seed(seed)
    your_initiative = 1 + (seed % 20) + your_initiative_bonus
    seed = next_seed(seed)
    enemy_initiative = 1 + (seed % 20) + enemy_initiative_bonus
    return your_initiative, enemy_initiative, seed


def rotate_party_left(party):
    party[0], party[1], party[2] = party[1], party[2], party[0]


def rotate_party_right(party):
    party[0], party[1], party[2] = party[2], party[0], party[1]


async def start_battle(floor, battle_type, seed, party, interaction: discord.Interaction):
    # consomme potions si nécessaire
    conn = make_connection()
    # génère l'ennemi et son niveau
    # BOSS BATTLE
    if battle_type == 8:
        star_power = 5
    else:
        star_power = 1 + int(floor / 3) + battle_type
        if seed % 100 > 90:
            star_power += 1
        star_power = min(4, star_power)

    print(star_power, star_power)
    seed = next_seed(seed)

    available_enemies = get_all_link_rarity(conn, star_power)
    number_options = len(available_enemies)
    choice = seed % number_options
    url, base_hp, base_atk, base_def, base_speed, bonus_hit, bonus_dodge =(
        get_enemy_waifu_by_id(conn, available_enemies[choice]))

    seed = next_seed(seed)

    level = 10 + (seed % 5) + (battle_type % 3) * 5

    hp, atk, defense, speed = (formula_calc_hp(base_hp, level),
                               formula_calc_stat(base_atk, level),
                               formula_calc_stat(base_def, level),
                               formula_calc_stat(base_speed, level))
    print("STATS")
    if star_power == 5:
        hp *= 3
    else:
        hp *= 2
    print(url, hp, atk, defense, speed, level)

    enemy = CombatWaifu(hp, hp, atk, defense, speed, bonus_hit, bonus_dodge, level, available_enemies[choice])

    # initiative
    your_initiative, enemy_initiative, seed = calculate_initative(enemy, party, seed)

    file = discord.File(url, filename="image.png")
    embed = await make_initiative_embed(your_initiative, enemy_initiative)
    await interaction.followup.send(file=file, embed=embed, ephemeral=True)

    if enemy_initiative > your_initiative:
        msg = await play_enemy_turn(enemy, party, seed, interaction, True)
    else:
        msg = f"C'est à votre tour d'attaquer."
    turn_embed = await make_turn_embed(enemy, party, msg)
    await interaction.followup.send(embed=turn_embed, ephemeral=True, view = CombatInputView(enemy, party,
                                                                                             interaction.user.id, seed))
    close_connection(conn)


async def play_enemy_turn(enemy, party, seed, interaction: discord.Interaction, first_turn = False):
    seed = next_seed(seed)
    hit_target = party[seed % len(party)]

    if hit_target.cur_hp <= 0:
        hit_target = party[0]

    enemy_hit = enemy.bonus_hit
    target_dodge = hit_target.bonus_dodge
    seed = next_seed(seed)

    if (seed % 20) + enemy_hit - target_dodge > 10:
        msg = f"L'ennemi attaque {CLASSES_EMOJIS[hit_target.dungeon_class]}!"
        enemy.attack_waifu(BASE_POWER, hit_target)

        if hit_target.cur_hp <= 0:
            msg += f"{CLASSES_EMOJIS[hit_target.dungeon_class]} tombe à terre!"

            if hit_target == party[0]:
                # try to find another leader
                if party[1].cur_hp > 0:
                    rotate_party_left(party)
                elif party[2].cur_hp > 0:
                    rotate_party_right(party)
                else:
                    # lose the battle
                    print("battle is lost!")
    else:
        msg = f"L'ennemi attaque {CLASSES_EMOJIS[hit_target.dungeon_class]} mais rate!"

    if not first_turn:
        turn_embed = await make_turn_embed(enemy, party, msg)
        await interaction.followup.send(embed=turn_embed, ephemeral=True, view=CombatInputView(enemy, party,
                                                                                               interaction.user.id, seed))
    return msg



class CombatInputView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
    def __init__(self, enemy, party, user, seed, *items: Item):
        super().__init__(*items)
        self.enemy = enemy
        self.party = party
        self.user = user
        self.seed = seed

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⚔️", custom_id="normal_attack")
    async def normal_attack_callback(self, button, interaction):
        if interaction.user.id == self.user:
            await interaction.response.defer()
            await interaction.followup.edit_message(interaction.message.id, view=None)
            power = BASE_POWER
            msg = "LOSS"
            for p in self.party:
                if p.cur_hp > 0:
                    p_hit = p.bonus_hit
                    enemy_dodge = self.enemy.bonus_dodge

                    self.seed = next_seed(self.seed)

                    if (self.seed % 20) + p_hit - enemy_dodge > 10:
                        if p == self.party[0]:
                            msg = "Vous attaquez l'ennemi avec une attaque normale!"
                        p.attack_waifu(power, self.enemy)
                    else:
                        if p == self.party[0]:
                            msg = "Vous attaquez l'ennemi avec une attaque normale, mais vous ratez votre attaque."
            if self.enemy.cur_hp <= 0:
                print("victoire!")
                # TODO LOOT
                await interaction.followup.send("Combat remporté!", ephemeral=True)
                conn = make_connection()

                floor = get_dungeon_floor(conn, self.user)

                if floor == 5:
                    # TODO
                    print("EXIT DUNGEON")
                else:
                    floor += 1
                    update_dungeon(conn, self.user, floor, self.party[0].cur_hp,
                                   self.party[1].cur_hp, self.party[2].cur_hp)
                    has_scout = False

                    choix1, choix2, choix3, choix4, room_count = generate_choices(self.seed,
                                                                                  floor,
                                                                                  False,
                                                                                  has_scout)
                    embed = await dungeon_choice_embed(choix1, choix2, choix3, choix4)

                    choices = [choix1, choix2, choix3, choix4]

                    await interaction.followup.send(ephemeral=True, view=DungeonChoiceView(
                        self, self.seed, self.user, room_count, choices, self.party), embed=embed)

                close_connection(conn)
            else:
                for p in self.party:
                    if p != self.party[0] and p.cur_hp > 0:
                        msg += "\nVos alliés attaquent avec vous!"
                        break
                turn_embed = await make_turn_embed(self.enemy, self.party, msg)
                await interaction.followup.send(embed=turn_embed, ephemeral=True)
                await play_enemy_turn(self.enemy, self.party, self.seed, interaction)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔮", custom_id="special_attack")
    async def special_attack_callback(self, button, interaction):
        if interaction.user.id == self.user:
            await interaction.response.defer()
            conn = make_connection()

            close_connection(conn)
            await interaction.followup.edit_message(interaction.message.id,view=None)



class CombatWaifu:

    def __init__(self, cur_hp, max_hp, atk, defense, speed, bonus_hit, bonus_dodge, level, waifu_id, dungeon_class = None) :
        self.cur_hp = cur_hp
        self.max_hp = max_hp
        self.atk = atk
        self.defense = defense
        self.speed = speed
        self.bonus_hit = bonus_hit
        self.bonus_dodge = bonus_dodge
        self.level = level
        self.waifu_id = waifu_id
        self.dungeon_class = dungeon_class


    def attack_waifu(self, power, target_waifu):
        target_waifu.cur_hp -= calc_dmg(self.atk, self.level, target_waifu.defense, power)


def calc_dmg(atk, atk_level, defense, power):
    return int (((((2 * atk_level / 5) + 2) * power * atk / defense / 50) + 2) * (random.randint(85, 100)) / 100)




class DungeonChoiceView(discord.ui.View):
    def __init__(self, dungeon_instance, seed, user, nb_choices, choices, party, *items: Item):
        super().__init__(*items)
        self.seed = seed
        self.user = user
        self.dungeon_instance = dungeon_instance
        self.choices = choices
        self.party = party
        options = []
        if nb_choices > 1:
            options.append(discord.SelectOption(
                label="Chemin 1",
                description="La première option est souvent la meilleure.",
                emoji="1️⃣"
            ))
            options.append(discord.SelectOption(
                label="Chemin 2",
                description="J'ai cru entendre un bruit venir de là!",
                emoji="2️⃣"
            ))
            if nb_choices > 2:
                options.append(discord.SelectOption(
                    label="Chemin 3",
                    description="Est-ce que je me suis perdu?",
                    emoji="3️⃣"
                ))
                if nb_choices == 4:
                    options.append(discord.SelectOption(
                        label="Chemin 4",
                        description="Un bon choix ... ?",
                        emoji="4️⃣"
                    ))
        else:
            options.append(discord.SelectOption(
                label="Le seul chemin",
                description="Impossible de se tromper.",
                emoji="⬆️"
            ))
        select_component = self.CustomSelect(options=options, placeholder="Choisissez le chemin à prendre.",
                                             dcv=self)
        self.add_item(select_component)

    async def take_path(self, path_number, interaction: discord.Interaction):
        conn = make_connection()
        path_taken = self.choices[path_number - 1]

        print("path taken!", path_taken)
        floor = get_dungeon_floor(conn, self.user)

        path_type = path_taken[0]

        if path_type in (0, 1, 8):
            await start_battle(floor, path_type, self.seed, self.party, interaction)
        close_connection(conn)

    class CustomSelect(discord.ui.Select):
        def __init__(self, options, placeholder, dcv):
            super().__init__(placeholder=placeholder, max_values=1, min_values=1, options=options)
            self.dcv = dcv

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id == self.dcv.user:
                await interaction.response.defer()
                val = self.values[0]
                if val == "Le seul chemin":
                    path_number = 1
                else:
                    path_number = int(val.split("Chemin ")[1])
                await interaction.followup.send(content=f"{val} a été choisi.", ephemeral=True)
                await interaction.followup.edit_message(interaction.message.id,
                                                        view=None)
                await self.dcv.take_path(path_number, interaction)


class Dungeon(commands.Cog):
    def __init__(self, setup_bot):  # this is a special method that is called when the cog is loaded
        self.bot = setup_bot


    @discord.slash_command(
        name="dungeon",
        guild_ids=restricted_guilds,
        description="Lance le donjon"
    )
    async def dungeon(
            self,
            ctx: discord.ApplicationContext
    ):
        conn = make_connection()
        try:
            user = ctx.user.id

            waifu_list = get_waifu_in_current_party_with_level(conn, user)

            if len(waifu_list) > 0:
                hps=[None, None, None]
                i = 0
                party = []
                for waifu_id, waifu_level in waifu_list:
                    link, star, base_hp, base_atk, base_def, base_speed, bonus_hit, bonus_dodge, dungeon_class \
                        = get_party_waifu_by_id(conn, waifu_id)

                    hp, atk, defense, speed = (formula_calc_hp(base_hp, waifu_level),
                                               formula_calc_stat(base_atk, waifu_level),
                                               formula_calc_stat(base_def, waifu_level),
                                               formula_calc_stat(base_speed, waifu_level))

                    hps[i] = hp
                    i += 1
                    party_waifu = CombatWaifu(hp, hp, atk, defense, speed, bonus_hit, bonus_dodge, waifu_level, waifu_id, dungeon_class)
                    party.append(party_waifu)

                seed = random.randint(1, 10000)

                item_count = MIN_ITEMS + (seed % (1 + MAX_ITEMS - MIN_ITEMS))

                potion_count = MIN_POTIONS
                food_count = MIN_FOOD
                key_count = MIN_KEYS

                item_count -= potion_count - food_count - key_count

                # distribute the remaining items
                for i in range(item_count):
                    if key_count < MAX_KEYS and int(seed / (10 ** i)) % 10 <= 4:
                        key_count += 1
                    if food_count < MAX_FOOD and int(seed / (10 ** i)) % 10 <= 7:
                        food_count += 1
                    elif potion_count < MAX_POTIONS:
                        potion_count += 1
                    elif food_count < MAX_FOOD:
                        food_count += 1
                    else:
                        key_count += 1
                base_floor = 1

                join_dungeon(conn, user, seed, hps[0], hps[1], hps[2], key_count, potion_count, food_count, base_floor)

                await ctx.respond("Vous avez rejoint le donjon!", ephemeral=True)

                has_scout = False

                choix1, choix2, choix3, choix4, room_count = generate_choices(seed,
                                                                              base_floor,
                                                                              False,
                                                                              has_scout)
                embed = await dungeon_choice_embed(choix1, choix2, choix3, choix4)

                choices = [choix1, choix2, choix3, choix4]

                await ctx.respond(ephemeral=True, view=DungeonChoiceView(
                    self, seed, user, room_count, choices, party), embed=embed)
            else:
                await ctx.respond("Vous n'avez pas de waifu dans votre groupe.", ephemeral=True)
            close_connection(conn)
        except Exception as e:
            print(e)
            close_connection(conn)


def setup(bot_setup):
    bot_setup.add_cog(Dungeon(bot_setup))

