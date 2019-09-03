import asyncio
from os import environ
from googletrans import Translator

from telebotapi.telebotapi import Bot
from solvemyproblem.znanija import AsyncZnanija
from solvemyproblem.tigeralgebra import AsyncTigerAlgebra
from solvemyproblem.wikipedia import Wikipedia

bot = Bot(environ('token'), prefix='')


@bot.command_handler('start')
def start_message(message):
    text = 'Привет! Для поиска решения задач просто напишите их условие боту. Например: "2x+2=0"'
    bot.send_message(message.chat.id, text)


@bot.command_handler()
def test(message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot.send_message(message.chat.id, 'test')
    message = bot.wait_for_message(message.chat.id)

    bot.send_message(message.chat.id, 'done ' + message.text)


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

    sym_pass = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    for sym in tuple(sym_pass):
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


@bot.command_handler('с', 'сalc', 'к', access_to=[971379586])
def calc(message):
    if message.text.replace(' ', '') == '':
        bot.send_message(message.chat.id, 'Напишите пример')
        message = bot.wait_for_message(message.chat.id)

    sym_pass = ['0', '1', '2', '3', '4', '5',
                '6', '7', '8', '9', '+', '-',
                '*', '/', '%', '(', ')', '.', ' ']
    for sym in tuple(message.text):
        if sym not in sym_pass:
            return False

    try:
        answer = eval(message.text)
        bot.send_message(message.chat.id, answer)
    except:
        return False
    return True


@bot.command_handler('tr', 'translate', 'тр', 'перевод')
def translate(message):
    if message.text.replace(' ', '') == '':
        bot.send_message(message.chat.id, 'Напишите на какой язык перевести, пример: "en"')
        message = bot.wait_for_message(message.chat.id)
        dest = message.text

        bot.send_message(message.chat.id, 'Напишите текст')
        message = bot.wait_for_message(message.chat.id)
        text = message.text

    else:
        dest, text = tuple(message.text.split(' ', 1))

    translator = Translator()
    src = translator.detect(text).lang

    try:
        translation = translator.translate(text, src=src, dest=dest)
        bot.send_message(message.chat.id, f'[{src.upper()} > {dest.upper()}]\n{translation.text}')
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
    bot.send_message(message.chat.id, 'Выберете какие секции через запятую:\n' + text)
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


@bot.listener('wrong_commands')
def solve(message):
    for solver in [calc, tigeralgebra_search, wikipeida, znanija_search]:
        res = solver(message)
        if res:
            return


bot.run()
