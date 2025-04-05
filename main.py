import json
import threading
import time
from customtkinter import *
import calendar
from datetime import datetime
from tkinter import *
from tkinter import ttk
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

notification_settings = {
    "enabled": True,
    "hour": 11,
    "minute": 15
}

try:
    with open("notification_settings.json", "r") as f:
        notification_settings.update(json.load(f))
except FileNotFoundError:
    pass

holidays = {}
for date, description in holidays_json.items():
    month, day = map(int, date.split("-"))
    holidays[(month, day)] = description


def save_notification_settings():
    with open("notification_settings.json", "w") as f:
        json.dump(notification_settings, f)


def save_holidays():
    with open("holidays.json", "w", encoding="utf-8") as f:
        json.dump({f"{m}-{d}": e for (m, d), e in holidays.items()}, f, ensure_ascii=False, indent=4)


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

        if len(current_events) > 1:
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
    holiday_window.geometry("500x600")

    events_frame = Frame(holiday_window)
    events_frame.pack(pady=10, fill=X)

    Label(events_frame, text="Текущие события:", font=('Arial', 14)).pack(pady=5)

    canvas = Canvas(events_frame, height=200)
    scrollbar = Scrollbar(events_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    event_labels = []
    event_buttons = []
    event_types = []

    for event in current_events:
        if isinstance(event, dict):
            event_text = event["text"]
            event_type = event.get("type", "once")
        else:
            event_text = event
            event_type = "once"

        event_frame = Frame(scrollable_frame)
        event_frame.pack(padx=20, pady=5, fill=X)

        # Иконка типа события
        type_icon = "★" if event_type == "yearly" else "•"
        Label(event_frame, text=type_icon, font=('Arial', 12), width=2).pack(side=LEFT)

        label = Label(event_frame, text=event_text, font=('Arial', 12), wraplength=300, justify=LEFT)
        label.pack(side=LEFT, fill=X, expand=True)

        def delete_event(event_text=event_text, event_type=event_type):
            if isinstance(event, dict):
                current_events.remove(event)
            else:
                current_events.remove(event_text)

            holidays[(month, day)] = current_events
            save_holidays()

            event_frame.destroy()

        delete_button = Button(event_frame, text="Удалить", command=delete_event)
        delete_button.pack(side=RIGHT)

        event_labels.append(label)
        event_buttons.append(delete_button)
        event_types.append(event_type)

    add_frame = Frame(holiday_window)
    add_frame.pack(pady=20, padx=20, fill=X)

    Label(add_frame, text="Добавить новое событие:", font=('Arial', 14)).pack(pady=5, anchor=W)

    text_entry = Text(add_frame, height=5, width=40, font=('Arial', 12))
    text_entry.pack(fill=X, pady=5)

    settings_frame = Frame(add_frame)
    settings_frame.pack(fill=X, pady=5)

    Label(settings_frame, text="Тип события:", font=('Arial', 12)).pack(side=LEFT)

    event_type_var = StringVar(value="once")
    ttk.Radiobutton(settings_frame, text="Единоразовое", variable=event_type_var, value="once").pack(side=LEFT, padx=5)
    ttk.Radiobutton(settings_frame, text="Ежегодное", variable=event_type_var, value="yearly").pack(side=LEFT, padx=5)

    def add_event():
        event_text = text_entry.get("1.0", END).strip()
        if event_text:
            event_data = {
                "text": event_text,
                "type": event_type_var.get()
            }

            current_events.append(event_data)
            holidays[(month, day)] = current_events
            save_holidays()

            event_frame = Frame(scrollable_frame)
            event_frame.pack(padx=20, pady=5, fill=X)

            type_icon = "★" if event_type_var.get() == "yearly" else "•"
            Label(event_frame, text=type_icon, font=('Arial', 12), width=2).pack(side=LEFT)

            label = Label(event_frame, text=event_text, font=('Arial', 12), wraplength=300, justify=LEFT)
            label.pack(side=LEFT, fill=X, expand=True)

            def delete_event(event_text=event_text, event_type=event_type_var.get()):
                for e in current_events:
                    if isinstance(e, dict) and e["text"] == event_text and e["type"] == event_type:
                        current_events.remove(e)
                        break

                holidays[(month, day)] = current_events
                save_holidays()
                event_frame.destroy()

            delete_button = Button(event_frame, text="Удалить", command=delete_event)
            delete_button.pack(side=RIGHT)

            text_entry.delete("1.0", END)

            canvas.yview_moveto(1.0)

    add_button = Button(add_frame, text="Добавить событие", command=add_event)
    add_button.pack(pady=10)

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


def show_holiday_notification():
    if not notification_settings["enabled"]:
        return

    now = datetime.now()
    current_month = now.month
    current_day = now.day
    if (current_month, current_day) in holidays:
        description = holidays[(current_month, current_day)][0]
        notification.notify(
                title='Праздник сегодня!',
                message=description,
                app_name='Календарь',
                timeout=10
            )


def check_time_for_notification():
    last_notified_day = None
    while True:
        now = datetime.now()
        if (now.hour == notification_settings["hour"] and
                now.minute == notification_settings["minute"]):
            if last_notified_day != now.date():
                show_holiday_notification()
                last_notified_day = now.date()
            time.sleep(60)
        else:
            time.sleep(60 - now.second)


def open_settings():
    settings_window = Toplevel(app)
    settings_window.title("Настройки уведомлений")
    settings_window.geometry("300x200")

    enabled_var = BooleanVar(value=notification_settings["enabled"])
    enabled_check = Checkbutton(settings_window, text="Включить уведомления",
                                variable=enabled_var, font=('Arial', 12))
    enabled_check.pack(pady=10)

    time_frame = Frame(settings_window)
    time_frame.pack(pady=10)

    Label(time_frame, text="Время уведомления:", font=('Arial', 12)).pack()

    hour_var = StringVar(value=str(notification_settings["hour"]))
    minute_var = StringVar(value=str(notification_settings["minute"]))

    time_entry_frame = Frame(time_frame)
    time_entry_frame.pack()

    Entry(time_entry_frame, textvariable=hour_var, width=2, font=('Arial', 12)).pack(side=LEFT)
    Label(time_entry_frame, text=":", font=('Arial', 12)).pack(side=LEFT)
    Entry(time_entry_frame, textvariable=minute_var, width=2, font=('Arial', 12)).pack(side=LEFT)

    def save_settings():
        try:
            notification_settings["enabled"] = enabled_var.get()
            notification_settings["hour"] = int(hour_var.get())
            notification_settings["minute"] = int(minute_var.get())
            save_notification_settings()
            settings_window.destroy()
        except ValueError:
            Label(settings_window, text="Введите корректное время!", fg="red").pack()

    Button(settings_window, text="Сохранить", command=save_settings).pack(pady=10)


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

settings_button = Button(app, text="⚙ Настройки", command=open_settings)
settings_button.grid(row=8, column=0, columnspan=7, sticky=NSEW, pady=10)

fill()

notification_thread = threading.Thread(target=check_time_for_notification, daemon=True)
notification_thread.start()

app.mainloop()
