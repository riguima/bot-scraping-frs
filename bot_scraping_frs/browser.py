import json
import re
from asyncio import create_task, gather
from itertools import count

from httpx import AsyncClient
from parsel import Selector


async def get_all_pages_data(url):
    async with AsyncClient() as client:
        domain, path = re.findall(r'(https://.+?)/(.+?)$', url, re.DOTALL)[0]
        tasks = []
        for i in count(1):
            if 'dcp' in url:
                url = re.sub(re.compile(r'.dcp=\d+'), f'?dcp={i}', url)
            else:
                url = url.replace(path, f'{path}#dcp={i}')
            response = await client.get(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0',
                },
            )
            selector = Selector(response.text)
            items = selector.css('.ProductImageList')
            if items:
                for item in items:
                    tasks.append(
                        create_task(
                            get_page_data(
                                client, f'{domain}{item.attrib["href"]}'
                            )
                        )
                    )
            else:
                break
        response = await gather(*tasks)
        return response


async def get_all_pages_data_lovellsoccer(url):
    async with AsyncClient() as client:
        tasks = []
        try:
            url = re.findall(r'(.+)#', url, re.DOTALL)[0]
        except IndexError:
            pass
        url += '/page/all'
        response = await client.get(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0',
            },
        )
        selector = Selector(response.text)
        items = selector.css('.item.clearfix a')
        urls = []
        for item in items:
            if item.attrib['href'] not in urls:
                urls.append(item.attrib['href'])
        for url in urls:
            tasks.append(create_task(get_page_data_lovellsoccer(client, url)))
        response = await gather(*tasks)
        return response


async def get_page_data(client, url):
    try:
        response = await client.get(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0',
            },
        )
    except:
        return await get_page_data(client, url)
    selector = Selector(response.text)
    try:
        main_data = json.loads(
            selector.css('.ProductDetailsVariants').attrib['data-variants']
        )
    except KeyError:
        return
    layer_data = json.loads(
        re.findall(
            r'var dataLayerData = (\{.+?\})\;', response.text, re.DOTALL
        )[0]
    )
    color_code = re.findall(r'colcode=(\d+)', url, re.DOTALL)[0]
    for data in main_data:
        if data['ColVarId'] == color_code:
            size = ', '.join(
                [size['SizeName'].split()[0] for size in data['SizeVariants']]
            )
            return {
                'url': url,
                'foto': data['MainImageDetails']['ImgUrlThumb'],
                'codigo': layer_data['productId'],
                'descricao': data['MainImageDetails']['AltText'],
                'valor': data['ProdVarPrices']['SellPriceRaw'],
                'tamanhos': size,
            }
    size = ', '.join(
        [size['SizeName'].split()[0] for size in main_data[0]['SizeVariants']]
    )
    return {
        'url': url,
        'foto': main_data[0]['MainImageDetails']['ImgUrlThumb'],
        'codigo': layer_data['productId'],
        'descricao': main_data[0]['MainImageDetails']['AltText'],
        'valor': main_data[0]['ProdVarPrices']['SellPriceRaw'],
        'tamanhos': size,
    }


async def get_page_data_lovellsoccer(client, url):
    try:
        response = await client.get(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0',
            },
        )
    except:
        return await get_page_data_lovellsoccer(client, url)
    selector = Selector(response.text)
    data = json.loads(
        selector.css('script[type="application/ld+json"]::text').get()
    )
    code = re.findall(r'/(\d+)$', url)[0]
    return {
        'url': url,
        'foto': f'https://lovellcdn.b-cdn.net/products/{code}.jpg?width=90',
        'codigo': code,
        'descricao': data['name'],
        'valor': float(data['offers']['price']),
        'tamanhos': ', '.join(
            selector.css('.orderButton.size span::text').getall()
        ),
    }
