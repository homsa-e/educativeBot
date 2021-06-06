import telebot
import Test
import User


class Room:
    def __init__(self, bot: telebot.TeleBot, iden, admin, name):
        self.id = iden
        self.name = name
        self.last_test = 0
        self.bot = bot
        self.admin_id = admin
        self.tests = []
        self.users = []
