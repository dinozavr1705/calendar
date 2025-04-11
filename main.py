import json
import threading
import time
import calendar
from datetime import datetime
from tkinter import *
from tkinter import ttk
from plyer import notification

months = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
}

try:
    with open("holidays.json", "r", encoding="utf-8") as f:
        holidays_json = json.load(f)
    holidays = {}
    for date, events in holidays_json.items():
        month, day = map(int, date.split("-"))
        holidays[(month, day)] = events if isinstance(events, list) else [events]
except FileNotFoundError:
    holidays = {}

notification_settings = {
    "enabled": True,
    "hour": 9,
    "minute": 0
}

try:
    with open("notification_settings.json", "r") as f:
        notification_settings.update(json.load(f))
except FileNotFoundError:
    pass


def save_notification_settings():
    with open("notification_settings.json", "w") as f:
        json.dump(notification_settings, f)


def save_holidays():
    with open("holidays.json", "w", encoding="utf-8") as f:
        json.dump({f"{m}-{d}": e for (m, d), e in holidays.items()}, f, ensure_ascii=False, indent=4)


def has_visited_today():
    try:
        today = datetime.now().date()
        with open("last_visit.txt", "r") as f:
            last_visit = f.read().strip()
            return last_visit == str(today)
    except FileNotFoundError:
        return False


def save_last_visit():
    today = datetime.now().date()
    with open("last_visit.txt", "w") as f:
        f.write(str(today))


def show_congratulations():
    current_events = holidays.get((month, day), [])
    congratulation_window = Toplevel(app)
    congratulation_window.title("Поздравление")

    if (month, day) in holidays:
        first_event = holidays[(month, day)][0]
        message = f"Поздравляем с праздником: {first_event['text'] if isinstance(first_event, dict) else first_event}!"
        Label(congratulation_window, text=message, font=('Arial', 14)).pack(padx=20, pady=20)

        if len(current_events) > 1:
            events = [e['text'] if isinstance(e, dict) else e for e in current_events[1:]]
            Label(congratulation_window, text="У вас есть события сегодня:\n" + "\n".join(events),
                  font=('Arial', 12)).pack(padx=20, pady=10)

        Button(congratulation_window, text="Перейти в календарь",
               command=lambda: [congratulation_window.destroy(), app.deiconify()]).pack(pady=10)
    else:
        Label(congratulation_window, text="Сегодня нет праздников.", font=('Arial', 14)).pack(padx=20, pady=20)
        Button(congratulation_window, text="Перейти в календарь",
               command=lambda: [congratulation_window.destroy(), app.deiconify()]).pack(pady=10)


def show_holiday(day):
    current_date = datetime(year, month, day).date()
    today = datetime.now().date()
    is_past_date = current_date < today

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
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    if is_past_date:
        current_events = [e for e in current_events if not (isinstance(e, dict) and e.get("type") == "once")]
        holidays[(month, day)] = current_events
        save_holidays()

    for event in current_events:
        event_frame = Frame(scrollable_frame)
        event_frame.pack(padx=20, pady=5, fill=X)
        event_text = event['text']['text'] if isinstance(event, dict) else event
        event_type = event.get("type", "yearly") if isinstance(event, dict) else "yearly"

        Label(event_frame, text="★" if event_type == "yearly" else "•", font=('Arial', 12), width=2).pack(side=LEFT)
        Label(event_frame, text=event_text, font=('Arial', 12), wraplength=300, justify=LEFT).pack(side=LEFT, fill=X,
                                                                                                   expand=True)

        Button(event_frame, text="Удалить",
               command=lambda e=event: [current_events.remove(e), holidays[(month, day)].remove(e),
                                        save_holidays(), event_frame.destroy()]).pack(side=RIGHT)

    if not is_past_date:
        add_frame = Frame(holiday_window)
        add_frame.pack(pady=20, padx=20, fill=X)
        Label(add_frame, text="Добавить новое событие:", font=('Arial', 14)).pack(pady=5, anchor=W)

        text_entry = Text(add_frame, height=5, width=40, font=('Arial', 12))
        text_entry.pack(fill=X, pady=5)

        settings_frame = Frame(add_frame)
        settings_frame.pack(fill=X, pady=5)
        Label(settings_frame, text="Тип события:", font=('Arial', 12)).pack(side=LEFT)

        event_type_var = StringVar(value="once")
        ttk.Radiobutton(settings_frame, text="Единоразовое", variable=event_type_var, value="once").pack(side=LEFT,
                                                                                                         padx=5)
        ttk.Radiobutton(settings_frame, text="Ежегодное", variable=event_type_var, value="yearly").pack(side=LEFT,
                                                                                                        padx=5)

        def add_event():
            text = text_entry.get("1.0", END).strip()
            if text:
                event = {"text": text, "type": event_type_var.get()}
                current_events.append(event)
                holidays[(month, day)] = current_events
                save_holidays()

                event_frame = Frame(scrollable_frame)
                event_frame.pack(padx=20, pady=5, fill=X)
                Label(event_frame, text="★" if event_type_var.get() == "yearly" else "•", font=('Arial', 12),
                      width=2).pack(side=LEFT)
                Label(event_frame, text=text, font=('Arial', 12), wraplength=300, justify=LEFT).pack(side=LEFT, fill=X,
                                                                                                     expand=True)
                Button(event_frame, text="Удалить", command=lambda e=event: [current_events.remove(e),
                                                                             holidays[(month, day)].remove(e),
                                                                             save_holidays(),
                                                                             event_frame.destroy()]).pack(side=RIGHT)

                text_entry.delete("1.0", END)
                canvas.yview_moveto(1.0)

        Button(add_frame, text="Добавить событие", command=add_event).pack(pady=10)
    else:
        Label(holiday_window, text="Нельзя добавлять события к прошедшим датам", font=('Arial', 12), fg='gray').pack(
            pady=20)

    Button(holiday_window, text="Закрыть", command=holiday_window.destroy).pack(pady=5)


def fill():
    today = datetime.now().date()
    for (m, d), events in list(holidays.items()):
        if datetime(year, m, d).date() < today:
            updated = [e for e in events if not (isinstance(e, dict) and e.get("type") == "once")]
            holidays[(m, d)] = updated if updated else None
    save_holidays()

    info_label['text'] = f"{calendar.month_name[month]}, {year}"
    month_days = calendar.monthrange(year, month)[1]
    week_day = calendar.monthrange(year, month)[0]

    for i in range(month_days):
        pos = i + week_day
        btn = Button(app, text=str(i + 1), width=4, height=2, font='Arial 16 bold', bg='grey',
                     command=lambda d=i + 1: show_holiday(d))
        btn.grid(row=(pos // 7) + 2, column=pos % 7, sticky=NSEW)
        btn['fg'] = 'red' if (week_day + i) % 7 in (5, 6) else 'black'
        if year == now.year and month == now.month and (i + 1) == now.day:
            btn['bg'], btn['fg'] = 'white', 'green'

    for n in range(week_day):
        days[week_day - n - 1].config(
            text=calendar.monthrange(year - 1 if month == 1 else year, 12 if month == 1 else month - 1)[1] - n,
            fg='gray', bg='#f3f3f3')
    for n in range(6 * 7 - month_days - week_day):
        days[week_day + month_days + n].config(text=n + 1, fg='gray', bg='#f3f3f3')


def prew():
    global month, year
    month = 12 if (month := month - 1) == 0 else month
    year = year - 1 if month == 12 else year
    fill()


def next():
    global month, year
    month = 1 if (month := month + 1) == 13 else month
    year = year + 1 if month == 1 else year
    fill()


def show_holiday_notification():
    if notification_settings["enabled"] and (now := datetime.now()):
        if (now.month, now.day) in holidays:
            desc = holidays[(now.month, now.day)][0]
            notification.notify(title='Праздник сегодня!', message=desc['text'] if isinstance(desc, dict) else desc,
                                    app_name='Календарь', timeout=10)


def check_time_for_notification():
    last_day = None
    while True:
        now = datetime.now()
        if now.hour == notification_settings["hour"] and now.minute == notification_settings["minute"]:
            if last_day != now.date():
                show_holiday_notification()
                last_day = now.date()
            time.sleep(60)
        else:
            time.sleep(60 - now.second)


def open_settings():
    win = Toplevel(app)
    win.title("Настройки уведомлений")
    win.geometry("300x200")

    enabled = BooleanVar(value=notification_settings["enabled"])
    Checkbutton(win, text="Включить уведомления", variable=enabled, font=('Arial', 12)).pack(pady=10)

    Frame(win).pack(pady=10)
    Label(win, text="Время уведомления:", font=('Arial', 12)).pack()

    f = Frame(win)
    f.pack()
    h = StringVar(value=str(notification_settings["hour"]))
    m = StringVar(value=str(notification_settings["minute"]))
    Entry(f, textvariable=h, width=2, font=('Arial', 12)).pack(side=LEFT)
    Label(f, text=":", font=('Arial', 12)).pack(side=LEFT)
    Entry(f, textvariable=m, width=2, font=('Arial', 12)).pack(side=LEFT)

    def save():
        try:
            notification_settings.update({"enabled": enabled.get(), "hour": int(h.get()), "minute": int(m.get())})
            save_notification_settings()
            win.destroy()
        except ValueError:
            Label(win, text="Введите корректное время!", fg="red").pack()

    Button(win, text="Сохранить", command=save).pack(pady=10)


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

Button(app, text="<", command=prew).grid(row=0, column=0, sticky=NSEW)
Button(app, text=">", command=next).grid(row=0, column=6, sticky=NSEW)

info_label = Label(app, text='0', font='Arial 16 bold', fg='blue')
info_label.grid(row=0, column=1, columnspan=5, sticky=NSEW)

for i in range(7):
    Label(app, text=calendar.day_abbr[i], font='Arial 10 bold', fg='darkblue').grid(row=1, column=i, sticky=NSEW)

for i in range(6 * 7):
    label = Label(app, text='', width=4, height=2, font='Arial 16 bold', bg='grey')
    label.grid(row=(i // 7) + 2, column=i % 7, sticky=NSEW)
    days.append(label)

Button(app, text="⚙ Настройки", command=open_settings).grid(row=8, column=0, columnspan=7, sticky=NSEW, pady=10)

fill()

threading.Thread(target=check_time_for_notification, daemon=True).start()

app.mainloop()
