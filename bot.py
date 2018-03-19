# -*- coding: utf-8 -*-
import telegrand, sqlite3, sys, random, string, re, Settings

# Some declarations
bot = telegrand.Bot(Settings.BOT_TOKEN)
userData = {}

# Init db
def initDB():
	db = sqlite3.connect("db.sqlite")
	c = db.cursor()
	c.execute("""
		CREATE TABLE REGISTERED (chat_id integer, points integer, address text, referral text, referrer text)
	""")

# Check if db is initialized
try:
	initDB()
except:
	pass

@bot.handle("text", ["/start"])
def start(message):
	db = sqlite3.connect("db.sqlite")
	c = db.cursor()

	# Check if user registered, else ask for address
	c.execute(
		"SELECT referral, points FROM REGISTERED WHERE chat_id = ?",
		[message.chat.id]
	)
	result = c.fetchone()
	if result:
		c.execute(
			"SELECT chat_id FROM REGISTERED WHERE referrer = ?",
			[result[0]]
		)
		invitedUsers = c.fetchall()
		invitedUsernames = []
		for user in invitedUsers:
			user = bot.req("getChat", data={"chat_id": user})
			invitedUsernames.append("<a href='tg://user?id="+str(user.id)+"'>"+user.first_name+"</a>")
		invitedUsernames = ", ".join(invitedUsernames)
	
		bot.req(
			"sendMessage",
			data={
				"chat_id": message.chat.id,
				"text": Settings.MESSAGES['START'] % (result[0], result[1], invitedUsernames),
				"parse_mode": "HTML"
			}
		)
		return
	global userData

	# Send introductive message
	bot.req(
		"sendMessage",
		data={
			"chat_id": message.chat.id,
			"text": Settings.MESSAGES['INTRODUCTION'] % message.chat.first_name
		}
	)
	
	# Store referrer's ID
	userData[message.chat.id] = {}
	if len(message.text.split(" ")) == 2 and len(message.text.split(" ")[1]) == 7:
		userData[message.chat.id]['referrer'] = message.text.split(" ")[1]
	else:
		userData[message.chat.id]['referrer'] = None
	bot.req(
		"sendMessage",
		data={
			"chat_id": message.chat.id,
			"text": Settings.MESSAGES['SEND_ADDRESS']
		}
	)
	bot.nsh(message.chat.id, receiveAddress)

def receiveAddress(message):

	# Check if address is valid
	if not len(message.text) == 42 or not message.text.startswith("0x"):
		bot.req(
			"sendMessage",
			data={
				"chat_id": message.chat.id,
				"text": Settings.MESSAGES['WRONG_ADDRESS']
			}
		)
		bot.req(
			"sendMessage",
			data={
				"chat_id": message.chat.id,
				"text": Settings.MESSAGES['SEND_ADDRESS']
			}
		)
		bot.nsh(message.chat.id, receiveAddress)
		return
	global userData

	# Store address, send greetings message and store data in DB
	userData[message.chat.id]['address'] = message.text
	bot.req(
		"sendMessage",
		data={
			"chat_id": message.chat.id,
			"text": Settings.MESSAGES['REGISTRATION_COMPLETED']
		}
	)
	finalizeRegistration(message)

@bot.handle("text", ["/csv"])
def exportCSV(message):

	# Check if admin
	if message.chat.id != Settings.ADMIN:
		return
	db = sqlite3.connect("db.sqlite")
	c = db.cursor()

	# Get data and build CSV
	c.execute(
		"SELECT address, points FROM REGISTERED"
	)
	results = c.fetchall()
	csv = "E-Mail;ETH Wallet;Points"
	for result in results:
		csv += "\n%s;%s;%s" % (result[0], result[1], result[2])

	# Send file
	bot.req(
		"sendDocument",
		data={
			"chat_id": message.chat.id,
		},
		files={
			"document": (
				"exported.csv",
				csv
			)
		}
	)

def finalizeRegistration(message):
	global userData, db
	db = sqlite3.connect("db.sqlite")
	c = db.cursor()

	# If referred then 
	try:
		userData[message.chat.id]['referrer']
	except:
		pass
	else:

		# Add points
		c.execute(
			"UPDATE REGISTERED SET points = points+5 WHERE referral = ?",
			[
				userData[message.chat.id]['referrer']
			]
		)
		db.commit()

		# Get referrer
		c.execute(
			"SELECT chat_id FROM REGISTERED WHERE referral = ?",
			[
				userData[message.chat.id]['referrer']
			]
		)
		user = c.fetchone()

		# Send congrats
		if user != None:
			bot.req(
				"sendMessage",
				data={
					"chat_id": user[0],
					"parse_mode": "HTML",
					"text": Settings.MESSAGES['EARNED_POINTS']
				}
			)
		db.commit()

	# Generate random referral ID
	referral = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))

	# Store data in DB
	c.execute(
		"INSERT INTO REGISTERED (chat_id, points, address, referral, referrer) VALUES (?, ?, ?, ?, ?)",
		[
			message.chat.id,
			0,
			userData[message.chat.id]['address'],
			referral,
			userData[message.chat.id]['referrer']
		]
	)
	db.commit()
	bot.req(
		"sendMessage",
		data={
			"chat_id": message.chat.id,
			"text": Settings.MESSAGES['START'] % (referral, "0", "")
		}
	)

bot.polling()