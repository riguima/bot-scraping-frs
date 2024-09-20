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
    main_data = json.loads(
        selector.css('.ProductDetailsVariants').attrib['data-variants']
    )
    layer_data = json.loads(
        re.findall(
            r'var dataLayerData = (\{.+?\})\;', response.text, re.DOTALL
        )[0]
    )
    color_code = re.findall(r'colcode=(\d+)', url, re.DOTALL)[0]
    for data in main_data:
        if data['ColVarId'] == color_code:
            return {
                'url': url,
                'foto': data['MainImageDetails']['ImgUrlLarge'],
                'codigo': layer_data['productId'],
                'descricao': f'{layer_data["pageTitle"]} - {data["ColourName"]}',
                'valor': data['ProdVarPrices']['SellPriceRaw'],
            }
