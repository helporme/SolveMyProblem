import sys
import asyncio
import aiohttp
from os import path
from bs4 import BeautifulSoup
from arsenic import get_session, browsers, services
from urllib.parse import quote

from io import BytesIO
from PIL import Image


class AsyncZnanija:
    def __init__(self, loop=asyncio.get_event_loop()):
        apath = path.dirname(path.dirname(__file__))
        sys.path.append(path.abspath(apath))

        self.bin = apath + '/solvemyproblem/drivers/phantomjs/bin/phantomjs.exe'
        self.link = 'https://znanija.com/app/ask?entry=hero&q='

        self.browser = browsers.PhantomJS()
        self.service = services.PhantomJS(binary=self.bin)

        self.loop = loop

    async def search(self, quest):
        async with get_session(self.service, self.browser) as session:
            await session.get(self.link + quote(quest))
            await session.wait_for_element(3, '.sg-layout__box')

            source = await session.get_page_source()
            soup = BeautifulSoup(source, features="lxml")
            links = [link.get('href') for link in soup.find_all('a') if '/task/' in link.get('href')]

            tasks = [links[n] for n in range(0, len(links), 2)]
            screen = await session.get_screenshot()

            await session.close()
            return tasks, crop(screen)

    async def fetch_url(self, session, url):
        async with session.get(url) as response:
            return await response.text()

    async def fetch_image(self, session, url):
        async with session.get(url) as response:
            return await response.read()

    async def answer(self, task):
        async with aiohttp.ClientSession() as session:
            source = await self.fetch_url(session, f'https://znanija.com{task}')

            image = None
            if 'brn-main-attachment--loading js-attachment-image-wrapper' in source:
                target = '-loading js-attachment-image-wrapper ">\n<img src="'
                image_part = source[source.find(target)+len(target):]
                image_link = image_part[:image_part.find('" title="Приложение" alt="">')]
                image = await self.fetch_image(session, image_link)

            answers = []
            while 'sg-text js-answer-content brn-rich-content' in source:
                target = 'js-answer-content brn-rich-content" data-test="answer-content">'
                answer_part = source[source.find(target)+len(target):]
                answer = answer_part[:answer_part.find('</div>')]

                for html_part in ['</p>', '<br>', '<br />']:
                    answer = answer.replace(html_part, '\n')
                for html_part in ['<p>']:
                    answer = answer.replace(html_part, '')

                source = answer_part
                answers.append(answer)

            return answers, image


def crop(screen):
    image = Image.open(screen)
    area = (0, 60, 400, 1350)
    image = image.crop(area)

    sbytes = BytesIO()
    image.save(sbytes, format='PNG')
    return sbytes.getvalue()
