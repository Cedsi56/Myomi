# This example requires the 'message_content' intent.

import os
from dotenv import load_dotenv
from constants import bot
from waifu import *
from upload import *
from music import *


load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


bot.run(TOKEN)

print("Execution is over")

