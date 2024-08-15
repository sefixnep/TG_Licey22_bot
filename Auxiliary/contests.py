from Auxiliary.chat import *
from math import ceil
from datetime import datetime, timedelta


# Contests
storage = {'past': list(), 'present': list(), 'future': list()}


def update(lst: list, tense):
    lst.clear()
    contests_tense = operations.contests_filter_tense(tense)
    amount_pages = ceil(len(contests_tense) / (config.page_shape_contests[0] * config.page_shape_contests[1]))

    if amount_pages == 0:
        lst.append(((button.back_to_contests_tense,),))
        return None

    def leafing(number: int):
        if amount_pages == 1:
            return ((button.back_to_contests_tense,),)
        elif amount_pages > 1 and number == 0:
            return ((button.back_to_contests_tense,
                     Button(" >> ", f"right_{tense}_{number + 1}_contests")),)
        elif amount_pages > 1 and number == amount_pages - 1:
            return ((Button(" << ", f"left_{tense}_{number - 1}_contests"),
                     button.back_to_contests_tense,),)
        else:
            return ((Button(" << ", f"left_{tense}_{number - 1}_contests"),
                     button.back_to_contests_tense,
                     Button(" >> ", f"right_{tense}_{number + 1}_contests")),)

    for page_number in range(amount_pages):
        Button("🔙 Назад 🔙", f'back_to_{tense}_{page_number}_contests')
        page = tuple()
        for i in range(config.page_shape_contests[0]):
            line = tuple()
            for j in range(config.page_shape_contests[1]):
                count = (page_number * config.page_shape_contests[0] * config.page_shape_contests[1] + i *
                         config.page_shape_contests[1] + j)
                if len(contests_tense) == count:  # Если все конкурсы размещены
                    if j:  # Если на строчке есть конкурсы
                        page += (line,)
                    page += leafing(page_number)
                    lst.append(page)
                    return None

                contest = contests_tense[count]
                callback_data = f'{contest[config.contest_indices.index("id")]}_contest'

                dates = [datetime.strptime(contest[config.contest_indices.index(mode)], "%Y-%m-%d")
                         .strftime("%d.%m.%Y") for mode in ("date_start", "date_end")]
                comment = contest[config.contest_indices.index('comment')]

                Button(contest[config.contest_indices.index('name')], callback_data)
                Message(f"🆔: `{contest[config.contest_indices.index('id')]}`\n"
                        f"*Конкурс*: `{contest[config.contest_indices.index('name')]}`\n"
                        f"├ *Дата проведения*: `{' - '.join(dates)}`\n"
                        f"└ *Предметы*: `{', '.join(contest[config.contest_indices.index('tags')])}`\n" +
                        (f"\n_Примечание: {comment}_" if comment else ""),
                        ((Button("Перейти", contest[config.contest_indices.index('link')], is_link=True),),
                         (getattr(button, f'back_to_{tense}_{len(lst)}_contests'),),),
                        getattr(button, callback_data))

                line += (getattr(button, callback_data),)
            page += (line,)

        page += leafing(page_number)
        lst.append(page)
