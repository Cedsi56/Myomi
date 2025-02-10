# This example requires the 'message_content' intent.

import os
from dotenv import load_dotenv
from constants import bot


load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


cogs_list = [
    'music',
    'upload',
    'waifu',
]

for cog in cogs_list:
    bot.load_extension(f'{cog}')

bot.run(TOKEN)

print("Execution is over")

