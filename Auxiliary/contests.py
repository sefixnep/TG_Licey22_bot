from Auxiliary.chat import *
from math import ceil
from datetime import datetime


# Contests
storage = {'past': list(), 'present': list(), 'future': list()}

def update(lst: list, tense: str):
    lst.clear()
    contests_tense = operations.contests_filter_tense(tense)
    amount_pages = ceil(len(contests_tense) / (config.page_shape_contests[0] * config.page_shape_contests[1]))

    if amount_pages == 0:
        lst.append(((button.back_to_contests,),))
        return

    def leafing(number: int):
        if amount_pages == 1:
            return (button.back_to_contests,)
        elif amount_pages > 1 and number == 0:
            return ((button.back_to_contests,
                     Button(" >> ", f"right_{tense}_{number + 1}_contests_page")),)
        elif amount_pages > 1 and number == amount_pages - 1:
            return (Button(" << ", f"left_{tense}_{number - 1}_contests_page"),
                     button.back_to_contests,)
        else:
            return (Button(" << ", f"left_{tense}_{number - 1}_contests_page"),
                     button.back_to_contests,
                     Button(" >> ", f"right_{tense}_{number + 1}_contests_page"))

    for page_number in range(amount_pages):
        Button("🔙 Назад 🔙", f'back_to_{tense}_{page_number}_contests_page')
        page = tuple()
        for i in range(config.page_shape_contests[0]):
            line = tuple()
            for j in range(config.page_shape_contests[1]):
                count = (page_number * config.page_shape_contests[0] * config.page_shape_contests[1] +
                         i * config.page_shape_contests[1] + j)
                if len(contests_tense) == count:  # Если все конкурсы размещены
                    if j:  # Если на строчке есть конкурсы
                        page += (line,)
                    page += (leafing(page_number),)
                    lst.append(page)
                    return

                contest = contests_tense[count]
                callback_data = f'contest_{contest[config.contest_indices.index("id")]}'

                dates = [datetime.strptime(contest[config.contest_indices.index(mode)], "%Y-%m-%d")
                         .strftime("%d.%m.%Y") for mode in ("date_start", "date_end")]
                comment = contest[config.contest_indices.index('comment')]

                Button(contest[config.contest_indices.index('name')], callback_data)
                Message(f"🆔: <code>{contest[config.contest_indices.index('id')]}</code>\n"
                        f"<b>Конкурс</b>: <code>{contest[config.contest_indices.index('name')]}</code>\n"
                        f"├ <b>Дата проведения</b>: <code>{' - '.join(dates)}</code>\n"
                        f"└ <b>Предметы</b>: <code>{', '.join(contest[config.contest_indices.index('tags')])}</code>\n" +
                        (f"\n<i>Примечание: {comment}</i>" if comment else ""),
                        ((Button("Перейти", contest[config.contest_indices.index('link')], is_link=True),),
                         (getattr(button, f'back_to_{tense}_{len(lst)}_contests_page'),),),
                        getattr(button, callback_data))

                line += (getattr(button, callback_data),)
            page += (line,)

        page += (leafing(page_number),)
        lst.append(page)


for tense, lst in storage.items():
    update(lst, tense)
