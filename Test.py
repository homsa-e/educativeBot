import telebot
import json
import random
import time


class Test:
    def __init__(self, bot: telebot.TeleBot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.counter = 0
        self.cbq_got = False
        self.cur_ques_time_begin = 0
        self.in_progress = False
        self.last_message = None
        self.current_room = 0
        self.file = ""
        self.data = None
        self.user_stat = {}
        self.keys = [["Tests", "My Statistics"], ["Leave"]]

    def create_markup(self):
        markup = telebot.types.ReplyKeyboardMarkup(row_width=len(self.keys[0]))
        for k in self.keys:
            if len(k) == 2:
                markup.row(k[0], k[1])
            elif len(k) == 1:
                markup.row(k[0])
        return markup

    def launch(self):
        self.in_progress = True
        self.cbq_got = False
        self.counter = 0
        if not self.parse_questions():
            return
        self.bot.send_message(self.user_id, "The test shall begin now!",
                              reply_markup=telebot.types.ReplyKeyboardRemove())
        for d in self.data.values():
            if not self.in_progress:
                return
            markup = telebot.types.InlineKeyboardMarkup()
            buttons = list()
            answers = d["answers"]
            buttons.append(telebot.types.InlineKeyboardButton(text=answers[0], callback_data='r'))
            for i in range(1, len(answers)):
                buttons.append((telebot.types.InlineKeyboardButton(text=answers[i], callback_data='f')))
            random.shuffle(buttons)
            if len(buttons) % 2:
                for i in range(0, len(buttons) - 1, 2):
                    markup.row(buttons[i], buttons[i + 1])
                markup.row(buttons[len(buttons) - 1])
            else:
                for i in range(0, len(buttons), 2):
                    markup.row(buttons[i], buttons[i + 1])
            self.last_message = self.bot.send_message(self.user_id, d["text"], reply_markup=markup)
            self.cur_ques_time_begin = time.time()
            while not self.cbq_got and time.time() - self.cur_ques_time_begin < 20:
                continue
            if not self.cbq_got:
                self.bot.edit_message_text(self.last_message.text + " Time is up!", self.user_id, self.last_message.id,
                                           reply_markup=telebot.types.InlineKeyboardMarkup())
            self.cbq_got = False
        if self.user_stat.get(str(self.current_room)) is None:
            self.user_stat[str(self.current_room)] = dict()
        if self.user_stat[str(self.current_room)].get(self.file[-6:-5]) is None:
            self.user_stat[str(self.current_room)][self.file[-6:-5]] = list()
        self.user_stat[str(self.current_room)][self.file[-6:-5]].append([self.counter, len(self.data.values())])
        self.bot.send_message(self.user_id,
                              f"The test is over! Your result is {self.counter} / {len(self.data.values())} or "
                              f"{round(self.counter / len(self.data.items()) * 100, 2)}%",
                              reply_markup=self.create_markup())
        self.in_progress = False

    def give_statistics(self, r):
        room = self.user_stat.get(str(r))
        if room is None:
            return ""
        # print(room)
        msg = f""
        for test, results in room.items():
            # print(results)
            s = 0
            m = 0
            q = results[0][1]
            for result in results:
                s += result[0]
                if result[0] > m:
                    m = result[0]
            s /= len(results)
            s = round(s, 2)
            msg += f"Test {test} – average score is ({s}/{q}), best attempt is ({m}/{q})\n"
        return msg

    def give_admin_statistics(self, r):
        room = self.user_stat[str(r)]
        # print(room)
        msg = f""
        for test, results in room.items():
            # print(results)
            q = results[0][1]
            msg += f"Test {test} - first attempt: ({results[0][0]}/{q}), " \
                   f"last attempt: ({results[len(results) - 1][0]}/{q}), " \
                   f"number of attempts: {len(results)}\n"
        return msg

    def interrupt(self):
        self.in_progress = False
        self.cbq_got = True
        self.bot.send_message(self.user_id, "The test was interrupted", reply_markup=self.create_markup())

    def cbq_react(self, call):
        if not self.in_progress or self.last_message.id != call.message.id:
            # print(self.last_message, call.message.id)
            self.bot.answer_callback_query(call.id, "Error!")
            self.bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id,
                                       reply_markup=telebot.types.InlineKeyboardMarkup())
        elif call.data == 'r':
            self.bot.answer_callback_query(call.id, "Right!")
            self.bot.edit_message_text(call.message.text + " ✅", call.message.chat.id, call.message.id,
                                       reply_markup=telebot.types.InlineKeyboardMarkup())
            self.counter += 1
            self.cbq_got = True
        else:
            self.bot.answer_callback_query(call.id, "Wrong!")
            self.bot.edit_message_text(call.message.text + " ❌", call.message.chat.id, call.message.id,
                                       reply_markup=telebot.types.InlineKeyboardMarkup())
            self.cbq_got = True

    def parse_questions(self):
        with open(self.file) as f:
            try:
                self.data = json.load(f)
            except json.decoder.JSONDecodeError:
                self.bot.send_message(self.user_id, "The test is broken. Please, address your tutor")
                self.interrupt()
                return False
            # print(self.data)
            f.close()
        return True
