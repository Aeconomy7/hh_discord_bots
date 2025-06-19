# Work with Python 3.6
import random
import re
import dice

import asyncio
import aiohttp
import json

import discord
from discord.ext import commands

BOT_PREFIX=("!dndbot ","/dndbot ","/")
TOKEN='XXXX'

# Define the intents your bot needs
intents = discord.Intents.all()

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

@bot.event
async def on_message(message):
	if message.author == bot.user:
		return
	if '/' in message.content:
		allowed_slash_cmds = ['roll','r']
		if message.content.split('/')[1] in allowed_slash_cmds or len(message.content.split()) > 1:
			await bot.process_commands(message)
	else:
		await bot.process_commands(message)
	return

#~~~~~~~~~~~~~~#
# Begin /hello #
#~~~~~~~~~~~~~~#
@bot.command(name	= 'hello',
	description	= "Introduce yourself to the bot and learn a lil something",
	brief		= "Hi there, `dndbot`! :)",
	pass_context	= True)
#@bot.command(name='hello',pass_context=True)
async def hello_cmd(context):
	# print('Function called by ' + context.message.author)
	msg = 'Hello ' + context.message.author.mention + ', I am `dndbot`!  Type in the command `!dndbot help` to learn more!'
	# await bot.send_message(message.channel, msg)
	await context.send(msg)
#~~~~~~~~~~~~#
# Emd /hello #
#~~~~~~~~~~~~#


#~~~~~~~~~~~~#
# Begin help #
#~~~~~~~~~~~~#
# Remove previous help command
bot.remove_command("help")

@bot.command(name 	= 'help',
	pass_context	= True)
async def help_cmd(context):
	msg	= ("```Usage: `!dndbot [cmd]` OR `/dndbot [cmd]`\n\n"
	"Available commands (`[cmd]`):\n"
	"\t`hello` : Say hello to `dndbot`!\n"
	"\t`roll`  : Roll a dice regularly (Ex: `!dndbot roll d20+2`)```")
	await context.send(msg)
#~~~~~~~~~~~#
# End /help #
#~~~~~~~~~~~#


#~~~~~~~~~~~~~#
# Begin /roll #
#~~~~~~~~~~~~~#
# Supporting commands
def dice_roll(sides):
	return randint(1,sides)

@bot.command(name	= 'roll',
	description	= "Roll a dice, any number of sides and any modifier!!",
	brief		= "Rolls dice d1-d199999",
	aliases		= ['r'],
	pass_context	= True)
async def roll_cmd(context,*dice_args):
	# get arguements passed
	dice_roll = ''.join(dice_args)

	# attempt to roll the dice!
	try:
		r = dice.roll(dice_roll)
		await context.send("You rolled a `" + str(r) + "`!")
	except dice.DiceBaseException as e:
		print(e.pretty_print())
		await context.send("Error with your `roll` command '" + dice_roll + "' :(")
#~~~~~~~~~~~#
# End /roll #
#~~~~~~~~~~~#


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
