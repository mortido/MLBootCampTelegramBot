import json
import logging

from telegram.ext import Updater, CommandHandler

from chart import Chart
from notifier import Notifier

# TODO: log errors to telegram
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)

logger = logging.getLogger(__name__)

notifier = None
chart = None


def load_config():
    with open("config.json") as file:
        return json.load(file)


def start_handler(bot, update):
    chat_id = update.message.chat_id
    if chat_id < 0:
        # Prevent working in groups
        return
    update.message.reply_text('Hi!\n Чтобы подписаться на обновления используй команду /subscribe %user_id%\n'
                              + 'Для получения id исаользуй `$(\'li.players__item[style="background-color: #0858a8"]\').attr(\'id\')` ' +
                              'в консоле браузера на странице с результатами... пока так...')


def error_handler(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def subscribe_handler(bot, update, args):
    chat_id = update.message.chat_id
    if chat_id < 0:
        # Prevent working in groups
        return

    if not args:
        update.message.reply_text('Укажи id\n```\n/subscribe player1234\n```', parse_mode='Markdown')
        return
    uid = args[0]
    if uid not in chart.users:
        update.message.reply_text('Не могу найти пользователя с данным id')
        return

    if chat_id in notifier.subscriptions:
        update.message.reply_text('Сменил подписку на ' + uid)
    else:
        update.message.reply_text('Подписался')
    notifier.subscribe(chat_id, uid)


def unsubscribe_handler(bot, update):
    chat_id = update.message.chat_id
    if chat_id < 0:
        # Prevent working in groups
        return

    if chat_id not in notifier.subscriptions:
        update.message.reply_text('Нет активных подписок')
        return

    notifier.unsubscribe(chat_id)
    update.message.reply_text('Отписался от обновлений')


def gather_ratings(bot, job):
    job.context['chart'].check_updates()


def notify_about_changes(bot, job):
    # TODO: Threads to prevent waiting on request?...
    job.context['notifier'].notify_main_chat(bot)
    job.context['notifier'].notify_subscribers(bot)
    job.context['chart'].reset_changes()


def main():
    global notifier, chart

    config = load_config()
    chart = Chart(config['ratings_url'], config['users_file_name'], config['top_n_to_track'])
    notifier = Notifier(config['main_chat_id'], config['subscriptions_file_name'], chart)
    updater = Updater(config['auth_token'])

    dp = updater.dispatcher
    dp.add_error_handler(error_handler)
    dp.add_handler(CommandHandler(["start", "help"], start_handler))
    dp.add_handler(CommandHandler("subscribe", subscribe_handler, pass_args=True))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe_handler))

    job_queue = updater.job_queue
    job_queue.run_repeating(gather_ratings,
                            config['update_rate'],
                            first=0.0,
                            context={'chart': chart}
                            )
    job_queue.run_repeating(notify_about_changes,
                            config['notify_rate'],
                            first=0.0,
                            context={'notifier': notifier,
                                     'chart': chart}
                            )

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
