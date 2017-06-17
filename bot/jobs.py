# TODO: Threads to prevent waiting on request?... if so locks to notifier/chart is required

from telegram.error import TelegramError

import formatter


def gather_ratings(bot, job):
    job.context['chart'].check_updates()


def notify_about_changes(bot, job):
    # TODO: do not notify if changes related only with player own updates.

    # User subscriptions
    subs = job.context['notifier'].get_subscriptions_by_type('place_tracking')
    for sub in subs:
        chat_id = sub['chat_id']
        player_id = sub['data']['uid']
        update_data, user_data = job.context['chart'].get_personal_updates(player_id)
        if update_data is not None:
            message = formatter.format_personal_updates(update_data, user_data)
            try:
                bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
            except TelegramError:
                print(1)
                pass

    # Top N subscriptions
    subs = job.context['notifier'].get_subscriptions_by_type('top_tracking')
    top_data = job.context['chart'].get_top_updates()
    if top_data:
        message = formatter.format_top(top_data)
        for sub in subs:
            try:
                bot.send_message(chat_id=sub['chat_id'], text=message, parse_mode='Markdown')
            except TelegramError as e:
                print(e)
                pass

    job.context['chart'].reset_changes()
