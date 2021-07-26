from telebot import types
import telebot
import json
import User
import os
import Room
import threading

TOKEN = "1767240235:AAErtjlNc0XvApBY3MmKCfqExXDDWkKgQYA"
bot = telebot.TeleBot(TOKEN)
MAIN, QUIZ, ROOMS, MANAGE, INROOM, ADMIN_ROOM = range(6)
with open("users.json") as f:
    userDB = json.load(f)
    f.close()

with open("rooms.json") as r:
    roomDB = json.load(r)
    r.close()

users = dict()
rooms = dict()

for index, row in userDB.items():
    users[int(index)] = User.User(bot, int(index), row['name'], row['state'], row['is_admin'])
    users[int(index)].rooms = row['rooms']
    users[int(index)].current_room = row['current_room']
    users[int(index)].test.user_stat = row['statistics']

for index, row in roomDB.items():
    rooms[int(index)] = Room.Room(bot, int(index), row['admin'], row['name'])
    rooms[int(index)].users = row['users']
    rooms[int(index)].last_test = row['last_test']
    rooms[int(index)].tests = row['tests']

# print(users)
# print(rooms)
# for key, value in rooms.items():
#     print(value.id, value.users, value.tests)
#
# for key, value in users.items():
#     print(value.id, value.current_room, value.name)


def save_states():
    for user in users.keys():
        userDB[str(user)]['state'] = users[user].state
        userDB[str(user)]['is_admin'] = users[user].is_admin
        userDB[str(user)]['current_room'] = users[user].current_room
        userDB[str(user)]['name'] = users[user].name
        userDB[str(user)]['rooms'] = users[user].rooms
        userDB[str(user)]['statistics'] = users[user].test.user_stat
    for room in rooms.keys():
        roomDB[str(room)] = dict()
        roomDB[str(room)]['users'] = rooms[room].users
        roomDB[str(room)]['tests'] = rooms[room].tests
        roomDB[str(room)]['name'] = rooms[room].name
        roomDB[str(room)]['admin'] = rooms[room].admin_id
        roomDB[str(room)]['last_test'] = rooms[room].last_test
    with open("users.json", "w") as out:
        json.dump(userDB, out, indent=4)
        out.close()
    with open("rooms.json", "w") as room_out:
        json.dump(roomDB, room_out, indent=4)
        room_out.close()


main_menu_keys = [["Quizzes", "My Rooms"], ["Rooms manager (for admins)"]]
rooms_menu_keys = [["Enter a new room", "Cancel"]]
inroom_keys = [["Tests", "My Statistics"], ["Leave"]]
admin_menu_keys = [["Create new room", "Rooms statistics"], ["Edit rooms", "Cancel"]]
admin_room_keys = [["Add a test", "Delete a test"], ["How to add a test?", "Leave"]]


def create_markup(keys):
    markup = types.ReplyKeyboardMarkup(row_width=len(keys[0]))
    for k in keys:
        if len(k) == 2:
            markup.row(k[0], k[1])
        elif len(k) == 1:
            markup.row(k[0])
    return markup


def room_markup(user_id):
    user = users[user_id]
    markup = types.InlineKeyboardMarkup()
    for room in user.rooms:
        btn = types.InlineKeyboardButton(text=f"{rooms[int(room)].name}", callback_data=f"{room}")
        markup.row(btn)
    return markup


def admin_markup(admin_id):
    markup = types.InlineKeyboardMarkup()
    for room in rooms.values():
        if room.admin_id == admin_id:
            btn = types.InlineKeyboardButton(text=f"{room.name}", callback_data=f"{room.id}")
            markup.row(btn)
    return markup


def test_markup(room_id):
    room = rooms[room_id]
    markup = types.InlineKeyboardMarkup()
    for test in room.tests:
        btn = types.InlineKeyboardButton(text=f"{test}", callback_data=f"{test}")
        markup.row(btn)
    return markup


@bot.message_handler(commands=['start'])
def start_message(message):
    username = str(message.from_user.first_name) + " " + str(message.from_user.last_name)
    user_id = message.from_user.id
    if users.get(user_id) is None:
        users[user_id] = User.User(bot, message.from_user.id, username)
        userDB[str(user_id)] = dict()
        # print(userDB)
    else:
        user = users[user_id]
        if user.quiz.in_progress or user.test.in_progress or user.new_room:
            main_handler(message)
            return
    bot.send_message(user_id, f'Hello, {username}!', reply_markup=types.ReplyKeyboardRemove())
    bot.send_message(user_id, "Please, choose:", reply_markup=create_markup(main_menu_keys))
    users[user_id].state = MAIN
    save_states()


@bot.message_handler(content_types=['text'])
def main_handler(message):
    user = users.get(message.chat.id)
    if user is None:
        bot.send_message(message.chat.id,
                         "Your account is not present in the database, please enter /start to register")
    elif user.state == MAIN:
        main_menu(message)
    elif user.state == QUIZ:
        quiz_menu(message)
    elif user.state == ROOMS:
        rooms_menu(message)
    elif user.state == MANAGE:
        admin_menu(message)
    elif user.state == INROOM:
        inroom_menu(message)
    elif user.state == ADMIN_ROOM:
        admin_room_menu(message)
    save_states()


def main_menu(message):
    user = users[message.from_user.id]
    if message.text == "Quizzes":
        bot.send_message(message.chat.id, "Welcome to Quizzes!", reply_markup=create_markup(user.quiz.keys))
        user.state = QUIZ
    elif message.text == "My Rooms":
        bot.send_message(message.chat.id, "Here is the list of your Rooms", reply_markup=create_markup(rooms_menu_keys))
        m = bot.send_message(message.chat.id, f"{message.from_user.first_name}'s rooms:",
                             reply_markup=room_markup(user.id))
        user.last_message = m.id
        user.state = ROOMS
    elif message.text == "Rooms manager (for admins)":
        if user.is_admin:
            m = bot.send_message(message.chat.id, "Welcome to the Rooms Manager!",
                                 reply_markup=create_markup(admin_menu_keys))
            user.last_message = m.id
            user.state = MANAGE
        else:
            bot.send_message(message.chat.id,
                             "Access denied. If you would like to get a Tutor account, please, address @chelseafan16")
    else:
        bot.send_message(message.chat.id, "Please, choose one of the options below",
                         reply_markup=create_markup(main_menu_keys))


def quiz_menu(message):
    user = users[message.from_user.id]
    if user.quiz.in_progress:
        if message.text != "/stop":
            bot.send_message(message.chat.id, 'If you want to stop the Quiz, please, type "/stop"')
        else:
            user.quiz.interrupt()
    elif message.text == "Simple Math Sums":
        user.quiz.type = 0
        t = threading.Thread(target=user.quiz.math_quiz)
        t.start()
    elif message.text == "Check the Sign":
        user.quiz.type = 1
        t = threading.Thread(target=user.quiz.sign_quiz)
        t.start()
    elif message.text == "Cancel":
        bot.send_message(message.chat.id, "You returned to main menu", reply_markup=create_markup(main_menu_keys))
        user.state = MAIN
    elif message.text == "Info":
        bot.send_message(message.chat.id, 'In "Simple Math Sums" you need to calculate the sum of 3 numbers and click '
                                          'the right option.\n"Check the Sign" requires you to click the correct '
                                          'sign that can be put into the expression. For each question you have 20 '
                                          'seconds to answer.')
    else:
        bot.send_message(message.chat.id, "Choose the quiz or click Cancel")


def rooms_menu(message):
    user = users[message.from_user.id]
    if user.new_room:
        if message.text.isnumeric():
            if rooms.get(int(message.text)) is not None and message.text not in user.rooms:
                bot.send_message(message.chat.id, "Welcome!", reply_markup=create_markup(inroom_keys))
                user.new_room = False
                user.current_room = int(message.text)
                user.state = INROOM
                user.rooms.append(message.text)
                rooms[int(message.text)].users.append(user.id)
            else:
                bot.send_message(message.chat.id, "Invalid room number. Try again")
        elif message.text == "Cancel":
            user.new_room = False
            bot.send_message(message.chat.id, "Cancelled", reply_markup=create_markup(rooms_menu_keys))
        else:
            bot.send_message(message.chat.id, "Type the number of a room you'd like to enter or click Cancel")
    elif message.text == "Cancel":
        bot.send_message(message.chat.id, "You returned to main menu", reply_markup=create_markup(main_menu_keys))
        user.state = MAIN
    elif message.text == "Enter a new room":
        user.new_room = True
        bot.send_message(message.chat.id, "Enter the room number:", reply_markup=create_markup([['Cancel']]))
    else:
        bot.send_message(message.chat.id, "Sorry, I don't understand you:(")


def admin_menu(message):
    user = users[message.from_user.id]
    if user.new_room:
        if message.text != "Cancel":
            # print(len(rooms.items()))
            rooms[len(rooms.items()) + 1] = Room.Room(bot, len(rooms.items()) + 1, user.id, message.text)
            room = rooms[len(rooms.items())]
            user.new_room = False
            bot.send_message(message.chat.id, f"The room was created with name {message.text} and ID {room.id}",
                             reply_markup=create_markup(admin_menu_keys))
            os.mkdir(f"rooms/{room.id}")
            os.mkdir(f"rooms/{room.id}/tests")
            # print(rooms)
        else:
            user.new_room = False
            bot.send_message(message.chat.id, "Cancelled", reply_markup=create_markup(admin_menu_keys))
    elif message.text == "Cancel":
        bot.send_message(message.chat.id, "You returned to main menu", reply_markup=create_markup(main_menu_keys))
        user.state = MAIN
    elif message.text == "Create new room":
        user.new_room = True
        bot.send_message(message.chat.id, "Give the room a name: ", reply_markup=create_markup([["Cancel"]]))
    elif message.text == "Edit rooms":
        m = bot.send_message(message.chat.id, "Choose a room you want to edit:", reply_markup=admin_markup(user.id))
        user.last_message = m.id
    elif message.text == "Rooms statistics":
        m = bot.send_message(message.chat.id, "Choose a room:", reply_markup=admin_markup(user.id))
        user.last_message = m.id
    else:
        bot.send_message(message.chat.id, "Under dev...", reply_markup=create_markup(admin_menu_keys))


def inroom_menu(message):
    user = users[message.from_user.id]
    if user.test.in_progress:
        if message.text != "/stop":
            bot.send_message(message.chat.id, 'If you want to stop the test, please, type "/stop"')
        else:
            user.test.interrupt()
    elif message.text == "Leave":
        bot.send_message(message.chat.id, "You left the room", reply_markup=create_markup(rooms_menu_keys))
        m = bot.send_message(message.chat.id, f"{message.from_user.first_name}'s rooms:",
                             reply_markup=room_markup(user.id))
        user.last_message = m.id
        user.state = ROOMS
    elif message.text == "Tests":
        m = bot.send_message(message.chat.id, "Here are the tests of the room:",
                             reply_markup=test_markup(user.current_room))
        user.last_message = m.id
    elif message.text == "My Statistics":
        bot.send_message(message.chat.id, f'Your statistics in room "{rooms[user.current_room].name}":\n'
                         + user.test.give_statistics(user.current_room))


def admin_room_menu(message):
    user = users[message.from_user.id]
    if user.new_room:
        if message.text == "Cancel":
            bot.send_message(message.chat.id, 'Cancelled', reply_markup=create_markup(admin_room_keys))
            user.new_room = False
        else:
            bot.send_message(message.chat.id, 'Upload a file or click "Cancel"')
    elif message.text == "Leave":
        bot.send_message(message.chat.id, "You returned to Admin menu", reply_markup=create_markup(admin_menu_keys))
        user.current_room = 0
        user.state = MANAGE
    elif message.text == "How to add a test?":
        bot.send_message(message.chat.id, 'In order to add a test to the room, you have to edit the following file,'
                                          ' fulfilling it with your questions and answers, and upload it.\n'
                                          'For each question you '
                                          'should set its text after the "text" key, and put all the answer options '
                                          'into [ ] brackets after "answers" key.\nPlease, note, the first answer will'
                                          ' be counted as the right one (the answers will be shuffled for the '
                                          'students). You may remove all unnecessary questions or add more of them '
                                          'by copying the existing ones.')
        bot.send_document(message.chat.id, open("test.json"))
    elif message.text == "Add a test":
        m = bot.send_message(message.chat.id, 'Waiting for a file...', reply_markup=create_markup([['Cancel']]))
        user.new_room = True
        user.last_message = m.id
    elif message.text == "Delete a test":
        bot.send_message(message.chat.id, "Choose a test you would like to delete",
                         reply_markup=create_markup([["Cancel"]]))
        m = bot.send_message(message.chat.id, f'Tests of room "{rooms[user.current_room].name}"',
                             reply_markup=test_markup(rooms[user.current_room].id))
        user.last_message = m.id

    elif message.text == "Cancel":
        m = bot.send_message(message.chat.id, 'Cancelled', reply_markup=create_markup(admin_room_keys))
        user.last_message = m.id
    else:
        bot.send_message(message.chat.id, "Sorry, I don't understand you:(")


@bot.message_handler(content_types=['document'])
def add_test(message):
    user = users[message.from_user.id]
    if user.state == ADMIN_ROOM and user.new_room:
        lt = rooms[user.current_room].last_test
        file_info = bot.get_file(message.document.file_id)
        df = bot.download_file(file_info.file_path)
        with open(f"rooms/{user.current_room}/tests/{lt + 1}.json", "wb") as new_test:
            new_test.write(df)
        bot.send_message(message.chat.id, "File accepted", reply_markup=create_markup(admin_room_keys))
        user.new_room = False
        rooms[user.current_room].tests.append(f"{lt + 1}")
        rooms[user.current_room].last_test += 1
    else:
        bot.send_message(message.chat.id, "Error")
    save_states()


@bot.callback_query_handler(func=lambda x: True)
def cbq(call):
    if users.get(call.message.chat.id) is not None:
    	user = users[call.message.chat.id]
    else:
        bot.answer_callback_query(call.id, text="Error!")
        bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id,
                              reply_markup=telebot.types.InlineKeyboardMarkup())
        return
    if user.state == QUIZ:
        user.quiz.cbq_react(call)
    elif user.state == ROOMS:
        if call.message.id == user.last_message and rooms[int(call.data)] is not None:
            bot.answer_callback_query(call.id, text="Access granted!")
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, f"You've entered room №{call.data}",
                             reply_markup=create_markup(inroom_keys))
            user.new_room = False
            user.current_room = int(call.data)
            # print(user.current_room)
            user.state = INROOM
        else:
            bot.answer_callback_query(call.id, text="Error!")
            bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id,
                                  reply_markup=telebot.types.InlineKeyboardMarkup())
    elif user.state == INROOM and user.test.in_progress:
        user.test.cbq_react(call)
    elif user.state == INROOM:
        if call.data in rooms[user.current_room].tests and call.message.id == user.last_message:
            bot.answer_callback_query(call.id, text="Accepted")
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, f"You chose test № {call.data}")
            user.test.file = f"rooms/{user.current_room}/tests/{call.data}.json"
            user.test.current_room = user.current_room
            t = threading.Thread(target=user.test.launch)
            t.start()
        else:
            bot.answer_callback_query(call.id, text="Error!")
            bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id,
                                  reply_markup=telebot.types.InlineKeyboardMarkup())
    elif user.state == MANAGE:
        if call.message.id == user.last_message:
            if call.message.text == "Choose a room:":
                bot.answer_callback_query(call.id, text="Accepted!")
                students = rooms[int(call.data)].users
                bot.send_message(call.message.chat.id, f'Statistics for room {rooms[int(call.data)].name}:')
                for iden in students:
                    msg = f""
                    st = users[iden]
                    msg += f"{st.name}:\n"
                    bot.send_message(call.message.chat.id, msg + st.test.give_admin_statistics(int(call.data)))
            else:
                bot.answer_callback_query(call.id, text="Access granted!")
                bot.delete_message(call.message.chat.id, call.message.id)
                bot.send_message(call.message.chat.id, f"You are editing room {rooms[int(call.data)].name}",
                                 reply_markup=create_markup(admin_room_keys))
                user.state = ADMIN_ROOM
                user.current_room = int(call.data)
        else:
            bot.answer_callback_query(call.id, text="Error!")
            bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id,
                                  reply_markup=telebot.types.InlineKeyboardMarkup())
    elif user.state == ADMIN_ROOM:
        if call.message.id == user.last_message and call.data in rooms[user.current_room].tests:
            bot.answer_callback_query(call.id, text="Success!")
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id, f"Test №{call.data} was successfully deleted", 
                             reply_markup=create_markup(admin_room_keys))
            os.remove(f"rooms/{user.current_room}/tests/{call.data}.json")
            rooms[user.current_room].tests.remove(call.data)
        else:
            bot.answer_callback_query(call.id, text="Error!")
            bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id,
                                  reply_markup=telebot.types.InlineKeyboardMarkup())
    else:
        bot.answer_callback_query(call.id, text="Error!")
        bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id,
                              reply_markup=telebot.types.InlineKeyboardMarkup())
    save_states()


bot.polling(none_stop=True, interval=0)
