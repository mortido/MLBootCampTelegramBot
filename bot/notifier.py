import formatter
import os
import json

class Notifier():
    # TODO: remove chart from this class
    def __init__(self, main_chat_id, subscriptions_file_name, chart):
        self._subscriptions_file_name = subscriptions_file_name
        self._chart = chart
        self._main_chat_id = main_chat_id
        self.subscriptions = self._load_subscriptions()

    def notify_main_chat(self, bot):
        top_data = self._chart.get_top_updates()
        if top_data:
            message = formatter.format_top(top_data)
            bot.send_message(chat_id=self._main_chat_id, text=message, parse_mode='Markdown')

    def notify_subscribers(self, bot):
        #TODO: do not notify if changes related only with player own updates.
        for chat_id, player_id in self.subscriptions.items():
            update_data, user_data = self._chart.get_personal_updates(player_id)
            if update_data is not None:
                message = formatter.format_personal_updates(update_data, user_data)
                bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

    def subscribe(self, chatid, player_id):
        self.subscriptions[chatid] = player_id
        self._save_subscriptions()

    def unsubscribe(self, chatid):
        del self.subscriptions[chatid]
        self._save_subscriptions()

    def _load_subscriptions(self):
        if os.path.exists(self._subscriptions_file_name):
            with open(self._subscriptions_file_name) as file:
                try:
                    return json.load(file)
                except:
                    return {}
        else:
            return {}

    def _save_subscriptions(self):
        with open(self._subscriptions_file_name, "w") as file:
            json.dump(self.subscriptions, file, indent=4)
