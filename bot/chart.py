import json
import os

import requests
from lxml import html

USERS_PATH = '//div[@class="players__items"]/ul/li'
NAME_PATH = 'div/div[contains(@class, "players__name")]'
SCORE_PATH = 'div/div[contains(@class, "players__rating")]'
PLACE_PATH = 'div[contains(@class, "players__number")]'


class Chart:
    def __init__(self, rating_url, users_file_name, top_n_to_track):
        self._top_n_to_track = top_n_to_track
        self._users_file_name = users_file_name
        self._rating_url = rating_url
        self.users = self._load_users()
        self._changes = {}
        self._rating_table = {}

        # TODO: update in case updates since last run should be displayed
        # TODO: (but will show all updates if started first time)
        self._gather_info(False)

    def check_updates(self):
        self._gather_info()

    def reset_changes(self):
        self._changes.clear()

    def get_top_updates(self):
        has_updates = False
        for i in range(1, self._top_n_to_track + 1):
            uid = self._rating_table[i]
            # Show updates only if there are some changes in positions or new user.
            # Don't bother main chat with scores updates in top N for now.
            if uid in self._changes and (self._changes[uid] != 0 or len(self.users[uid]['scores']) == 1):
                has_updates = True
                break

        if not has_updates:
            return None

        updates = []
        for i in range(1, self._top_n_to_track + 1):
            uid = self._rating_table[i]
            user = self.users[uid]
            status = ''
            if uid in self._changes:
                change = self._changes[uid]
                if change != 0:
                    status = '^v'[change < 0] + str(abs(change))
                elif len(user['scores']) == 1:
                    status = '*'
            updates.append({
                'name': user['name'],
                'score': user['choosen_score'],
                'status': status
            })
        return updates

    def get_personal_updates(self, uid):
        # TODO: update changes detection to track even updates which move player up (but not related to his/her own changes)
        if uid in self._changes and self._changes[uid] < 0:
            user = self.users[uid]
            update_data = []
            for i in range(1, user['place'] + 1):
                other_uid = self._rating_table[i]
                other_user = self.users[other_uid]
                if other_uid in self._changes and ((other_user['place'] + self._changes[other_uid]) >= user['place']
                                                   or self._changes[other_uid] == 0 and len(other_user['scores']) == 1):
                    change = self._changes[other_uid]
                    update_data.append({
                        'place': other_user['place'],
                        'name': other_user['name'],
                        'score': other_user['choosen_score'],
                        'status': '*' if change == 0 else '^' + str(abs(change))
                    })

            user_update = {
                'place': user['place'],
                'name': user['name'],
                'score': user['choosen_score'],
                'status': 'v' + str(abs(change)) # '^v'[change < 0] + str(abs(change)) Always down for now
            }
            return update_data, user_update
        else:
            return None, None

    def _gather_info(self, track_changes=True):
        page = requests.get(self._rating_url)
        tree = html.fromstring(page.text)
        self._rating_table = {}

        for user in tree.xpath(USERS_PATH):
            uid = user.attrib['id']
            place = int(user.xpath('div[contains(@class, "players__number")]')[0].text.strip())
            name = user.xpath('div/div[contains(@class, "players__name")]')[0].text.strip()
            score = float(user.xpath('div/div[contains(@class, "players__rating")]')[0].text.strip())
            change = False

            if uid not in self.users:
                self.users[uid] = {
                    # TODO: should I use set(it's harder to parse from json)?
                    'scores': [],
                    'place': place
                }
                change = True

            if score not in self.users[uid]['scores']:
                self.users[uid]['scores'].append(score)
                change = True

            if place != self.users[uid]['place']:
                change = True

            if track_changes and change:
                self._changes[uid] = self._changes.get(uid, 0) + self.users[uid]['place'] - place

            self.users[uid]['place'] = place
            self.users[uid]['name'] = name
            self.users[uid]['choosen_score'] = score
            self._rating_table[place] = uid  # AAAAAA counting from 1!!!

        self._save_users()

    def _load_users(self):
        if os.path.exists(self._users_file_name):
            with open(self._users_file_name) as file:
                try:
                    return json.load(file)
                except:
                    return {}
        else:
            return {}

    def _save_users(self):
        with open(self._users_file_name, "w") as file:
            json.dump(self.users, file, indent=4)
