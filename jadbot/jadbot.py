# Work with Python 3.6
import requests
import pprint
from bs4 import BeautifulSoup
import urllib

from random import randint
from time import sleep

import asyncio
import aiocron
import aiohttp
import json

import discord
from discord.ext import commands

from db.jbotdb import JadDbHandler

#~~~~~~~~~~~~~~~~~~~#
# Initiate database #
#~~~~~~~~~~~~~~~~~~~#
JBOT_DB = JadDbHandler()
JBOT_DB.__enter__()
#~~~~~~~~~~~~~~#
# End database #
#~~~~~~~~~~~~~~#

BOT_PREFIX=("!jadbot ","/jadbot ","/")
TOKEN='XXXX'

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=BOT_PREFIX,intents=intents)
print("[+] Successfully attached bot!")

#~~~~~~~~~~~~~~~~~~~~~~#
# Main command handler #
#~~~~~~~~~~~~~~~~~~~~~~#
@bot.event
async def on_message(message):
	if message.author == bot.user:
		return
	if '/' in message.content:
		allowed_slash_cmds = ['hiscore','hiscores','pray','begin','commence','stats','stat']
		if message.content.split('/')[1] in allowed_slash_cmds or len(message.content.split()) > 1:
			await bot.process_commands(message)
	else:
		await bot.process_commands(message)
	return
#~~~~~~~~~~~~~~~~~~~~~#
# end command handler #
#~~~~~~~~~~~~~~~~~~~~~#


#~~~~~~~~~~~~~~#
# Begin /hello #
#~~~~~~~~~~~~~~#
@bot.command(name	= 'hello',
	description	= "Introduce yourself to the bot and learn a lil something",
	brief		= "Hi there, `JadBot`! :)",
	pass_context	= True)
#@bot.command(name='hello',pass_context=True)
async def hello_cmd(context):
	# print('Function called by ' + context.message.author)
	msg = 'Hello ' + context.message.author.mention + ', I am `JadBot`!  Type in the command `!JadBot help` to learn more!'
	# await bot.send_message(message.channel, msg)
	await context.send(msg)
#~~~~~~~~~~~~#
# Emd /hello #
#~~~~~~~~~~~~#


#~~~~~~~~~~~~~~~~~#
# Begin /hiscores #
#~~~~~~~~~~~~~~~~~#
# Supporting commands
#def dice_roll(sides):
#	return randint(1,sides)

@bot.command(name	= 'hiscores',
	description	= "Return high scores of a character",
	brief		= "View highscores",
	aliases		= ['h','hiscore'],
	pass_context	= True)
async def roll_cmd(context,*char_args):
	legal_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890 -"

	# get arguements passed
	osrs_char = ' '.join(char_args)

	# Validate character name passed
	for i in osrs_char:
		valid = False
		for j in legal_chars:
			if i == j:
				valid = True
				break
		if valid is False:
			await context.send("Invalid character name.")
			return

	URL  = 'https://secure.runescape.com/m=hiscore_oldschool/hiscorepersonal'
	DATA = 'user1=' + urllib.parse.quote(osrs_char) + '&submit=Search'

	print("JadBot started searching for '" + osrs_char + "'...")
	async with context.typing():
		try:
			r = requests.post(url=URL,data=DATA,timeout=50)
		except requests.exceptions.RequestException as e:
			await context.send("Request timed out, most likely the OSRS hiscores functionality is suffering. :(")
			return
	print("JadBot done searching...")

	char_exist = "No player <b>&quot;" + osrs_char + "&quot;</b> found"

	# Check if user does not exist
	if char_exist in r.text:
		await context.send("Could not find player named **" + osrs_char + "** :(")
		return

	soup = BeautifulSoup(r.text, "lxml")

	skill_row = []

	for table_row in soup.select("table tr"):
		cells = table_row.findAll('td')

		if len(cells) == 5:
			if cells[1].text != '':
				skill = []
				img_link = True
				for cell in cells:
					if img_link is True:
						skill.append(cell.img)
						img_link = False
					else:
						skill.append(cell.text.strip("\n"))
				skill_row.append(skill)

	### START MSG ###
	msg = ""
	msg = msg + "```~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
	msg = msg + "Hiscores for:   " + osrs_char + "\n"
	msg = msg + "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
	msg = msg + "Skill          Rank        Level    Total Exp\n"
	msg = msg + "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
	#           "Construction   11,111,111  99       4,600,000,000"
	for skill in skill_row:
		skill_name = str(skill[1])
		ranking = str(skill[2])
		level = str(skill[3])
		total_exp = str(skill[4])
		msg = msg + skill_name + (15-len(skill_name))*' '
		msg = msg + ranking + (12-len(ranking))*' '
		msg = msg + level + (9-len(level))*' '
		msg = msg + total_exp + '\n'
	msg = msg + "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
	msg = msg + "```"
	### END MSG ###

	#print(msg)
	#pp = pprint.PrettyPrinter(indent=8)
	#pp.pprint(skill_row)

	await context.send(msg)
	# attempt to roll the dice!
#~~~~~~~~~~~~~~~#
# End /hiscores #
#~~~~~~~~~~~~~~~#


#~~~~~~~~~~~~~~#
# Begin /begin #
#~~~~~~~~~~~~~~#
@bot.command(name	= 'begin',
	description	= "Start your JadBot character!",
	brief		= "Begin your journey :)",
	aliases		= ['create','start','adventure','commence'],
	pass_context	= True)
async def begin_cmd(context):
	msg = ''

	print("[!] Attempting to create character \'" + str(context.message.author) + "\'...")

	# Check if character is already in database
	check_char = JBOT_DB.get_character(str(context.message.author))
	if check_char is not None:
		msg = msg + "[-] You have already begun your journey! :)"
		await context.send(msg)
		return

	# Attempt to create character
	status = JBOT_DB.create_character(str(context.message.author))
	if status is True:
		msg = msg + '[+] Successfully registered your character!  It is tied to your Discord account and will not store/process any personal data.'
		await context.send(msg)
	else:
		msg = msg + '[-] Something went wrong :('
		await context.send(msg)
#~~~~~~~~~~~~#
# End /begin #
#~~~~~~~~~~~~#

#~~~~~~~~~~~~~#
# Begin /pray #
#~~~~~~~~~~~~~#
@bot.command(name	= 'pray',
	description	= "Start your JadBot character!",
	brief		= "Begin your journey :)",
	aliases		= ['prayer'],
	pass_context	= True)
async def pray_cmd(context,*pray_args):
	prayer_types = ['range','mage','melee']
	prayer_cast = ''.join(pray_args)
	prayer_time_secs = 90

	msg = ''

	valid = False

	# Check for valid prayer type
	for prayer in prayer_types:
		if prayer_cast.lower() == prayer.lower():
			valid = True
			break

	# Check that character exists and is not currently praying
	char_check = JBOT_DB.get_character(str(context.message.author))
	if char_check is None:
		msg = msg + "[-] Could not find your character, have you started your journey with `/begin`?"
		await context.send(msg)
		return
	else:
		if char_check[6] != 'nopray':
			msg = msg + "[-] Sorry, you are already praying **" + char_check[6] + "**, please wait for this prayer to expire."
			await context.send(msg)
			return


	# Try to cast prayer to database now
	if valid is False:
		msg = msg + "[-] Invalid prayer type, the prayers you can choose are: `range, mage, melee`"
		await context.send(msg)
		return
	else:
		status = JBOT_DB.update_character(char_name=str(context.message.author),prayer=prayer_cast.lower())
		if status is True:
			msg = msg + "[!] **" + str(context.message.author).split("#")[0] + "** is now praying **" + prayer_cast.lower() + "** for " + str(prayer_time_secs) + "  seconds!"
			print("[!] \'" + str(context.message.author).split("#")[0] + "\' is now praying " + prayer_cast.lower() + " for " + str(prayer_time_secs) + "  seconds!")
			await context.send(msg)
		else:
			msg = msg + "[-] Something went wrong with attempting to pray..."
			print("[-] Something went wrong with attempting to pray...")
			await context.send(msg)
			return

		msg = ''

		#
		await asyncio.sleep(prayer_time_secs)
		while JBOT_DB.update_character(char_name=str(context.message.author),prayer='nopray') is not True:
			print("[-] BAD ERROR: failed to set prayer back to \'nopray\'...")
		msg = msg = "[!] **" + str(context.message.author).split("#")[0] + "** is done praying"
		await context.send(msg)
		return
#~~~~~~~~~~~#
# End /pray #
#~~~~~~~~~~~#



#~~~~~~~~~~~~~~#
# Begin /stats #
#~~~~~~~~~~~~~~#
@bot.command(name	= 'stat',
	description	= "See how you are faring!!!",
	brief		= "Character stats",
	aliases		= ['stats','charstats'],
	pass_context	= True)
async def stat_cmd(context):
	msg = ''

	# Check if character is already in database
	check_char = JBOT_DB.get_character(str(context.message.author))
	if check_char is None:
		msg = msg + "[-] Could not find your character, have you started your journey with `/begin`?"
		await context.send(msg)
		return

	# Craft character message
	msg = "```#------------------------------------#\n"
	msg = msg + "  CHARACTER : " + check_char[1].split("#")[0] + "\n"
	msg = msg + "  LEVEL     : " + str(check_char[4]) + " (" + str(check_char[5]) + " exp)\n"
	msg = msg + "#------------------------------------#\n\n"
	msg = msg + "    Current HP : " + str(check_char[2]) + "\n"
	msg = msg + "    Gold       : " + str(check_char[3]) + "\n\n"
	msg = msg + "    Strength   : " + str(check_char[7]) + "\n"
	msg = msg + "    Magic      : " + str(check_char[8]) + "\n"
	msg = msg + "    Accuracy   : " + str(check_char[9]) + "\n\n"
	msg = msg + "#------------------------------------#```"

	await context.send(msg)
#~~~~~~~~~~~~#
# End /stats #
#~~~~~~~~~~~~#


# print ready status
@bot.event
async def on_ready():
	print('+----------------+')
	print('[+] Logged in as:')
	print("BOT USER: " + bot.user.name)
	print("BOT ID  : " + str(bot.user.id))
	print('+----------------+')

#~~~~~~~~~~~~~~~~~~#
# Event JAD-ATTACK #
#~~~~~~~~~~~~~~~~~~#
@bot.event
async def jad_attack():
	reward_gold	= 1000

	channel_id 	= 754542101219508385
#	channel_id	= 729104553638625310 # Test channel
#	role_id		= 751833828729028729
#	role_id		= 723296898852716667 # Test role

	# Get channel
	await asyncio.sleep(10)
	channel = bot.get_channel(channel_id)

	if channel is None:
		print("[-] Error finding channel...")
		return

	while True:
		msg = ''
		jad_target = ''

		# Roll random jad attack (mage/range)
		jad_attack = randint(0,1)
		jad_attack_type = ''

		# FOR DEBUGGING
		#rand_sleep = 30

		# SLEEP BETWEEN JAD ATTACKS
		# .5 to 5 hours
		rand_sleep = randint(1800,18000)
		print("[!] Jad has gone to sleep for " + str(rand_sleep) + " seconds")
		await asyncio.sleep(rand_sleep)

		# JAD IS MAD
		print("[!] JAD IS ABOUT TO ATTACK...")
		await channel.send("[!] Jad is stirring...BE ON YOUR TOES!!!")
		rand_sleep = randint(40,200)
		await asyncio.sleep(rand_sleep)

		# Select random character to target
		char_target = JBOT_DB.get_rand_character()
		if char_target is None:
			print("[-] Error choosing Jad attack target...")
			return

		if jad_attack == 0:
			# Range attack
			jad_attack_type = 'range'
			with open('img/jad/jad_ranged_attack.gif','rb') as f:
				picture = discord.File(f)
				msg = "[!] Jad is targeting **" + char_target[1].split("#")[0] + "** with a **" + jad_attack_type + "** attack!!!  Quick, pray **" + jad_attack_type + "**!"
				#msg = "**Jad** is targeting <@&" + member.id + "> with a **" + jad_attack_type + "** attack!!!  Quick, pray **" + jad_attack_type + "**!"
				print("[+] " + msg)
				await channel.send(content=msg,file=picture)
		elif jad_attack == 1:
			# Mage attack
			jad_attack_type = 'mage'
			with open('img/jad/jad_magic_attack.gif','rb') as f:
				picture = discord.File(f)
				msg = "[!] Jad is targeting **" + char_target[1].split("#")[0] + "** with a **" + jad_attack_type + "** attack!!!  Quick, pray **" + jad_attack_type + "**!"
				#msg = "**Jad** is targeting <@&" + member.id + "> with a **" + jad_attack_type + "** attack!!!  Quick, pray **" + jad_attack_type + "**!"
				print("[+] " + msg)
				await channel.send(content=msg,file=picture)
		elif jad_attack == 2:
			# Melee attack (not yet implemented)
			jad_attack_type = 'melee'
			#msg = "**Jad** is targeting **" + str(char_target) + "** with a **" + jad_attack_type + "** attack!!!  Quick, pray **" + jad_attack_type + "**!"
		else:
			print("[-] Encountered an error with jad_attack")
			return

		await asyncio.sleep(60)

		msg = ''

		# Check if the target is correctly praying
		pray_check = JBOT_DB.get_character(char_target[1])
		# SUCCESS
		if pray_check[6] == jad_attack_type:
			while JBOT_DB.update_character(char_name=char_target[1],gold=1000) is not True:
				print("[-] BAD ERROR")
			msg = msg + "[+] You have successfully fended off Jad's attack!!!  You have earned **" + str(reward_gold) + " gold**!"
			await channel.send(msg)
		# FAIL
		else:
			dmg = randint(1,20) * -1
			while JBOT_DB.update_character(char_name=char_target[1],hp=dmg) is not True:
				print("[-] BAD ERROR")
			msg = msg + "[-] Jad has struck **" + char_target[1].split("#")[0] + "** with a **" + jad_attack_type + "** attack, dealing **" + str(dmg) + "** damage."
			await channel.send(msg)

		# JAD IS SLEEPY
		print("[!] JAD IS DONE ATTACKING!  he is sleepy now...")

#~~~~~~~~~~~~~~~~#
# End JAD-ATTACK #
#~~~~~~~~~~~~~~~~#
bot.loop.create_task(jad_attack())
print("[+] Bot started")
bot.start(TOKEN)

