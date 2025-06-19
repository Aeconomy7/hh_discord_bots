import sqlite3

from sqlite3 import Error


class JadDbHandler:
	def __init__(self):
		self.__db_location = "/home/sc00by/Documents/Programming/Discord/haunted_house_bots/JadBot/db/jbotsqlite.db"

		# Create connection for initiating tables
		self.__conn = self.__create_connection(self.__db_location)
		if self.__conn is None:
			print("[-] Could not connect to Jad DB")
			return

		# Create tables if not exist
		self.__create_char_table()
		print("[+] Successfully initiated database!")

		# Close connection
		self.__conn.close()

	def __enter__(self):
		#Establish connection with Jad DB
		self.__conn = self.__create_connection(self.__db_location)
		print("[+] Connected to Jad DB")

	def __exit__(self):
		# Commit changes to DB
		self.__conn.commit()
		# Close DB
		self.__conn.close()

	def __create_connection(self,db_file):
		conn = None

		try:
			conn = sqlite3.connect(db_file)
		except Error as e:
			print(e)

		return conn

	def __create_char_table(self):
		sql_query = """ CREATE TABLE IF NOT EXISTS characters (
				id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
				discord_name TEXT NOT NULL,
				hp INTEGER DEFAULT 99,
				gold INTEGER DEFAULT 1000,
				level INTEGER DEFAULT 1,
				exp INTEGER DEFAULT 0,
				prayer TEXT DEFAULT 'nopray',
				strength INTEGER DEFAULT 5,
				magic INTEGER DEFAULT 0,
				accuracy INTEGER DEFAULT 50
			);"""

		try:
			cursor = self.__conn.cursor()
			cursor.execute(sql_query)
			self.__conn.commit()
		except Error as e:
			print(e)

	def get_character(self,char_name):
		sql_query = "SELECT * FROM characters WHERE discord_name = \'" + char_name + "\'"

		try:
			cursor = self.__conn.cursor()
			cursor.execute(sql_query)
			row = cursor.fetchone()
			if row is None:
				print("[-] Could not find character \'" + char_name + "\' :(")
				return None
			else:
				print("[+] Found character named \'" + char_name + "\' :D")
				return row
		except Error as e:
			print(e)
			return None

	def get_rand_character(self):
		sql_query = "SELECT * FROM characters ORDER BY RANDOM() LIMIT 1;"

		try:
			cursor = self.__conn.cursor()
			cursor.execute(sql_query)
			row = cursor.fetchone()
			if row is None:
				print("[-] Error picking random character :(")
				return None
			else:
				print("[+] \'" + row[1] + "\' was randomly selected!")
				return row
		except Error as e:
			print(e)
			return None

	def create_character(self,char_name):
		sql_query = "INSERT INTO characters ( discord_name ) VALUES ( \'" + char_name + "\' )"

		try:
			cursor = self.__conn.cursor()
			cursor.execute(sql_query)
			self.__conn.commit()
			print("[+] Created character \'" + char_name + "\'!")
			return True
		except Error as e:
			print(e)
			return False

	def update_character(self, char_name, hp=0, gold=0, level=0, exp=0, prayer='nopray', strength=0, magic=0, accuracy=0):
		# Attempt to fetch character by character name first
		character = self.get_character(char_name)

		if character is None:
			return False

		print("character: ")
		print(character)

		new_hp 		= character[2] + hp
		new_gold 	= character[3] + gold
		new_level	= character[4] + level
		new_exp		= character[5] + exp
		new_prayer	= prayer
		new_strength	= character[7] + strength
		new_magic	= character[8] + magic
		new_accuracy	= character[9] + accuracy

		sql_query = "UPDATE characters SET hp=" + str(new_hp) + ", gold=" + str(new_gold) + ", level=" + str(new_level) + ", exp=" + str(new_exp) + ", prayer=\'" + new_prayer + "\', strength=" + str(new_strength) + ", magic=" + str(new_magic) + ", accuracy=" + str(new_accuracy) + " WHERE id=" + str(character[0])

		print("[?] Trying: " + sql_query)

		try:
			cursor = self.__conn.cursor()
			cursor.execute(sql_query)
			self.__conn.commit()
			print("[+] Successfully updated character \'" + char_name + "\' :D")
			return True
		except Error as e:
			print(e)
			return False
