def format_rating_table_row(row_data):
    return "{}{}{}{}".format(
        str(row_data['place']).ljust(4),
        row_data["name"].ljust(25),
        str(row_data["score"]).ljust(10),
        row_data["status"].ljust(4))


def format_top(top):
    table = "\n".join(map(format_rating_table_row, top))
    return "```\n" + table + "\n```"


def format_personal_updates(update_data, user_data):
    table = "\n".join(map(format_rating_table_row, update_data[:10]))
    if len(update_data) > 10:
        table += '\n ...and ' + str(len(update_data) - 10) + ' others'
    table += '\n ...\n'
    table += format_rating_table_row(user_data)
    return "```\n" + table + "\n```"
