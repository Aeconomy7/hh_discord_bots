import sqlite3

from sqlite3 import Error


class LolDbHandler:
	def __init__(self):
		self.__db_location = "/home/sc00by/Documents/Programming/Discord/haunted_house_bots/LOLBOT/db/loldbsqlite.db"

		self.__conn = self.__create_connection(self.__db_location)
		if self.__conn is None:
			print("[DB][-] Could not connect to LOL DB")
			return

		# Create hiscore table if not exist
		self.__create_summoner_table()
		print("[DB][+] Successfully initiated database!")

		self.__conn.close()

	def __enter__(self):
		self.__conn = self.__create_connection(self.__db_location)
		print("[DB][+] Connected to LOL DB")

	def __exit__(self):
		self.__conn.commit()
		self.__conn.close()

	def __create_connection(self,db_file):
		conn = None

		try:
			conn = sqlite3.connect(db_file)
		except Error as e:
			print(e)

		return conn

	def __create_summoner_table(self):
		sql_query = """ CREATE TABLE IF NOT EXISTS summoner (
				id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
				summoner_name TEXT NOT NULL,
				competitor INTEGER DEFAULT 0
			);"""

		try:
			cursor = self.__conn.cursor()
			cursor.execute(sql_query)
			self.__conn.commit()
		except Error as e:
			print(e)

	# Assumption: Summoner ranked history exists
	def get_summoner(self,sn):
		sql_query = "SELECT * FROM summoner WHERE summoner_name = \'" + sn + "\'"

		try:
			cursor = self.__conn.cursor()
			cursor.execute(sql_query)
			row = cursor.fetchone()
			if row is None:
				print("[-] Error finding summoner in DB")
				return None
			else:
				print("[DB][+] \'" + row[1] + "\' was found!")
				return row
		except Error as e:
			print(e)
			return None

	def add_summoner(self,sn,prop_data):
		sql_query = "INSERT INTO summoner ( summoner_name,competitor ) VALUES ( \'" + sn + "\' )"

		try:
			cursor = self.__conn.cursor()
			cursor.execute(sql_query)
			self.__conn.commit()
			print("[DB][+] Added summoner '" + sn + "' to the DB")
		except Error as e:
			print(e)
			return None

	def update_summoner(self, sn, comp):
                # Attempt to fetch character by character name first
		summoner = self.get_summoner(sn)

		if summoner is None:
			return False

		#print("character: ")
		#print(character)

		sql_query = "UPDATE summoner SET competitor=" + str(comp) + " WHERE summoner_name=" + sn

		print("[?] Trying: " + sql_query)

		try:
			cursor = self.__conn.cursor()
			cursor.execute(sql_query)
			self.__conn.commit()
			print("[+] Successfully updated character \'" + sn + "\' to \'" + str(comp) + "\' :D")
			return True
		except Error as e:
			print(e)
			return False

