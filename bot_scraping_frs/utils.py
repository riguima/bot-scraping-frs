from asyncio import create_task, gather

from httpx import AsyncClient, get


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


async def get_image_content(client, image_url):
    try:
        response = await client.get(image_url, timeout=1000)
    except:
        return await get_image_content(client, image_url)
    return response.content


async def get_all_images_content(images_urls):
    tasks = []
    async with AsyncClient() as client:
        for image_url in images_urls:
            tasks.append(create_task(get_image_content(client, image_url)))
        response = await gather(*tasks)
        return response
