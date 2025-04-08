from discord.ext import commands
bot = commands.Bot()
allowed_guilds = [1190980903296569395, 272125925896880129]
restricted_guilds = [1190980903296569395]


def formula_calc_hp(base_hp, level):
    return int ((base_hp * 2 * level) / 100 + level + 10)


def formula_calc_stat(base_stat, level):
    return int ((base_stat * 2 * level) / 100 + 5)




MIN_KEYS = 0
MAX_KEYS = 2

MIN_POTIONS = 2
MAX_POTIONS = 4

MIN_FOOD = 1
MAX_FOOD = 2

MIN_ITEMS = 4
MAX_ITEMS = 6




CLASSES_EMOJIS = [
    "🧙‍♀️",
    "🍬"
]


BASE_POWER = 70