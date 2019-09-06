import asyncio

from os import environ
from googletrans import Translator, LANGUAGES

from telebotapi.telebotapi import Bot
from solvemyproblem.znanija import AsyncZnanija
from solvemyproblem.tigeralgebra import AsyncTigerAlgebra
from solvemyproblem.wikipedia import Wikipedia


bot = Bot(environ('token'), prefix='', dest=None)
DEV = [971379586]


@bot.command_handler('start')
def start_message(message):
    text = 'Привет! Для поиска решения задач просто напишите их условие боту. Например: "2x+2=0"'
    bot.send_message(message.chat.id, text)


@bot.command_handler()
def info(message):
    for key, value in message.update.items():
        bot.send_message(message.chat.id, f'{key}: {value}')

        
@bot.command_handler('eval', access_to=DEV)
def _eval(message):
    try:
        res = eval(message.text)
        bot.send_message(message.chat.id, res)

    except Exception as e:
        bot.send_message(message.chat.id, str(e))

        
@bot.command_handler('z', 'з')
def znanija_search(message):
    if message.text.replace(' ', '') == '':
        bot.send_message(message.chat.id, 'Напишите задачу или её часть')
        message = bot.wait_for_message(message.chat.id)

    bot.send_message(message.chat.id, 'Поиск в znanija.com..')

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    znanija = AsyncZnanija()
    tasks, image = loop.run_until_complete(znanija.search(message.text))

    if tasks == []:
        return False

    bot.send_message(message.chat.id, f'Выберите 1 из {len(tasks)} задач')
    bot.send_photo(message.chat.id, image)

    message = bot.wait_for_message(message.chat.id)
    answers, image = loop.run_until_complete(znanija.answer(tasks[int(message.text)-1]))

    for n, answer in enumerate(answers):
        bot.send_message(message.chat.id, f'[Ответ пользователя {n+1}]\n {answer}')

    if image is not None:
        bot.send_message(message.chat.id, '[Приложение]')
        bot.send_photo(message.chat.id, image)

    return True


@bot.command_handler('t', 'т')
def tigeralgebra_search(message):
    if message.text.replace(' ', '') == '':
        bot.send_message(message.chat.id, 'Напишите пример')
        message = bot.wait_for_message(message.chat.id)

    sym_pass = tuple('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    for sym in sym_pass:
        if sym in message.text or sym.upper() in message.text:
            return False

    bot.send_message(message.chat.id, 'Поиск в tiger-algebra.com..')

    tigeralebra = AsyncTigerAlgebra()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    answer = loop.run_until_complete(tigeralebra.solve(message.text))
    if answer is None:
        return False

    bot.send_message(message.chat.id, answer)
    return True


@bot.command_handler('tr', 'translate', 'тр', 'перевод')
def translate(message):
    if message.text.replace(' ', '') == '':
        if bot._else['dest'] is None:
            bot.send_message(message.chat.id, 'Напишите на какой язык перевести, пример: "en"')
            message = bot.wait_for_message(message.chat.id)
            bot._else['dest'] = message.text
        dest = bot._else['dest']

        bot.send_message(message.chat.id, 'Напишите текст')
        message = bot.wait_for_message(message.chat.id)
        text = message.text

    else:
        args = message.text.split(' ', 1)
        if len(args) == 1:
            text = args[0]
            dest = bot._else['dest']

            if dest is None:
                text = 'Стандартный язык для перевода не установлен, вы можете' \
                       'выбрать его, написав /tr <язык> <текст> или /tr >> язык >> текст'
                bot.send_message(message.chat.id, text)
                return

        else:
            dest, text = tuple(args)

            if dest in LANGUAGES:
                bot._else['dest'] = dest
            else:
                dest = bot._else['dest'],
                text = message.text

    translator = Translator()
    src = translator.detect(text).lang

    try:
        translation = translator.translate(text, src=src, dest=dest)
        if translation.text != text:
            bot.send_message(message.chat.id, f'[{src.upper()} > {dest.upper()}]\n{translation.text}')
        return translation.text
    except ValueError:
        bot.send_message(message.chat.id, 'Неизвестный язык')


@bot.command_handler('w', 'wiki', 'wikipedia', 'в', 'вики', 'википедия')
def wikipeida(message):
    if message.text.replace(' ', '') == '':
        bot.send_message(message.chat.id, 'Напишите название статьи')
        message = bot.wait_for_message(message.chat.id)

    bot.send_message(message.chat.id, 'Поиск в ru.wikipedia.org..')
    sections = Wikipedia(message.text).sections()
    if sections == {}:
        bot.send_message(message.chat.id, 'Такой статьи не существует')
        return False

    text = '\n'.join([f'{n+1}. {key}' for n, key in enumerate(sections.keys())])
    bot.send_message(message.chat.id, 'Выберете секции через запятую:\n' + text)
    message = bot.wait_for_message(message.chat.id)

    selected_sections = [int(n)-1 for n in message.text.replace(' ', '').split(',')]
    for n, (key, value) in enumerate(sections.items()):
        if n in selected_sections:
            resp = bot.send_message(message.chat.id, f'[{key}]\n{value}')
            if resp['ok'] is False:
                splited_value = [value[i:i+2000] for i in range(0, len(value), 2000)]
                bot.send_message(message.chat.id, f'[{key}]')
                for val in splited_value:
                    bot.send_message(message.chat.id, val)

    return True


@bot.command_handler('m', 'morse', 'м', 'морзе')
def morse(message):
    if message.text.replace(' ', '') == '':
        bot.send_message(message.chat.id, 'Напишите текст')
        message = bot.wait_for_message(message.chat.id)

    message.text = 'en ' + message.text
    message.text = translate(message)

    codes = {
        '•-'   : 'A', '-•••' : 'B',
        '-•-•' : 'C', '-••'  : 'D',
        '•'    : 'E', '••-•' : 'F',
        '--•'  : 'G', '••••' : 'H',
        '••'   : 'I', '•---' : 'J',
        '-•-'  : 'K', '•-••' : 'L',
        '--'   : 'M', '-•'   : 'N',
        '---'  : 'O', '•--•' : 'P',
        '--•-' : 'Q', '•-•'  : 'R',
        '•••'  : 'S', '-'    : 'T',
        '••-'  : 'U', '•••-' : 'V',
        '•--'  : 'W', '-••-' : 'X',
        '-•--' : 'Y', '--••' : 'Z',
        '•----': '1', '••---': '2',
        '•••--': '3', '••••-': '4',
        '•••••': '5', '-••••': '6',
        '--•••': '7', '---••': '8',
        '----•': '9', '-----': '0'
    }

    text_type = 'morse'
    for sym in tuple(message.text):
        if sym not in ['-', '•', ' ']:
            text_type = 'text'

    res = ''
    if text_type == 'text':
        for sym in tuple(message.text.upper()):
            for key, value in codes.items():
                if sym == value:
                    res += key + ' '
                    break

    elif text_type == 'morse':
        text = message.text.replace('   ', '<space>')
        for sym in text.split(' '):
            if sym in codes:
                res += codes[sym]
            elif sym == '<space>':
                res += ' '

    bot.send_message(message.chat.id, res)


@bot.listener('wrong_commands')
def solve(message):
    for solver in [tigeralgebra_search, wikipeida, znanija_search]:
        res = solver(message)
        if res:
            return


bot.run()
