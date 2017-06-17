def format_top(top):
    table = "\n".join("{}{}{}{}".format(
        str(i + 1).ljust(3),
        user["name"].ljust(25),
        str(user["score"]).ljust(10),
        user["status"].ljust(4),
    ) for i, user in enumerate(top))
    return "Топ обновился!\n```\n" + table + "\n```"


def format_personal_updates(update_data, user_data):
    table = "\n".join("{}{}{}{}".format(
        str(user["place"]).ljust(3),
        user["name"].ljust(25),
        str(user["score"]).ljust(10),
        user["status"].ljust(4),
    ) for i, user in enumerate(update_data[:10]))
    if len(update_data) > 10:
        table += '\n ...and ' + str(len(update_data) - 10) + ' others'
    table += '\n ...\n'
    table += "{}{}{}{}".format(
        str(user_data["place"]).ljust(3),
        user_data["name"].ljust(25),
        str(user_data["score"]).ljust(10),
        user_data["status"].ljust(4),
    )
    return "Обходят!!\n```\n" + table + "\n```"
