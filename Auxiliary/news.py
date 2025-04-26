from Auxiliary.chat import *
from math import ceil

storage = list()

def update(lst):
    lst.clear()
    news = operations.get_all_news()
    amount_pages = ceil(len(news) / (config.page_shape_news[0] * config.page_shape_news[1]))

    if amount_pages == 0:
        lst.append(((button.back_to_start,),))
        return

    def leafing(number: int):
        if amount_pages == 1:
            return (button.back_to_start,)
        elif amount_pages > 1 and number == 0:
            return (button.back_to_start,
                     Button(" >> ", f"right_{number + 1}_news_page"))
        elif amount_pages > 1 and number == amount_pages - 1:
            return (Button(" << ", f"left_{number - 1}_news_page"),
                     button.back_to_start,)
        else:
            return (Button(" << ", f"left_{number - 1}_news_page"),
                     button.back_to_start,
                     Button(" >> ", f"right_{number + 1}_news_page"))

    for page_number in range(amount_pages):
        Button("🔙 Назад 🔙", f'back_to_{page_number}_news_page')
        page = tuple()
        for i in range(config.page_shape_news[0]):
            line = tuple()
            for j in range(config.page_shape_news[1]):
                count = (page_number * config.page_shape_news[0] * config.page_shape_news[1] +
                         i * config.page_shape_news[1] + j)
                if len(news) == count:
                    if j:
                        page += (line,)
                    page += (leafing(page_number),)
                    lst.append(page)
                    return

                item = news[count]
                callback_data = f'news_{item[config.news_indices.index("id")]}'

                date = item[config.news_indices.index("date")].strftime('%H:%M (%d.%m.%Y)')

                Button(item[config.news_indices.index('name')], callback_data)
                Message(f"🆔: <code>{item[config.news_indices.index('id')]}</code>\n"
                        f"<b>Новость</b>: <code>{item[config.news_indices.index('name')]}</code>\n"
                        f"<b>Дата создания</b>: <code>{date}</code>\n"
                        f"<b>Описание</b>: {item[config.news_indices.index('description')]}\n",
                        ((getattr(button, f'back_to_{page_number}_news_page'),),),
                        getattr(button, callback_data))

                line += (getattr(button, callback_data),)
            page += (line,)

        page += (leafing(page_number),)
        lst.append(page)


update(storage)
