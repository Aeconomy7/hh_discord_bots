# Work with Python 3.6
import random
import re
import dice

import asyncio
import aiohttp
import json

import discord
from discord.ext import commands

BOT_PREFIX=("!hack ","/hack ","/")
TOKEN='XXXX'

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

@bot.event
async def on_message(message):
        if message.author == bot.user:
                return
        if '/' in message.content:
                allowed_slash_cmds = ['hexdump', 'hex']
                if message.content.split('/')[1] in allowed_slash_cmds or len(message.content.split()) > 1:
                        await bot.process_commands(message)

#~~~~~~~~~~~~~~~~#
# Begin /hexdump #
#~~~~~~~~~~~~~~~~#
@bot.command(name	= 'hexdump',
	aliases		= ['hex'],
	pass_context	= True)
async def hexdump_cmd(context,*args):
	hexstr=""
	for tuple in args:
		hexstr += str(tuple) + " => `\\x" + "\\x".join("{:02x}".format(ord(c)) for c in tuple) + "`\n"
	print("Executing hexdump...OUTPUT: " + hexstr)
	await context.send(hexstr)
#~~~~~~~~~~~~~~#
# End /hexdump #
#~~~~~~~~~~~~~~#

# print ready status
@bot.event
async def on_ready():
        print('Logged in as')
        print(bot.user.name)
        print(bot.user.id)
        print('------')

# list servers using bot
#async def list_servers():
#    await bot.wait_until_ready()
#    while not bot.is_closed:
#        print("Current servers:")
#        for server in bot.servers:
#            print(server.name)
#        await asyncio.sleep(600)

#bot.loop.create_task(list_servers())

print("[+] Bot started")
bot.run(TOKEN)

