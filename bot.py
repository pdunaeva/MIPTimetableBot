import telebot
import re
import requests
from bs4 import BeautifulSoup
import datetime
from telebot import types

access_token = "5308781999:AAH1g7_pFST8-oVp1TA3vZL-WlOh5-38QwY"

bot = telebot.TeleBot(access_token)

group = ''
group_hash = 0
all_groups = []

lessons = []
durations = []

time_slots = [["9:00", "9:40"], ["9:45", "10:25"],
              ["10:45", "11:25"], ["11:30", "12:10"],
              ["12:20", "13:00"], ["13:05", "13:45"],
              ["13:55", "14:35"], ["14:40", "15:20"],
              ["15:30", "16:10"], ["16:15", "16:55"],
              ["17:05", "17:45"], ["17:50", "18:30"],
              ["18:35", "19:15"], ["19:20", "20:00"]]

day_names = ["Понедельник", "Вторник", "Среда", "Четверг",
             "Пятница", "Суббота", "Воскресенье"]


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id,
                     text="Привет!\nЯ бот-помощник для студентов Физтеха. "
                          "Введи номер своей группы в формате Б01-001 и я "
                          "расскажу тебе про твое расписание.")
    bot.register_next_step_handler(message, get_group_and_hash)


def get_group_and_hash(message):
    global group
    global group_hash
    group = message.text.strip()

    url = "https://lms.mipt.ru/local/schedule/?embedded=1"

    if group == "Б01-001":
        group_hash = 3517
    else:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        ans = soup.find_all('option', text=group)

        if not ans:
            bot.send_message(message.chat.id,
                             text="Неправильный формат ввода или номер группы.")
            bot.send_message(message.chat.id,
                             text="Введи номер своей группы в формате Б01-001.")
            bot.register_next_step_handler(message, get_group_and_hash)
            return

        for s in str(ans[0]).split('"'):
            if s.isdigit():
                group_hash = int(s)
                break

    y_n_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but_yes = types.KeyboardButton("Да")
    but_no = types.KeyboardButton("Нет")
    y_n_markup.add(but_yes, but_no)
    bot.send_message(message.chat.id,
                     text=f"Твоя группа - {group}?", reply_markup=y_n_markup)
    bot.register_next_step_handler(message, y_n_group)


def y_n_group(message):
    if message.text == "Нет":
        bot.send_message(message.chat.id,
                         text="Давай попробуем еще раз.")
        bot.send_message(message.chat.id,
                         text="Введи номер своей группы в формате Б01-001.")
        bot.register_next_step_handler(message, get_group_and_hash)
    else:
        bot.send_message(message.chat.id, text="Ок")
        choose_different_schedule(message)


def choose_different_schedule(message):
    sched_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but_today = types.KeyboardButton("Расписание на сегодня")
    but_tomorrow = types.KeyboardButton("Расписание на завтра")
    but_week = types.KeyboardButton("Расписание на неделю")
    sched_markup.add(but_today, but_tomorrow, but_week)
    bot.send_message(message.chat.id,
                     text="Выбери внизу какое расписание ты хочешь посмотреть.",
                     reply_markup=sched_markup)
    bot.register_next_step_handler(message, get_schedule)


def get_schedule(message):
    url = "https://lms.mipt.ru/local/schedule/?cohort=0&year=2021" \
          "&semester=2&user=0&embedded=1&cohort=" + str(
        group_hash)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    days_1 = soup.find_all('td', class_='cell c1')
    days_2 = soup.find_all('td', class_='cell c2 lastcol')
    today = datetime.datetime.today().weekday()
    global lessons
    global durations

    if message.text == "Расписание на сегодня":

        if today == 6:
            bot.send_message(message.from_user.id,
                             text="Сегодня воскресенье, выходной, "
                                  "иди отдохни!")
            do_you_want_more(message)
            return

        lessons = []
        durations = []
        get_information(days_1, days_2, today)

        bot.send_message(message.from_user.id,
                         text="Расписание на сегодня:")

        first_slot = 0
        for i in range(len(lessons)):
            ans = create_lesson_texts(i, first_slot)
            first_slot = ans[0]
            if len(ans) == 1:
                continue
            title_text = ans[1]
            dur_text = ans[2]
            time_text = ans[3]
            bot.send_message(message.chat.id,
                             text=title_text + "Продолжительность:" +
                                  dur_text + time_text)

    elif message.text == "Расписание на завтра":

        today = (today + 1) % 7

        if today == 6:
            bot.send_message(message.from_user.id,
                             text="Завтра воскресенье, ура-ура!")
            do_you_want_more(message)
            return

        lessons = []
        durations = []
        get_information(days_1, days_2, today)

        bot.send_message(message.from_user.id,
                         text="Расписание на завтра:")

        first_slot = 0
        for i in range(len(lessons)):
            ans = create_lesson_texts(i, first_slot)
            first_slot = ans[0]
            if len(ans) == 1:
                continue
            title_text = ans[1]
            dur_text = ans[2]
            time_text = ans[3]
            bot.send_message(message.chat.id,
                             text=title_text + "Продолжительность:" +
                                  dur_text + time_text)

    else:
        for today in range(6):

            lessons = []
            durations = []
            get_information(days_1, days_2, today)

            final_text = day_names[today] + ":\n" + "--------" + '\n'

            first_slot = 0
            for i in range(len(lessons)):
                ans = create_lesson_texts(i, first_slot)
                first_slot = ans[0]
                if len(ans) == 1:
                    continue
                title_text = ans[1]
                dur_text = ans[2]
                time_text = ans[3]
                final_text = final_text + time_text + ' ' + \
                             title_text + "--------" + '\n'

            bot.send_message(message.chat.id, text=final_text)

    do_you_want_more(message)


def do_you_want_more(message):
    more_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but_more = types.KeyboardButton("Да")
    but_nomore = types.KeyboardButton("Нет")
    more_markup.add(but_more, but_nomore)
    bot.send_message(message.chat.id,
                     text="Хочешь еще что-то посмотреть для этой группы?",
                     reply_markup=more_markup)
    bot.register_next_step_handler(message, more_or_no_choice)


def more_or_no_choice(message):
    if message.text == "Да":
        bot.send_message(message.chat.id, text="Ок")
        choose_different_schedule(message)
    else:
        rem = telebot.types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id,
                         text="Если передумаешь, введи /start",
                         reply_markup=rem)


def get_information(days_1, days_2, today):
    global lessons
    global durations
    if today < 3:
        day = days_1[today]
    else:
        day = days_2[today - 3]

    # нашли названия всех модулей в расписании
    lessons = day.find_all('a', class_="mini-schedule-link")

    # теперь хотим найти продолжительность
    with_durations = day.find_all('div',
                                  class_=re.compile('^mini-schedule-activity'))
    for i in range(len(with_durations)):
        index = str(with_durations[i]).find('duration')
        if str(with_durations[i])[index + 10] != ' ':
            durations.append(int(str(with_durations[i])[index + 9]) * 10 +
                             int(str(with_durations[i])[index + 10]))
        else:
            durations.append(int(str(with_durations[i])[index + 9]))


def create_lesson_texts(number, first_slot):
    title = lessons[number].text
    title_arr = title.split('—')
    for j in range(len(title_arr)):
        title_arr[j] = title_arr[j].lstrip()
        title_arr[j] = title_arr[j].rstrip()
        title_arr[j] = title_arr[j].replace('\t', ' ')
        title_arr[j] = title_arr[j].replace('\n', ' ')
    title_text = ''
    if len(title_arr) == 1:
        title_text = title_arr[0] + '\n'
    else:
        title_text = title_arr[1] + '\n' + title_arr[0] + '\n'

    if title_text == "Перерыв\n":
        first_slot = first_slot + durations[number]
        return [first_slot]

    slots = durations[number]
    time_text = time_slots[first_slot][0] + \
                " - " + time_slots[first_slot + slots - 1][1]
    first_slot = first_slot + slots
    if durations[number] % 2 == 0:
        dur = durations[number] // 2
        if dur == 1:
            dur_text = " пара"
        elif dur == 2 or dur == 3 or dur == 4:
            dur_text = " пары"
        else:
            dur_text = " пар"
    else:
        dur = durations[number] / 2
        dur_text = " пары"

    dur_text = str(dur) + dur_text + '\n'
    return [first_slot, title_text, dur_text, time_text]


@bot.message_handler(content_types=['text'])
def func(message):
    bot.send_message(message.chat.id, "Введи команду /start ")


if __name__ == '__main__':
    bot.polling(non_stop=True)
