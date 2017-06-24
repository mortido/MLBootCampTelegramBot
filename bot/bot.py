import logging

from telegram.ext import Updater, CommandHandler

import jobs
import storage
from chart import Chart
from notifier import Notifier

# TODO: log errors to telegram
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)

logger = logging.getLogger(__name__)

notifier = None
chart = None


def start_handler(bot, update):
    chat_id = update.message.chat_id
    if chat_id < 0:
        # Prevent working in groups
        return
    update.message.reply_text(
        'Hi!\nЧтобы подписаться на обновления своих результатов используй команду `/subscribe user_id` .\n\n'
        + 'Для получения `user_id` в консоли браузера на странице с результатами выполни: '
        + ' ```\n$(\'li.players__item[style="background-color: #0858a8"]\').attr(\'id\') ```\n\n'
        + 'Пока так...', parse_mode='Markdown')


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

    subs = notifier.get_subscriptions_by_chat_and_type(chat_id, 'place_tracking')
    if subs:
        update.message.reply_text('Сменил подписку на ' + uid)
        for sub in subs:
            notifier.remove_subscription_by_id(sub['id'])
    else:
        update.message.reply_text('Подписался')
    notifier.add_subscription(chat_id, 'place_tracking', {'uid': uid})


def unsubscribe_handler(bot, update):
    chat_id = update.message.chat_id
    if chat_id < 0:
        # Prevent working in groups
        return
    subs = notifier.get_subscriptions_by_chat_and_type(chat_id, 'place_tracking')
    if subs:
        for sub in subs:
            notifier.remove_subscription_by_id(sub['id'])
        update.message.reply_text('Отписался от обновлений')
    else:
        update.message.reply_text('Нет активных подписок')


def main():
    global notifier, chart

    config = storage.load_from_file('config.json')
    if config is None:
        print("Can't open configuration file")
        return

    chart = Chart(config['ratings_url'], config['users_file_name'], config['warm_start'])
    notifier = Notifier(config['subscriptions_file_name'])
    updater = Updater(config['auth_token'])

    dp = updater.dispatcher
    dp.add_error_handler(error_handler)
    dp.add_handler(CommandHandler(["start", "help"], start_handler))
    dp.add_handler(CommandHandler("subscribe", subscribe_handler, pass_args=True))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe_handler))

    job_queue = updater.job_queue
    job_queue.run_repeating(jobs.gather_ratings,
                            config['update_rate'],
                            first=0.0,
                            context={
                                'chart': chart
                            })

    job_queue.run_repeating(jobs.notify_about_changes,
                            config['notify_rate'],
                            first=0.0,
                            context={
                                'notifier': notifier,
                                'chart': chart,
                            })

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
