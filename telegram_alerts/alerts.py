import json
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, Set
import aiofiles
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from PIL import Image
import io
import hashlib

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8401414063:AAESVUpfFJEu_5dOxkQY-0c-MU45GTUSEzY"  # Замените на настоящий

JSON_FILE = "/Users/reznicenkodaniivsevolodovic/GolandProjects/ClarityWeb/storage/files/applications.json"
STATE_FILE = "d/Users/reznicenkodaniivsevolodovic/GolandProjects/ClarityWeb/storage/files/bot_state.json"
SUBSCRIBERS_FILE = "/Users/reznicenkodaniivsevolodovic/GolandProjects/ClarityWeb/storage/files/subscribers.json"
SENT_POSTS_FILE = "/Users/reznicenkodaniivsevolodovic/GolandProjects/ClarityWeb/storage/files/sent_posts.json"
CHECK_INTERVAL = 3


class FormMonitorBot:
    def __init__(self):
        self.application = None
        self.bot = None
        self.subscribed_chats = set()
        self.sent_post_hashes = set()
        self.sent_post_ids = set()  # Новый: отслеживаем по ID
        self.last_form_id = None
        self.is_monitoring = True

        os.makedirs("data", exist_ok=True)

        print(f"📁 Проверяю файл JSON: {JSON_FILE}")
        if not os.path.exists(JSON_FILE):
            print(f"⚠️  Файл {JSON_FILE} не существует. Создаю пустой...")
            with open(JSON_FILE, 'w') as f:
                json.dump([], f)
            print(f"✅ Файл создан")

    def generate_post_hash(self, form_data: Dict) -> str:
        """Создает уникальный хеш для поста"""
        # Используем ВСЕ важные поля для хеша
        data_parts = [
            str(form_data.get('id', '')),
            str(form_data.get('name', '')),
            str(form_data.get('email', '')),
            str(form_data.get('message', '')),
            str(form_data.get('timestamp', ''))
        ]
        data = '-'.join(data_parts)
        print(f"🔑 Генерация хеша для формы {form_data.get('id')}: {data[:50]}...")
        return hashlib.md5(data.encode()).hexdigest()

    def is_post_sent(self, form_data: Dict) -> bool:
        """Проверяет, был ли пост уже отправлен"""
        form_id = form_data.get('id')

        # Проверяем по ID (самый надежный способ)
        if form_id and form_id in self.sent_post_ids:
            print(f"📭 Форма {form_id} уже была отправлена (по ID)")
            return True

        # Дополнительная проверка по хешу
        post_hash = self.generate_post_hash(form_data)
        if post_hash in self.sent_post_hashes:
            print(f"📭 Форма {form_id} уже была отправлена (по хешу)")
            return True

        print(f"🆕 Форма {form_id} НОВАЯ!")
        return False

    def mark_post_as_sent(self, form_data: Dict):
        """Помечает пост как отправленный"""
        form_id = form_data.get('id')

        if form_id:
            self.sent_post_ids.add(form_id)
            print(f"✅ Добавил ID {form_id} в sent_post_ids")

        post_hash = self.generate_post_hash(form_data)
        self.sent_post_hashes.add(post_hash)
        print(f"✅ Добавил хеш {post_hash[:8]}... в sent_post_hashes")

        # Сохраняем в файл сразу
        self.save_data()

    def load_data(self):
        """Загружает данные из файлов"""
        try:
            # Подписчики
            if os.path.exists(SUBSCRIBERS_FILE):
                with open(SUBSCRIBERS_FILE, 'r') as f:
                    data = f.read()
                    if data:
                        subscribers = json.loads(data)
                        self.subscribed_chats = set(subscribers.get("chats", []))
                        print(f"✅ Загружено {len(self.subscribed_chats)} подписчиков")

            # Отправленные посты (хеши)
            if os.path.exists(SENT_POSTS_FILE):
                with open(SENT_POSTS_FILE, 'r') as f:
                    data = f.read()
                    if data:
                        sent_data = json.loads(data)
                        self.sent_post_hashes = set(sent_data.get("hashes", []))
                        self.sent_post_ids = set(sent_data.get("ids", []))  # Загружаем IDs
                        print(f"✅ Загружено {len(self.sent_post_hashes)} хешей и {len(self.sent_post_ids)} ID")

            # Состояние
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    data = f.read()
                    if data:
                        state = json.loads(data)
                        self.last_form_id = state.get("last_form_id")
                        if self.last_form_id:
                            print(f"✅ Последний ID: {self.last_form_id}")

        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            import traceback
            traceback.print_exc()

    def save_data(self):
        """Сохраняет данные в файлы"""
        try:
            # Подписчики
            subscribers_data = {"chats": list(self.subscribed_chats)}
            with open(SUBSCRIBERS_FILE, 'w') as f:
                json.dump(subscribers_data, f, indent=2)

            # Отправленные посты (хеши И IDs)
            sent_data = {
                "hashes": list(self.sent_post_hashes),
                "ids": list(self.sent_post_ids)  # Сохраняем IDs
            }
            with open(SENT_POSTS_FILE, 'w') as f:
                json.dump(sent_data, f, indent=2)

            # Состояние
            state_data = {"last_form_id": self.last_form_id}
            with open(STATE_FILE, 'w') as f:
                json.dump(state_data, f, indent=2)

            print(
                f"💾 Сохранено: {len(self.subscribed_chats)} подписчиков, {len(self.sent_post_hashes)} хешей, {len(self.sent_post_ids)} ID")

        except Exception as e:
            print(f"❌ Ошибка сохранения данных: {e}")

    def create_color_image(self, hex_color: str) -> io.BytesIO:
        """Создает изображение с заданным цветом"""
        hex_color = hex_color.lstrip('#')

        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        elif len(hex_color) == 3:
            r = int(hex_color[0] * 2, 16)
            g = int(hex_color[1] * 2, 16)
            b = int(hex_color[2] * 2, 16)
        else:
            r, g, b = 128, 128, 128

        img = Image.new('RGB', (200, 100), (r, g, b))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return img_byte_arr

    def format_form_message(self, form_data: Dict) -> str:
        """Форматирует сообщение о форме"""
        timestamp = form_data.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%d.%m.%Y %H:%M:%S')
            except:
                time_str = timestamp
        else:
            time_str = 'Не указано'

        topics = form_data.get('topics', [])
        topics_text = ', '.join(topics) if topics else 'Не выбраны'

        links = form_data.get('links', [])
        links_text = '\n'.join([f'• {link}' for link in links[:3]]) if links else '• Нет ссылок'
        if len(links) > 3:
            links_text += f'\n• ... и еще {len(links) - 3} ссылок'

        message = f"""📋 *Новая заявка!*

👤 *Имя:* {form_data.get('name', 'Не указано')}
🏢 *Компания:* {form_data.get('company', 'Не указано')}
📧 *Email:* `{form_data.get('email', 'Не указано')}`
📞 *Телефон:* {form_data.get('phone', form_data.get('Phone', 'Не указано'))}

📝 *Сообщение:*
{form_data.get('message', 'Не указано')}

🎯 *Темы:* {topics_text}
🎨 *Тематика:* {form_data.get('theme', 'Не выбрана')}

🕒 *Время:* {time_str}
🆔 *ID:* `{form_data.get('id', 'Нет')}`

🔗 *Ссылки:*
{links_text}"""

        return message

    async def check_for_new_forms(self):
        """Проверяет есть ли новые формы в файле"""
        try:
            if not os.path.exists(JSON_FILE):
                print(f"❌ Файл {JSON_FILE} не найден!")
                return

            # Читаем файл
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if not content:
                print("📭 Файл форм пустой")
                return

            try:
                forms = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка парсинга JSON: {e}")
                print(f"Содержимое файла: {content[:100]}...")
                return

            if not isinstance(forms, list):
                print(f"❌ JSON не является массивом. Тип: {type(forms)}")
                return

            print(f"🔍 Проверяю {len(forms)} форм в файле...")
            print(f"📊 В истории: {len(self.sent_post_ids)} ID, {len(self.sent_post_hashes)} хешей")

            # Ищем новые формы
            new_forms = []
            for form in forms:
                form_id = form.get('id')
                if not form_id:
                    print(f"⚠️  Форма без ID: {form.get('name', 'Без имени')}")
                    continue

                if not self.is_post_sent(form):
                    print(f"🎯 Найдена НОВАЯ форма: ID {form_id}")
                    new_forms.append(form)
                else:
                    print(f"📭 Форма {form_id} уже отправлена")

            if new_forms:
                print(f"✅ Найдено {len(new_forms)} новых форм!")
                for i, form in enumerate(new_forms, 1):
                    form_id = form.get('id')
                    print(f"  {i}. Отправляю форму {form_id}...")

                    # Проверяем есть ли подписчики
                    if not self.subscribed_chats:
                        print("⚠️  Нет подписчиков! Пропускаю отправку...")
                        self.mark_post_as_sent(form)  # Все равно помечаем как отправленную
                        continue

                    success = await self.send_form_to_subscribers(form)
                    if success:
                        self.mark_post_as_sent(form)
                        self.last_form_id = form_id
                    else:
                        print(f"❌ Не удалось отправить форму {form_id}")

                # Сохраняем данные
                self.save_data()
                print("💾 Данные сохранены")
            else:
                print("📭 Новых форм не найдено")

            print("-" * 50)

        except Exception as e:
            print(f"❌ Ошибка при проверке форм: {e}")
            import traceback
            traceback.print_exc()

    async def send_form_to_subscribers(self, form_data: Dict) -> bool:
        """Отправляет форму всем подписчикам"""
        if not self.subscribed_chats:
            print("⚠️ Нет подписчиков для отправки")
            return False

        form_id = form_data.get('id', 'Без ID')
        print(f"🚀 Отправляю форму {form_id} всем {len(self.subscribed_chats)} подписчикам...")

        # Форматируем сообщение
        message = self.format_form_message(form_data)

        # Отправляем текстовое сообщение
        success_count = 0
        failed_chats = []

        for chat_id in self.subscribed_chats:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                success_count += 1
            except Exception as e:
                error_msg = str(e).lower()
                if "bot was blocked" in error_msg or "chat not found" in error_msg:
                    print(f"🗑️ Удаляю заблокировавшего подписчика: {chat_id}")
                    self.subscribed_chats.discard(chat_id)
                    failed_chats.append(chat_id)
                else:
                    print(f"❌ Ошибка отправки в чат {chat_id}: {e}")

        # Удаляем заблокированных подписчиков
        for chat_id in failed_chats:
            self.subscribed_chats.discard(chat_id)

        # Отправляем цвета
        colors = form_data.get('colors', [])
        colors_sent = 0

        if colors and success_count > 0:  # Только если есть кому отправлять
            for i, color in enumerate(colors[:3]):  # Максимум 3 цвета
                try:
                    color_image = self.create_color_image(color)

                    color_names = ['Основной', 'Вторичный', 'Акцентный']
                    color_name = color_names[i] if i < len(color_names) else f'Цвет {i + 1}'

                    for chat_id in self.subscribed_chats:
                        try:
                            await self.bot.send_photo(
                                chat_id=chat_id,
                                photo=color_image,
                                caption=f"🎨 *{color_name}:* `{color}`",
                                parse_mode='Markdown'
                            )
                            # Возвращаем указатель в начало
                            color_image.seek(0)
                        except Exception as e:
                            print(f"❌ Ошибка отправки цвета в чат {chat_id}: {e}")

                    colors_sent += 1

                except Exception as e:
                    print(f"❌ Ошибка создания изображения цвета {color}: {e}")

        print(f"✅ Форма {form_id} отправлена {success_count} подписчикам, отправлено {colors_sent} цветов")
        return success_count > 0

    async def monitoring_task(self):
        """Задача мониторинга файла"""
        print("🔄 Запуск мониторинга файла...")

        # Первая проверка сразу
        print("🔍 Первоначальная проверка...")
        await self.check_for_new_forms()

        check_count = 0
        while self.is_monitoring:
            try:
                await asyncio.sleep(CHECK_INTERVAL)
                check_count += 1
                print(f"\n🔄 Проверка #{check_count}...")
                await self.check_for_new_forms()
            except asyncio.CancelledError:
                print("🛑 Мониторинг остановлен")
                break
            except Exception as e:
                print(f"❌ Ошибка в задаче мониторинга: {e}")

    async def clear_history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Очищает историю отправленных постов"""
        self.sent_post_hashes.clear()
        self.sent_post_ids.clear()
        self.save_data()

        await update.message.reply_text(
            "🧹 *История очищена!*\n\n"
            "Теперь все формы из файла будут считаться новыми.",
            parse_mode='Markdown'
        )
        print("✅ История очищена")

    async def debug_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для отладки"""
        # Читаем текущий файл форм
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                forms = json.loads(content) if content else []

            debug_info = f"""🐛 *Отладочная информация:*

📁 *Файлы:*
• {JSON_FILE}: {len(forms)} форм
• {SUBSCRIBERS_FILE}: {len(self.subscribed_chats)} подписчиков
• {SENT_POSTS_FILE}: {len(self.sent_post_ids)} ID, {len(self.sent_post_hashes)} хешей

📊 *Состояние:*
• Подписчиков: {len(self.subscribed_chats)}
• Отслеживаемых ID: {len(self.sent_post_ids)}
• Последний ID: `{self.last_form_id or 'Нет'}`

📝 *Формы в файле ({len(forms)}):*"""

            for i, form in enumerate(forms[-5:], 1):  # Последние 5 форм
                form_id = form.get('id', 'Без ID')
                name = form.get('name', 'Без имени')
                is_sent = form_id in self.sent_post_ids
                debug_info += f"\n{i}. `{form_id}` - {name} - {'✅ Отправлена' if is_sent else '❌ Новая'}"

            if len(forms) > 5:
                debug_info += f"\n... и еще {len(forms) - 5} форм"

            await update.message.reply_text(debug_info, parse_mode='Markdown')

        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}", parse_mode='Markdown')

    async def resend_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправляет последнюю форму заново"""
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                forms = json.loads(content) if content else []

            if not forms:
                await update.message.reply_text("📭 Нет форм в файле", parse_mode='Markdown')
                return

            last_form = forms[-1]
            form_id = last_form.get('id', 'Без ID')

            # Удаляем из истории, чтобы отправить заново
            if form_id in self.sent_post_ids:
                self.sent_post_ids.remove(form_id)
                post_hash = self.generate_post_hash(last_form)
                if post_hash in self.sent_post_hashes:
                    self.sent_post_hashes.remove(post_hash)
                self.save_data()

            await update.message.reply_text(
                f"🔄 *Отправляю форму {form_id} заново...*",
                parse_mode='Markdown'
            )

            success = await self.send_form_to_subscribers(last_form)
            if success:
                self.mark_post_as_sent(last_form)
                await update.message.reply_text(
                    f"✅ *Форма {form_id} отправлена заново!*",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ *Не удалось отправить форму {form_id}*",
                    parse_mode='Markdown'
                )

        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}", parse_mode='Markdown')

    # ========== КОМАНДЫ БОТА ==========
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик /start"""
        chat_id = update.effective_chat.id

        if chat_id not in self.subscribed_chats:
            self.subscribed_chats.add(chat_id)
            self.save_data()

            await update.message.reply_text(
                "✅ *Вы подписались на уведомления!*\n\n"
                "Теперь вы будете получать сообщения о всех новых заявках.\n\n"
                "*Доступные команды:*\n"
                "• /status - ваш статус\n"
                "• /unsubscribe - отписаться\n"
                "• /test - тестовое сообщение\n"
                "• /check - проверить формы сейчас\n"
                "• /debug - отладочная информация\n"
                "• /clear - очистить историю\n"
                "• /resend - отправить последнюю форму заново\n"
                "• /help - справка",
                parse_mode='Markdown'
            )
            print(f"🎉 Новый подписчик: {chat_id}")
        else:
            await update.message.reply_text(
                "👋 *Вы уже подписаны!*\n\n"
                "Используйте /status для проверки статуса.",
                parse_mode='Markdown'
            )

    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик /unsubscribe"""
        chat_id = update.effective_chat.id

        if chat_id in self.subscribed_chats:
            self.subscribed_chats.remove(chat_id)
            self.save_data()

            await update.message.reply_text(
                "❌ *Вы отписались от уведомлений.*\n\n"
                "Чтобы снова подписаться, используйте /start",
                parse_mode='Markdown'
            )
            print(f"👋 Отписался: {chat_id}")
        else:
            await update.message.reply_text(
                "ℹ️ *Вы не были подписаны.*\n\n"
                "Используйте /start для подписки.",
                parse_mode='Markdown'
            )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик /status"""
        chat_id = update.effective_chat.id
        is_subscribed = chat_id in self.subscribed_chats

        # Проверяем существование файла
        file_exists = os.path.exists(JSON_FILE)
        file_size = os.path.getsize(JSON_FILE) if file_exists else 0

        try:
            form_count = 0
            if file_exists and file_size > 0:
                with open(JSON_FILE, 'r') as f:
                    content = f.read()
                    if content:
                        forms = json.loads(content)
                        form_count = len(forms) if isinstance(forms, list) else 0
        except:
            form_count = 0

        message = f"""📊 *Статус:*

{'✅ *ПОДПИСАН*' if is_subscribed else '❌ *НЕ ПОДПИСАН*'}

👥 *Статистика:*
• Подписчиков: {len(self.subscribed_chats)}
• Форм в файле: {form_count}
• Отслеживаемых ID: {len(self.sent_post_ids)}
• Последняя форма: `{self.last_form_id or 'Нет'}`

🔄 *Настройки:*
• Проверка каждые: {CHECK_INTERVAL} сек.
• Файл: {'✅' if file_exists else '❌'} ({file_size} байт)

{'Используйте /unsubscribe для отписки' if is_subscribed else 'Используйте /start для подписки'}"""

        await update.message.reply_text(message, parse_mode='Markdown')

    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик /test"""
        chat_id = update.effective_chat.id

        test_form = {
            'id': f'test_{int(time.time())}',
            'name': 'Тестовый пользователь',
            'company': 'Тестовая компания',
            'email': 'test@example.com',
            'phone': '+79999999999',
            'message': 'Это тестовое сообщение для проверки бота',
            'topics': ['development'],
            'theme': 'corporate',
            'colors': ['#FF5733', '#33FF57', '#3357FF'],
            'links': ['https://example.com'],
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Отправляем тест только отправившему
            message = self.format_form_message(test_form)
            await update.message.reply_text(message, parse_mode='Markdown')

            # Отправляем цвета
            for i, color in enumerate(test_form['colors']):
                color_image = self.create_color_image(color)
                color_names = ['Основной', 'Вторичный', 'Акцентный']
                color_name = color_names[i] if i < len(color_names) else f'Цвет {i + 1}'

                await update.message.reply_photo(
                    photo=color_image,
                    caption=f"🎨 *{color_name}:* `{color}`",
                    parse_mode='Markdown'
                )

            await update.message.reply_text(
                "✅ *Тестовое сообщение отправлено!*\n\n"
                "Если вы подписаны (/status), вы получите такое же уведомление "
                "при появлении новой заявки.",
                parse_mode='Markdown'
            )

        except Exception as e:
            print(f"❌ Ошибка теста: {e}")
            await update.message.reply_text(
                f"❌ *Ошибка:* `{str(e)}`",
                parse_mode='Markdown'
            )

    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик /check - принудительная проверка"""
        await update.message.reply_text(
            "🔍 *Проверяю формы...*",
            parse_mode='Markdown'
        )

        await self.check_for_new_forms()

        await update.message.reply_text(
            "✅ *Проверка завершена!*\n\n"
            "Используйте /status для проверки статуса.",
            parse_mode='Markdown'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик /help"""
        await update.message.reply_text(
            "🤖 *Команды бота:*\n\n"
            "• /start - подписаться на уведомления\n"
            "• /status - ваш статус и статистика\n"
            "• /unsubscribe - отписаться\n"
            "• /test - тестовое сообщение\n"
            "• /check - проверить формы сейчас\n"
            "• /debug - отладочная информация\n"
            "• /clear - очистить историю отправленных\n"
            "• /resend - отправить последнюю форму заново\n"
            "• /help - эта справка\n\n"
            "*Как это работает:*\n"
            "1. Подпишитесь командой /start\n"
            "2. Бот автоматически проверяет файл data/forms.json\n"
            "3. При появлении новой формы - получаете уведомление",
            parse_mode='Markdown'
        )

    async def run(self):
        """Запускает бота"""
        print("=" * 60)
        print("🤖 ЗАПУСК ТЕЛЕГРАМ БОТА")
        print("=" * 60)

        # Проверяем токен
        if BOT_TOKEN == "ВАШ_ТОКЕН_БОТА":
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Укажите токен бота!")
            print("   Получите токен у @BotFather в Telegram")
            print("   Замените 'ВАШ_ТОКЕН_БОТА' на настоящий токен")
            return

        # Загружаем данные
        print("📂 Загружаю данные...")
        self.load_data()

        print("🤖 Создаю приложение Telegram...")

        try:
            # Создаем приложение
            self.application = Application.builder().token(BOT_TOKEN).build()
            self.bot = self.application.bot

            # Добавляем обработчики команд
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CommandHandler("test", self.test_command))
            self.application.add_handler(CommandHandler("check", self.check_command))
            self.application.add_handler(CommandHandler("debug", self.debug_command))
            self.application.add_handler(CommandHandler("clear", self.clear_history_command))
            self.application.add_handler(CommandHandler("resend", self.resend_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("stats", self.status_command))

            # Инициализируем
            await self.application.initialize()

            # Запускаем мониторинг в фоне
            monitoring_task = asyncio.create_task(self.monitoring_task())

            print("✅ Бот успешно инициализирован!")
            print(f"👥 Подписчиков: {len(self.subscribed_chats)}")
            print(f"📝 В истории: {len(self.sent_post_ids)} ID, {len(self.sent_post_hashes)} хешей")
            print(f"🔄 Проверка каждые {CHECK_INTERVAL} секунд")
            print("\n📋 Команды:")
            print("   /start - подписаться")
            print("   /status - статус")
            print("   /test - тест")
            print("   /check - проверка сейчас")
            print("   /debug - отладка")
            print("   /clear - очистить историю")
            print("   /resend - отправить последнюю форму заново")
            print("\n⚠️  Нажмите Ctrl+C для остановки")
            print("=" * 60)

            # Запускаем polling
            await self.application.start()

            print("📡 Запускаю polling...")
            await self.application.updater.start_polling()

            # Бесконечный цикл
            await asyncio.Event().wait()

        except KeyboardInterrupt:
            print("\n🛑 Получен сигнал остановки...")
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Останавливаем
            self.is_monitoring = False
            if 'monitoring_task' in locals():
                monitoring_task.cancel()

            print("💾 Сохраняю данные...")
            self.save_data()

            if self.application:
                print("🛑 Останавливаю бота...")
                await self.application.stop()

            print("👋 Бот остановлен")


# ========== ЗАПУСК ==========
def main():
    """Точка входа"""
    print("🤖 Телеграм бот для мониторинга форм")
    print("-" * 60)

    # Создаем тестовый файл если нужно
    if not os.path.exists(JSON_FILE):
        print(f"📝 Создаю файл {JSON_FILE}...")
        with open(JSON_FILE, 'w') as f:
            json.dump([], f)

    # Проверяем зависимости
    try:
        import telegram
        from PIL import Image
    except ImportError as e:
        print(f"❌ Не хватает библиотеки: {e}")
        print("\n📦 Установите зависимости:")
        print("   pip install python-telegram-bot pillow")
        return

    # Запускаем бота
    bot = FormMonitorBot()

    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")


if __name__ == "__main__":
    main()