from telebot import types
import Quiz
import Test


class User:
    def __init__(self, bot, user_id, name, state=0, admin=False):
        self.id = user_id
        self.name = name
        self.state = state
        self.quiz = Quiz.Quiz(bot, user_id)
        self.test = Test.Test(bot, user_id)
        self.rooms = []
        self.new_room = False
        self.current_room = 0
        self.last_message = 0
        self.is_admin = admin
