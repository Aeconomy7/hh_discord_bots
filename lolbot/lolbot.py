# Work with Python 3.6
import requests

import asyncio
import aiohttp
import json
import re
import random

import urllib.parse

import discord
from discord.ext import commands

from db.loldb import LolDbHandler

from riotwatcher import LolWatcher, RiotWatcher, ApiError

# INITIATE DB
LOL_DB = LolDbHandler()
LOL_DB.__enter__()
# END INITIATE

BOT_PREFIX=("!lolbot ","/lolbot ","/lol")
TOKEN='XXXX'
PROXY_MODE=0
RIOT_API_KEY='XXXX'
lol_watcher = LolWatcher(RIOT_API_KEY)
riot_watcher = RiotWatcher(RIOT_API_KEY)
REGION='na1'
RANK_COLORS = {
	"iron": 0x6E6867,
	"bronze": 0x9C5221,
	"silver": 0xC0C0C0,
	"gold": 0xE1B61A,
	"platinum": 0x1FAF9B,
	"emerald": 0x2AB97D,
	"diamond": 0x4F77FF,
	"master": 0xA045E0,
	"grandmaster": 0xBD3737,
	"challenger": 0xF4C873
}
intents = discord.Intents.all()

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

@bot.event
async def on_message(message):
	if message.author == bot.user:
		return
	if '/' in message.content:
		allowed_slash_cmds = ['']
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
	brief		= "Hi there, `LOLBOT`! :)",
	pass_context	= True)
#@bot.command(name='hello',pass_context=True)
async def hello_cmd(context):
	# print('Function called by ' + context.message.author)
	msg = 'Hello ' + context.message.author.mention + ', I am `LOLBOT`!  Type in the command `!LOLBOT help` to learn more!'
	# await bot.send_message(message.channel, msg)
	await context.send(msg)
#~~~~~~~~~~~~#
# Emd /hello #
#~~~~~~~~~~~~#


#~~~~~~~~~~~~~#
# Begin /rank #
#~~~~~~~~~~~~~#
# rank command:
# params:
#	summoner_name 	= string
@bot.command(
	name='rank',
	description="Return rank and top champion winrates (NA ONLY)!!!!!!",
	brief="RANKED",
	aliases=[],
	pass_context=True
)
async def rank_cmd(context, *rank_args):
	requests.packages.urllib3.disable_warnings()

	region = 'na1'
	platform = 'americas'
	rank = ''

	summoner_name = ' '.join(rank_args)
	if '#' not in summoner_name:
		await context.send("Please use the format `SummonerName#TAG`.")
		return

	name, tag = summoner_name.split('#')
	print("[?] Looking up summoner:", name + "#" + tag)

	# Get Account Info
	try:
		account = riot_watcher.account.by_riot_id(platform, name, tag)
	except ApiError as err:
		code = err.response.status_code
		if code == 429:
			await context.send("Too many requests, not enough cooks...")
		elif code == 404:
			await context.send(f"Could not find account for summoner `{name}#{tag}` :(")
		else:
			await context.send(f"API error: {code}")
		return

	print("[+] Found account info for summoner:", account)
		
	summoner_name = account.get('gameName', name)

	# Get Summoner Info by PUUID
	try:
		summoner = lol_watcher.summoner.by_puuid(region, account['puuid'])
	except ApiError as err:
		code = err.response.status_code
		if code == 429:
			await context.send("Too many requests, not enough cooks...")
		elif code == 404:
			await context.send(f"Could not find summoner info for `{summoner_name}#{tag}` :(")
		else:
			await context.send(f"API error: {code}")
		return

	print("[+] Found summoner info for:", summoner)

	if not summoner or 'puuid' not in summoner:
		await context.send(f"Could not find summoner info for `{summoner_name}#{tag}` :(")
		return

	# Get Ranked Data
	try:
		ranked_response = lol_watcher.league.by_puuid(region, summoner['puuid'])
	except ApiError as err:
		code = err.response.status_code
		if code == 429:
			await context.send("Too many requests, not enough cooks...")
		elif code == 404:
			await context.send(f"Could not find ranked history for `{summoner_name}#{tag}` :(")
		else:
			await context.send(f"API error: {code}")
		return

	msg = "```"
	try:
		for i in ranked_response:
			if i['queueType'] == "RANKED_SOLO_5x5":
				winrate = (i['wins'] / (i['wins'] + i['losses'])) * 100
				msg += f"[SOLO/DUO]: {i['tier']} {i['rank']} {i['leaguePoints']}LP, {i['wins']} W / {i['losses']} L ({winrate:.2f}%)\n"
				rank = i['tier']
			if i['queueType'] == "RANKED_FLEX_SR":
				winrate = (i['wins'] / (i['wins'] + i['losses'])) * 100
				msg += f"[FLEXEMSs]: {i['tier']} {i['rank']} {i['leaguePoints']}LP, {i['wins']} W / {i['losses']} L ({winrate:.2f}%)\n"
	except:
		await context.send(f"Could not find solo/duo ranked history for summoner `{summoner_name}` :(")
		return
	msg += "```"

	if msg == "``````":
		await context.send(f"Could not find solo/duo ranked history for summoner `{summoner_name}` :(")
		return
	else:
		try:
			with open(f"./static/img/ranked_emblems/{rank.lower()}.png", "rb") as f:
				rank_file = discord.File(f, filename="rank.png")
				rank_embed = discord.Embed(
					title=summoner_name + "'s Rank Stats",
					color=RANK_COLORS.get(rank.lower(), 0xFFFFFF)
				)
				rank_embed.set_thumbnail(url="attachment://rank.png")
				rank_embed.add_field(name="Rank Info", value=msg, inline=False)
				await context.send(file=rank_file, embed=rank_embed)
		except FileNotFoundError:
			await context.send(msg)

	print(f"[+] Successfully found ranking of summoner '{summoner_name}'")
	return

#~~~~~~~~~~~#
# End /rank #
#~~~~~~~~~~~#


#~~~~~~~~~~~~~~~~#
# Begin /compete #
#~~~~~~~~~~~~~~~~#
# rank command:
# params:
#	action		= string (add / remove)
#	   summoner_name   = string
@bot.command(name	= 'compete',
	description	= "Add or remove summoner from rank competition",
	brief		= "COMPETE",
	aliases		= [],
	pass_context	= True)
async def join_compete_cmd(context,*rank_args):
	print(rank_args[0])
	return
#~~~~~~~~~~~~~~#
# End /compete #
#~~~~~~~~~~~~~~#



#~~~~~~~~~~~~~~~#
# Begin /update #
#~~~~~~~~~~~~~~~#
# update command:
# params:
# 	- summoner name
@bot.command(name	   = 'update',
	description	 = "Update rank history of summoner",
	brief		   = "UPDATE",
	aliases		 = [],
	pass_context	= True)
async def update_cmd(context,*update_args):
	requests.packages.urllib3.disable_warnings()

	summoner_name = urllib.parse.quote(' '.join(update_args))

	# CACHE MECHANISM
	#with open("/home/sc00by/Documents/Programming/Discord/haunted_house_bots/LOLBOT/_summoner.cache","r") as f:
	#	for line in f:
	#		if line.split(":")[0] == summoner_name:
	#			summid = line.split(":")[1]
	#f.close()

	# DATABASE CACHE MECHANISM
	summoner = LOL_DB.get_summoner(summoner_name)

	# NO CACHE HIT
	#if summoner == None:
#		
#	else:
#		update_status = update_rank_history(summid)
#		if update_status == "FAIL":
#			await context.send("Error updating ranked history for `" + summoner_name + "`")
#		else:
#		

#~~~~~~~~~~~~~#
# End /update #
#~~~~~~~~~~~~~#




#~~~~~~~~~~~~~~~~#
# Begin /hiscore #
#~~~~~~~~~~~~~~~~#

#~~~~~~~~~~~~~~#
# End /hiscore #
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
#	await bot.wait_until_ready()
#	while not bot.is_closed:
#		print("Current servers:")
#		for server in bot.servers:
#			print(server.name)
#		await asyncio.sleep(600)

#bot.loop.create_task(list_servers())

print("[+] Bot started")
bot.run(TOKEN)
