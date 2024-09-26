import json
import re
from asyncio import create_task, gather
from itertools import count
from time import sleep

import undetected_chromedriver as uc
from httpx import AsyncClient, Limits, Timeout
from parsel import Selector
from selenium.webdriver.common.by import By

driver = uc.Chrome(headless=False)


async def get_all_pages_data(url):
    async with AsyncClient(
        timeout=Timeout(10, pool=10),
        limits=Limits(max_connections=100, max_keepalive_connections=0),
    ) as client:
        tasks = []
        items_selector = 1
        for i in count(1):
            if 'dcp' in url:
                url = re.sub(re.compile(r'.dcp=\d+'), f'#dcp={i}', url)
            driver.get(url)
            sleep(1)
            items = driver.find_elements(By.CSS_SELECTOR, '.ProductImageList')
            if i == 1 and not items or items_selector == 2:
                items = driver.find_elements(
                    By.CSS_SELECTOR,
                    '.ProductCardForGrid_productCardSkeletonLink__12uxY',
                )
                items.extend(
                    driver.find_elements(
                        By.CSS_SELECTOR, '.ProductCard_link__cCkNX'
                    )
                )
                items_selector = 2
            if items:
                for item in items:
                    tasks.append(
                        create_task(
                            get_page_data(client, item.get_attribute('href'))
                        )
                    )
            else:
                break
        response = await gather(*tasks)
        return response


async def get_all_pages_data_lovellsoccer(url):
    async with AsyncClient(
        timeout=Timeout(10, pool=10),
        limits=Limits(max_connections=100, max_keepalive_connections=0),
    ) as client:
        tasks = []
        try:
            url = re.findall(r'(.+)#', url, re.DOTALL)[0]
        except IndexError:
            pass
        urls = []
        for i in count(1):
            if '#page' in url:
                url = re.sub(re.compile(r'#page=\d+'), f'#page={i}', url)
            else:
                url += f'#page={i}'
            driver.get(url)
            sleep(1)
            items = driver.find_elements(By.CSS_SELECTOR, '.item.clearfix a')
            if not items:
                break
            for item in items:
                if item.get_attribute('href') not in urls:
                    urls.append(item.get_attribute('href'))
            for item_url in urls:
                tasks.append(
                    create_task(get_page_data_lovellsoccer(client, item_url))
                )
        response = await gather(*tasks)
        indexes = []
        for _ in range(10):
            tasks = []
            for i, item in enumerate(response):
                if item is None and i not in indexes:
                    tasks.append(
                        create_task(
                            get_page_data_lovellsoccer(client, urls[i])
                        )
                    )
            remain = await gather(*tasks)
            indexes.extend([urls.index(r['url']) for r in remain if r])
            response.extend([r for r in remain if r])
            if [r for r in remain if r is None]:
                continue
            for index in indexes:
                response.pop(index)
            break
        response = [r for r in response if r]
        return response


async def get_page_data(client, url):
    try:
        response = await client.get(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0',
            },
        )
        if response.status_code == 403:
            return await get_page_data(client, url)
    except:
        return await get_page_data(client, url)
    selector = Selector(response.text)
    color_code = re.findall(r'colcode=(\d+)', url, re.DOTALL)[0]
    try:
        main_data = json.loads(
            selector.css('.ProductDetailsVariants').attrib['data-variants']
        )
    except KeyError:
        try:
            json_data = json.loads(
                selector.css('[type="application/ld+json"]::text')[-1].get()
            )
        except IndexError:
            return
        domain = re.findall(r'https://.+?/', url, re.DOTALL)
        for data in json_data['offers']['offers']:
            if data['gtin8'] == color_code:
                size = ', '.join(
                    [
                        i.attrib['value']
                        for i in selector.css(
                            'div[data-testid="variant-selector-items"] button[data-testid="swatch-button-enabled"]'
                        )
                    ]
                )
                return {
                    'url': url,
                    'foto': f'{domain}images/products/{data["gtin8"]}_piat.jpg',
                    'codigo': data['gtin8'],
                    'descricao': f'{data["itemOffered"]["name"]} - {data["itemOffered"]["color"]}',
                    'valor': float(data['price']),
                    'tamanhos': size,
                }
        return
    layer_data = json.loads(
        re.findall(
            r'var dataLayerData = (\{.+?\})\;', response.text, re.DOTALL
        )[0]
    )
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
        return
    selector = Selector(response.text)
    try:
        data = json.loads(
            selector.css('script[type="application/ld+json"]::text').get()
        )
    except TypeError:
        return
    domain = re.findall(r'https://.+?/', url, re.DOTALL)
    code = re.findall(r'/(\d+)$', url)[0]
    return {
        'url': url,
        'foto': f'{domain}products/{code}.jpg?width=90',
        'codigo': code,
        'descricao': data['name'],
        'valor': float(data['offers']['price']),
        'tamanhos': ', '.join(
            selector.css('.orderButton.size span::text').getall()
        ),
    }
