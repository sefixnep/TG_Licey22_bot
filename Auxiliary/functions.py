import re


def is_valid_url(string: str):
    # Регулярное выражение для проверки URL
    url_regex = re.compile(
        r'^(?:http|ftp)s?://'  # Проверка на схемы http, https, ftp, ftps
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # Доменное имя
        r'localhost|'  # Локальный хост
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IP-адрес (IPv4)
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # IP-адрес (IPv6)
        r'(?::\d+)?'  # Порт (опционально)
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # Конечный путь

    return re.match(url_regex, string) is not None
