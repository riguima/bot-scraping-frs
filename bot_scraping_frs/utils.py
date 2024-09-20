from httpx import get


def convert_value(value):
    results = {
        15: value + 2.50,
        30: value + 2.50 + 10,
        50: value + 2.50 + 15,
        80: value + 5 + 20,
        120: value + 5 + 25,
        150: value + 5 + 30,
        200: value + 5 + 35,
        300: value + 10 + 40,
        400: value + 10 + 50,
        500: value + 10 + 60,
        800: value + 10 + 70,
        1000: value + 10 + 80,
        1500: value + 10 + 80,
        2000: value + 10 + 100,
        3000: value + 10 + 120,
        4000: value + 10 + 140,
        5000: value + 10 + 160,
        6000: value + 10 + 180,
        7000: value + 10 + 200,
    }
    for limit, result in results.items():
        if value < limit:
            gbp_value = float(
                get(
                    'https://economia.awesomeapi.com.br/json/last/GBP-BRL'
                ).json()['GBPBRL']['bid']
            )
            result = result + (result * 0.023) + (result * 0.053)
            return round(result * gbp_value)
    return round(value)


def format_number(number, symbol):
    return f'{symbol} {number:.2f}'.replace('.', ',')
