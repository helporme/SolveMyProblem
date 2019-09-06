import asyncio
import sys

from os import path
from arsenic import get_session, browsers, services, keys


class AsyncTigerAlgebra:
    def __init__(self, loop=asyncio.get_event_loop()):
        apath = path.dirname(path.dirname(__file__))
        sys.path.append(path.abspath(apath))

        self.bin = apath + '/solvemyproblem/drivers/phantomjs/bin/phantomjs.exe'
        self.link = 'https://www.tiger-algebra.com/'

        self.browser = browsers.PhantomJS()
        self.service = services.PhantomJS(binary=self.bin)

        self.loop = loop

    async def solve(self, problem):
        async with get_session(self.service, self.browser) as session:
            await session.get(self.link)
            box = await session.get_element('#ctl00_drill')
            await box.send_keys(problem)
            await box.send_keys(keys.RETURN)

            solution = await session.get_element('.solution')
            text = await solution.get_text()

            answers = []
            for stroke in text.split('\n')[2:]:
                if 'Rearrange' in stroke or 'ends' in stroke:
                    break
                elif any(word in stroke for word in ['Terminated', 'Quadratic']):
                    return

                answers.append(stroke[1:] if stroke.startswith(' ') else stroke)

            await session.close()
            return '\n'.join(answers)
