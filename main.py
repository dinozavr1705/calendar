import json
import threading
import time
from customtkinter import *
import calendar
from datetime import datetime
from tkinter import *
from plyer import notification
import os

a = open("праздники.txt")
b = a.readlines()
months = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
}

with open("holidays.json", "r", encoding="utf-8") as f:
    holidays_json = json.load(f)

holidays = {}
for date, description in holidays_json.items():
    month, day = map(int, date.split("-"))
    holidays[(month, day)] = description

def has_visited_today():
    today = datetime.now().date()
    with open("last_visit.txt", "r") as f:
        last_visit = f.read().strip()
        return last_visit == str(today)

def save_last_visit():
    today = datetime.now().date()
    with open("last_visit.txt", "w") as f:
        f.write(str(today))

def show_congratulations():
    current_events = holidays.get((month, day), [])
    congratulation_window = Toplevel(app)
    congratulation_window.title("Поздравление")

    if (month, day) in holidays:
        congratulation_message = f"Поздравляем с праздником: {holidays[(month, day)][0]}!"
        Label(congratulation_window, text=congratulation_message, font=('Arial', 14)).pack(padx=20, pady=20)

        if len(current_events)>1:
            events_message = "У вас есть события сегодня:\n" + "\n".join(current_events[1:len(current_events)])
            Label(congratulation_window, text=events_message, font=('Arial', 12)).pack(padx=20, pady=10)

        Button(congratulation_window, text="Перейти в календарь",
               command=lambda: [congratulation_window.destroy(), app.deiconify()]).pack(pady=10)
    else:
        Label(congratulation_window, text="Сегодня нет праздников.", font=('Arial', 14)).pack(padx=20, pady=20)
        Button(congratulation_window, text="Перейти в календарь",
               command=lambda: [congratulation_window.destroy(), app.deiconify()]).pack(pady=10)

def show_holiday(day):
    current_events = holidays.get((month, day), [])
    holiday_window = Toplevel(app)
    holiday_window.title(f"Праздник {day} {calendar.month_name[month]}")
    Label(holiday_window, text="Текущие события:", font=('Arial', 14)).pack(padx=20, pady=10)

    event_labels = []
    for event in current_events:
        label = Label(holiday_window, text=event, font=('Arial', 12))
        label.pack(padx=20, pady=5)
        event_labels.append(label)

    text_entry = Text(holiday_window, height=5, width=30, font=('Arial', 12))
    text_entry.pack(padx=20, pady=10)

    def add_event():
        event_text = text_entry.get("1.0", END).strip()
        if event_text:
            current_events.append(event_text)
            holidays[(month, day)] = current_events

            with open("holidays.json", "w", encoding="utf-8") as f:
                json.dump({f"{m}-{d}": e for (m, d), e in holidays.items()}, f, ensure_ascii=False, indent=4)

            label = Label(holiday_window, text=event_text, font=('Arial', 12))
            label.pack(padx=20, pady=5)
            event_labels.append(label)
            text_entry.delete("1.0", END)

    def delete_event(event_label):
        event_text = event_label.cget("text")
        current_events.remove(event_text)
        holidays[(month, day)] = current_events

        with open("holidays.json", "w", encoding="utf-8") as f:
            json.dump({f"{m}-{d}": e for (m, d), e in holidays.items()}, f, ensure_ascii=False, indent=4)

        event_label.destroy()
        event_labels.remove(event_label)

    add_button = Button(holiday_window, text="Добавить событие", command=add_event)
    add_button.pack(pady=10)

    delete_button = Button(holiday_window, text="Удалить событие",
                           command=lambda: delete_event(event_labels[-1]) if event_labels else None)
    delete_button.pack(pady=10)

    close_button = Button(holiday_window, text="Закрыть", command=holiday_window.destroy)
    close_button.pack(pady=5)

def fill():
    info_label['text'] = calendar.month_name[month] + ', ' + str(year)
    month_days = calendar.monthrange(year, month)[1]
    if month == 1:
        back_month_days = calendar.monthrange(year - 1, 12)[1]
    else:
        back_month_days = calendar.monthrange(year, month - 1)[1]
    week_day = calendar.monthrange(year, month)[0]

    for i in range(month_days):
        current_pos = i + week_day
        day_text = str(i + 1)
        day_button = Button(app, text=day_text, width=4, height=2, font='Arial 16 bold', bg='grey',
                            command=lambda day=i + 1: show_holiday(day))
        day_button.grid(row=(current_pos // 7) + 2, column=current_pos % 7, sticky=NSEW)
        current_day_week = (week_day + i) % 7
        day_button['fg'] = 'red' if current_day_week in (5, 6) else 'black'
        if year == now.year and month == now.month and (i + 1) == now.day:
            day_button['bg'] = 'white'
            day_button['fg'] = 'green'
        else:
            day_button['bg'] = 'grey'

    for n in range(week_day):
        days[week_day - n - 1].config(text=back_month_days - n, fg='gray', bg='#f3f3f3')
    for n in range(6 * 7 - month_days - week_day):
        days[week_day + month_days + n].config(text=n + 1, fg='gray', bg='#f3f3f3')

def prew():
    global month, year
    month -= 1
    if month == 0:
        month = 12
        year -= 1
    fill()

def next():
    global month, year
    month += 1
    if month == 13:
        month = 1
        year += 1
    fill()

def is_holiday(month, day):
    return (month, day) in holidays

months = ["yanvar", "fevral", "mart", "aprel", "may", "iyun",
          "iyul", "avgust", "sentyabr", "oktyabr", "noyabr", "dekabr"]

now = datetime.now()
days = []
day = now.day
month = now.month
year = now.year

app = Tk()
app.withdraw()

if has_visited_today():
    app.deiconify()
else:
    show_congratulations()
    save_last_visit()

back_button = Button(app, text="<", command=prew)
back_button.grid(row=0, column=0, sticky=NSEW)

next_button = Button(app, text=">", command=next)
next_button.grid(row=0, column=6, sticky=NSEW)


info_label = Label(app, text='0', font='Arial 16 bold', fg='blue')
info_label.grid(row=0, column=1, columnspan=5, sticky=NSEW)

for i in range(7):
    Label(app, text=calendar.day_abbr[i], font='Arial 10 bold', fg='darkblue').grid(row=1, column=i, sticky=NSEW)
import json
import threading
import time
from customtkinter import *
import calendar
from datetime import datetime
from tkinter import *
from plyer import notification
import os

a = open("праздники.txt")
b = a.readlines()
months = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
}

with open("holidays.json", "r", encoding="utf-8") as f:
    holidays_json = json.load(f)

holidays = {}
for date, description in holidays_json.items():
    month, day = map(int, date.split("-"))
    holidays[(month, day)] = description

def has_visited_today():
    today = datetime.now().date()
    with open("last_visit.txt", "r") as f:
        last_visit = f.read().strip()
        return last_visit == str(today)

def save_last_visit():
    today = datetime.now().date()
    with open("last_visit.txt", "w") as f:
        f.write(str(today))

def show_congratulations():
    current_events = holidays.get((month, day), [])
    congratulation_window = Toplevel(app)
    congratulation_window.title("Поздравление")

    if (month, day) in holidays:
        congratulation_message = f"Поздравляем с праздником: {holidays[(month, day)][0]}!"
        Label(congratulation_window, text=congratulation_message, font=('Arial', 14)).pack(padx=20, pady=20)

        if len(current_events)>1:
            events_message = "У вас есть события сегодня:\n" + "\n".join(current_events[1:len(current_events)])
            Label(congratulation_window, text=events_message, font=('Arial', 12)).pack(padx=20, pady=10)

        Button(congratulation_window, text="Перейти в календарь",
               command=lambda: [congratulation_window.destroy(), app.deiconify()]).pack(pady=10)
    else:
        Label(congratulation_window, text="Сегодня нет праздников.", font=('Arial', 14)).pack(padx=20, pady=20)
        Button(congratulation_window, text="Перейти в календарь",
               command=lambda: [congratulation_window.destroy(), app.deiconify()]).pack(pady=10)

def show_holiday(day):
    current_events = holidays.get((month, day), [])
    holiday_window = Toplevel(app)
    holiday_window.title(f"Праздник {day} {calendar.month_name[month]}")
    Label(holiday_window, text="Текущие события:", font=('Arial', 14)).pack(padx=20, pady=10)

    event_labels = []
    for event in current_events:
        label = Label(holiday_window, text=event, font=('Arial', 12))
        label.pack(padx=20, pady=5)
        event_labels.append(label)

    text_entry = Text(holiday_window, height=5, width=30, font=('Arial', 12))
    text_entry.pack(padx=20, pady=10)

    def add_event():
        event_text = text_entry.get("1.0", END).strip()
        if event_text:
            current_events.append(event_text)
            holidays[(month, day)] = current_events

            with open("holidays.json", "w", encoding="utf-8") as f:
                json.dump({f"{m}-{d}": e for (m, d), e in holidays.items()}, f, ensure_ascii=False, indent=4)

            label = Label(holiday_window, text=event_text, font=('Arial', 12))
            label.pack(padx=20, pady=5)
            event_labels.append(label)
            text_entry.delete("1.0", END)

    def delete_event(event_label):
        event_text = event_label.cget("text")
        current_events.remove(event_text)
        holidays[(month, day)] = current_events

        with open("holidays.json", "w", encoding="utf-8") as f:
            json.dump({f"{m}-{d}": e for (m, d), e in holidays.items()}, f, ensure_ascii=False, indent=4)

        event_label.destroy()
        event_labels.remove(event_label)

    add_button = Button(holiday_window, text="Добавить событие", command=add_event)
    add_button.pack(pady=10)

    delete_button = Button(holiday_window, text="Удалить событие",
                           command=lambda: delete_event(event_labels[-1]) if event_labels else None)
    delete_button.pack(pady=10)

    close_button = Button(holiday_window, text="Закрыть", command=holiday_window.destroy)
    close_button.pack(pady=5)

def fill():
    info_label['text'] = calendar.month_name[month] + ', ' + str(year)
    month_days = calendar.monthrange(year, month)[1]
    if month == 1:
        back_month_days = calendar.monthrange(year - 1, 12)[1]
    else:
        back_month_days = calendar.monthrange(year, month - 1)[1]
    week_day = calendar.monthrange(year, month)[0]

    for i in range(month_days):
        current_pos = i + week_day
        day_text = str(i + 1)
        day_button = Button(app, text=day_text, width=4, height=2, font='Arial 16 bold', bg='grey',
                            command=lambda day=i + 1: show_holiday(day))
        day_button.grid(row=(current_pos // 7) + 2, column=current_pos % 7, sticky=NSEW)
        current_day_week = (week_day + i) % 7
        day_button['fg'] = 'red' if current_day_week in (5, 6) else 'black'
        if year == now.year and month == now.month and (i + 1) == now.day:
            day_button['bg'] = 'white'
            day_button['fg'] = 'green'
        else:
            day_button['bg'] = 'grey'

    for n in range(week_day):
        days[week_day - n - 1].config(text=back_month_days - n, fg='gray', bg='#f3f3f3')
    for n in range(6 * 7 - month_days - week_day):
        days[week_day + month_days + n].config(text=n + 1, fg='gray', bg='#f3f3f3')

def prew():
    global month, year
    month -= 1
    if month == 0:
        month = 12
        year -= 1
    fill()

def next():
    global month, year
    month += 1
    if month == 13:
        month = 1
        year += 1
    fill()

def is_holiday(month, day):
    return (month, day) in holidays

months = ["yanvar", "fevral", "mart", "aprel", "may", "iyun",
          "iyul", "avgust", "sentyabr", "oktyabr", "noyabr", "dekabr"]

now = datetime.now()
days = []
day = now.day
month = now.month
year = now.year

app = Tk()
app.withdraw()

if has_visited_today():
    app.deiconify()
else:
    show_congratulations()
    save_last_visit()

back_button = Button(app, text="<", command=prew)
back_button.grid(row=0, column=0, sticky=NSEW)

next_button = Button(app, text=">", command=next)
next_button.grid(row=0, column=6, sticky=NSEW)


info_label = Label(app, text='0', font='Arial 16 bold', fg='blue')
info_label.grid(row=0, column=1, columnspan=5, sticky=NSEW)

for i in range(7):
    Label(app, text=calendar.day_abbr[i], font='Arial 10 bold', fg='darkblue').grid(row=1, column=i, sticky=NSEW)

for i in range(6 * 7):
    label = Label(app, text='', width=4, height=2, font='Arial 16 bold', bg='grey')
    label.grid(row=(i // 7) + 2, column=i % 7, sticky=NSEW)
    days.append(label)

fill()
app.mainloop()
for i in range(6 * 7):
    label = Label(app, text='', width=4, height=2, font='Arial 16 bold', bg='grey')
    label.grid(row=(i // 7) + 2, column=i % 7, sticky=NSEW)
    days.append(label)

fill()
app.mainloop()