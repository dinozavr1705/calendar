import asyncio
import json
import logging
import pytz
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class HolidayNotifierBot:
    def __init__(self):
        self.bot_token = "7380715390:AAHZuseuGWA9pxE6QayeBxFoM51IXdAh02s"
        self.timezone = pytz.timezone('Asia/Novokuznetsk')
        self.notification_settings = self._load_notification_settings()
        self.holidays = self._load_holidays()
        self.chat_id = None
        self.last_notification_date = None
        self.job = None

    def _load_notification_settings(self) -> Dict:
        settings_path = Path("notification_settings.json")
        try:
            with settings_path.open('r') as f:
                settings = json.load(f)
                if not all(key in settings for key in ["enabled", "hour", "minute"]):
                    raise ValueError("Неполные настройки уведомлений")
                return settings
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
            return {"enabled": True, "hour": 9, "minute": 15}

    def _save_notification_settings(self) -> None:
        with open("notification_settings.json", 'w') as f:
            json.dump(self.notification_settings, f, indent=4)

    def _load_holidays(self) -> Dict[Tuple[int, int], List[Dict]]:
        try:
            with open("holidays.json", "r", encoding="utf-8") as f:
                holidays_json = json.load(f)
                holidays = {}
                for date, events in holidays_json.items():
                    try:
                        month, day = map(int, date.split("-"))
                        holidays[(month, day)] = events if isinstance(events, list) else [events]
                    except (ValueError, AttributeError):
                        logger.warning(f"Некорректная дата: {date}")
                return holidays
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Ошибка загрузки праздников: {e}")
            return {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.chat_id = update.effective_chat.id
        await update.message.reply_text(
            "Привет! Я буду присылать уведомления о праздниках.\n"
            f"Текущее время уведомлений: {self.notification_settings['hour']:02d}:{self.notification_settings['minute']:02d}\n"
            "Используй /settime HH:MM для изменения времени.\n"
            "Используй /test для тестового уведомления.\n"
            "Используй /status для проверки настроек."
        )
        logger.info(f"Чат зарегистрирован: {self.chat_id}")
        await self._restart_job(context.application)

    async def settime(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            time_str = context.args[0]
            hour, minute = map(int, time_str.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError

            self.notification_settings.update({
                "hour": hour,
                "minute": minute
            })
            self._save_notification_settings()

            await self._restart_job(context.application)
            await update.message.reply_text(f"✅ Время уведомлений изменено на {hour:02d}:{minute:02d}")
            logger.info(f"Время уведомлений изменено на {hour:02d}:{minute:02d}")
        except (IndexError, ValueError):
            await update.message.reply_text("❌ Используйте формат: /settime HH:MM (например, /settime 09:15)")

    async def test_notification(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.chat_id:
            await update.message.reply_text("⚠ Сначала зарегистрируйтесь с помощью /start")
            return

        if message := self._get_holidays_message():
            try:
                await context.bot.send_message(
                    chat_id=self.chat_id,
                    text=f"🔔 Тестовое уведомление:\n{message}"
                )
                await update.message.reply_text("✅ Тестовое уведомление отправлено!")
                logger.info("Тестовое уведомление отправлено")
            except Exception as e:
                await update.message.reply_text("❌ Ошибка отправки тестового уведомления")
                logger.error(f"Ошибка отправки теста: {e}")
        else:
            await update.message.reply_text("ℹ Сегодня нет праздников для уведомления")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        status_msg = (
            f"📅 Текущие настройки:\n"
            f"Чат ID: {self.chat_id or 'не установлен'}\n"
            f"Время уведомлений: {self.notification_settings['hour']:02d}:{self.notification_settings['minute']:02d}\n"
            f"Последнее уведомление: {self.last_notification_date or 'еще не отправлялось'}\n"
            f"Запланированное задание: {'активно' if self.job else 'не активно'}"
        )
        await update.message.reply_text(status_msg)

    def _get_holidays_message(self) -> Optional[str]:
        now = datetime.now(self.timezone)
        today = (now.month, now.day)

        if today in self.holidays:
            events = self.holidays[today]
            return "🎉 Сегодня праздник:\n" + "\n".join(
                event.get('text', str(event)) if isinstance(event, dict) else str(event)
                for event in events
            )
        return None

    async def _send_notification(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.notification_settings["enabled"] or not self.chat_id:
            return

        now = datetime.now(self.timezone).date()
        if now == self.last_notification_date:
            return

        if message := self._get_holidays_message():
            try:
                await context.bot.send_message(
                    chat_id=self.chat_id,
                    text=message
                )
                self.last_notification_date = now
                logger.info(f"Уведомление отправлено в {datetime.now(self.timezone)}")
            except Exception as e:
                logger.error(f"Ошибка отправки: {e}")

    async def _restart_job(self, application) -> None:
        if self.job:
            self.job.schedule_removal()

        self.job = application.job_queue.run_daily(
            self._send_notification,
            time=time(
                hour=self.notification_settings["hour"],
                minute=self.notification_settings["minute"],
                tzinfo=self.timezone
            ),
            days=tuple(range(7)),
            name="daily_holiday_notification"
        )
        logger.info(
            f"Уведомления запланированы на {self.notification_settings['hour']:02d}:{self.notification_settings['minute']:02d}")

    def run(self) -> None:
            application = Application.builder().token(self.bot_token).build()
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("settime", self.settime))
            application.add_handler(CommandHandler("test", self.test_notification))
            application.add_handler(CommandHandler("status", self.status))

            application.job_queue.run_once(
                lambda ctx: asyncio.create_task(self._restart_job(ctx.application)),
                when=0
            )

            logger.info("Бот запущен и готов к работе")
            application.run_polling()

if __name__ == '__main__':
        try:
            bot = HolidayNotifierBot()
            bot.run()
        except Exception as e:
            logger.error(f"Фатальная ошибка: {e}", exc_info=True)
