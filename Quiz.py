import telebot
import random
import time


class Quiz:
    def __init__(self, bot: telebot.TeleBot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.stats = 0
        self.cbq_got = False
        self.cur_ques_time_begin = 0
        self.in_progress = False
        self.last_message = 0
        self.keys = [["Simple Math Sums", "Check the Sign"], ["Info", "Cancel"]]
        self.type = 0

    def math_quiz(self):
        self.in_progress = True
        self.cbq_got = False
        self.stats = 0
        self.bot.send_message(self.user_id, "The quiz shall begin now!",
                              reply_markup=telebot.types.ReplyKeyboardRemove())
        for i in range(10):
            if not self.in_progress:
                return
            a = random.randint(10, 99)
            b = random.randint(10, 99)
            c = random.randint(10, 99)
            r = a + b + c
            f1 = random.randint(r - 10, r - 1)
            f3 = random.randint(r + 6, r + 10)
            f2 = random.randint(r + 1, r + 5)
            markup = telebot.types.InlineKeyboardMarkup()
            ar = telebot.types.InlineKeyboardButton(text=f"{r}", callback_data='r')
            af1 = telebot.types.InlineKeyboardButton(text=f"{f1}", callback_data='f')
            af2 = telebot.types.InlineKeyboardButton(text=f"{f2}", callback_data='f')
            af3 = telebot.types.InlineKeyboardButton(text=f"{f3}", callback_data='f')
            answers = [ar, af1, af2, af3]
            random.shuffle(answers)
            markup.row(answers[0], answers[1])
            markup.row(answers[2], answers[3])
            m = self.bot.send_message(self.user_id, f"What is {a} + {b} + {c}?", reply_markup=markup)
            self.last_message = m.id
            self.cur_ques_time_begin = time.time()
            while not self.cbq_got and time.time() - self.cur_ques_time_begin < 20:
                continue
            if not self.cbq_got:
                self.bot.edit_message_text(m.text + " Time is up!", self.user_id, m.id,
                                           reply_markup=telebot.types.InlineKeyboardMarkup())
            self.cbq_got = False
        self.bot.send_message(self.user_id,
                              f"The Quiz is over! Your result is {self.stats} / 10 or "
                              f"{round(self.stats / 10 * 100, 2)}%")
        self.bot.send_message(self.user_id, "Now you play a new quiz or return to Main Menu!",
                              reply_markup=self.create_markup())
        self.in_progress = False

    def sign_quiz(self):
        self.in_progress = True
        self.cbq_got = False
        self.stats = 0
        self.bot.send_message(self.user_id, "The quiz shall begin now!",
                              reply_markup=telebot.types.ReplyKeyboardRemove())
        for i in range(10):
            if not self.in_progress:
                return
            a = random.randint(10, 99)
            b = random.randint(10, 99)
            c = random.randint(10, 99)
            d = random.randint(10, 99)
            e = random.randint(10, 99)
            f = random.randint(10, 99)
            num1 = a + b + c
            num2 = d + e + f
            if num1 > num2:
                gr = telebot.types.InlineKeyboardButton(text=">", callback_data='r>')
                eq = telebot.types.InlineKeyboardButton(text="=", callback_data='f>')
                less = telebot.types.InlineKeyboardButton(text="<", callback_data='f>')
            elif num1 == num2:
                gr = telebot.types.InlineKeyboardButton(text=">", callback_data='f=')
                eq = telebot.types.InlineKeyboardButton(text="=", callback_data='r=')
                less = telebot.types.InlineKeyboardButton(text="<", callback_data='f=')
            else:
                gr = telebot.types.InlineKeyboardButton(text=">", callback_data='f<')
                eq = telebot.types.InlineKeyboardButton(text="=", callback_data='f<')
                less = telebot.types.InlineKeyboardButton(text="<", callback_data='r<')
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row(less, eq, gr)
            m = self.bot.send_message(self.user_id, f"{a} + {b} + {c} ? {d} + {e} + {f}", reply_markup=markup)
            self.last_message = m.id
            self.cur_ques_time_begin = time.time()
            while not self.cbq_got and time.time() - self.cur_ques_time_begin < 20:
                continue
            if not self.cbq_got:
                self.bot.edit_message_text(m.text + " Time is up!", self.user_id, m.id,
                                           reply_markup=telebot.types.InlineKeyboardMarkup())
            self.cbq_got = False
        self.bot.send_message(self.user_id,
                              f"The Quiz is over! Your result is {self.stats} / 10 or {self.stats / 10 * 100}%")
        self.bot.send_message(self.user_id, "Now you play a new quiz or return to Main Menu!",
                              reply_markup=self.create_markup())
        self.in_progress = False

    def interrupt(self):
        self.in_progress = False
        self.cbq_got = True
        self.bot.send_message(self.user_id, "The Quiz was interrupted", reply_markup=self.create_markup())

    def cbq_react(self, call):
        if not self.in_progress or self.last_message != call.message.id:
            self.bot.answer_callback_query(call.id, "Error!")
            self.bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id,
                                       reply_markup=telebot.types.InlineKeyboardMarkup())
        elif self.type == 1:
            self.sign_cbq_react(call)
        else:
            self.math_cbq_react(call)

    def math_cbq_react(self, call):
        self.bot.answer_callback_query(call.id, "Accepted!")
        if call.data == 'r':
            self.bot.edit_message_text(call.message.text + " ✅", call.message.chat.id, call.message.id,
                                       reply_markup=telebot.types.InlineKeyboardMarkup())
            self.stats += 1
        else:
            self.bot.edit_message_text(call.message.text + " ❌", call.message.chat.id, call.message.id,
                                       reply_markup=telebot.types.InlineKeyboardMarkup())
        self.cbq_got = True

    def sign_cbq_react(self, call):
        self.bot.answer_callback_query(call.id, "Accepted!")
        if call.data[0] == 'r':
            self.bot.edit_message_text(call.message.text[0:call.message.text.find('?')] +
                                       call.data[1] + call.message.text[(call.message.text.find('?') + 1)::] + " ✅",
                                       call.message.chat.id, call.message.id,
                                       reply_markup=telebot.types.InlineKeyboardMarkup())
            self.stats += 1
        else:
            self.bot.edit_message_text(call.message.text[0:call.message.text.find('?')] +
                                       call.data[1] + call.message.text[(call.message.text.find('?') + 1)::] + " ❌",
                                       call.message.chat.id, call.message.id,
                                       reply_markup=telebot.types.InlineKeyboardMarkup())
        self.cbq_got = True

    def create_markup(self):
        markup = telebot.types.ReplyKeyboardMarkup(row_width=len(self.keys[0]))
        for r in self.keys:
            if len(r) == 2:
                markup.row(r[0], r[1])
            elif len(r) == 1:
                markup.row(r[0])
        return markup
