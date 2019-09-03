import requests
import asyncio
import sys
import importlib
import inspect
from threading import Thread


class Message:
    def __init__(self, **update):
        self.text = None
        self.chat = None

        for key, value in update.items():
            if isinstance(value, dict):
                setattr(self, key, Message(**value))
            else:
                setattr(self, key, value)


class Bot:
    def __init__(self, token: str, prefix='/', loop=None, **kwargs):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.prefix = prefix

        self.offset = 0
        self.threads = []

        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.listeners = {}
        self.extension = {}
        self.commands = {}
        self.answers = {}

        self.user_settings = kwargs

    def run(self):
        self.loop.run_until_complete(self.updates_listener())

    def load_extension(self, name):
        if name in self.extension:
            return

        lib = importlib.import_module(name)

        if not hasattr(lib, 'setup'):
            del lib
            del sys.modules[name]
            raise Exception('File does not have a setup function.')

        lib.setup(self)
        self.extension[name] = lib

    def add_class(self, obj):
        members = inspect.getmembers(obj)
        for name, member in members:
            if 'command_flag' in dir(member):
                for command_name in member.command_names:
                    self.commands[command_name] = member

            elif 'listener_flag' in dir(member):
                for listener_type in member.listener_types:
                    self.listeners[listener_type] = member

    def get_updates(self, timeout=60):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': self.offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']

        if result_json:
            self.offset = result_json[-1]['update_id'] + 1
        return result_json

    async def updates_listener(self):
        while True:
            for update in self.get_updates():
                message = Message(**update['message'])
                if message.chat.id in self.answers:
                    self.answers[message.chat.id] = message
                    await asyncio.sleep(1)
                else:
                    await self.message_handler(message)

    async def message_handler(self, message, func=None, args=None):
        if message.text is None:
            return

        if message.text.startswith(self.prefix) or message.text.startswith('/') \
                or self.prefix == '':
            message.text = message.text[len(self.prefix) if not message.text.startswith('/') else 1:]
            text = message.text.split(' ', 1)
            command = text[0]

            if command in self.commands:
                func = self.commands[command]
                message.text = text[1] if len(text) > 1 else ''
                args = (message, )

            elif 'wrong_commands' in self.listeners:
                func = self.listeners['wrong_commands']
                args = (message,)

        elif 'text' in self.listeners:
            func = self.listeners['text']
            args = (message,)

        if func is not None:
            if func.access_to is not None:
                if message.chat.id not in func.access_to:
                    self.send_message(message.chat.id, 'Access denied')
                    return

            thread = Thread(target=func, args=args)
            thread.start()
            self.threads.append(thread)

    def wait_for_message(self, chat_id: int):
        self.answers[chat_id] = None

        while self.answers[chat_id] is None:
            pass

        message = self.answers[chat_id]

        del self.answers[chat_id]
        return message

    def command_handler(self, *names, access_to=None):
        def decorator(func):
            command_names = names if names != () else (func.__name__,)

            for command_name in command_names:
                self.commands[command_name] = func
            func.access_to = access_to

            return func

        return decorator

    def listener(self, *types, access_to=None):
        def decorator(func):
            listener_types = types if types != () else (func.__name__,)

            for listener_type in listener_types:
                self.listeners[listener_type] = func
            func.access_to = access_to

            return func

        return decorator

    def send_message(self, chat_id: int, text: str, send: bool = True):
        if not send:
            return

        data = {'chat_id': chat_id, 'text': text}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, data)

        if resp.json()['ok'] is False:
            print(resp.json())

        return resp.json()

    def send_photo(self, chat_id: int, photo, send: bool = True):
        if not send:
            return

        data = {'chat_id': chat_id}
        files = {'photo': photo}
        method = 'sendPhoto'
        resp = requests.post(self.api_url + method, data=data, files=files)

        if resp.json()['ok'] is False:
            print(resp.json())

        return resp.json()


def bot_command_handler(*names, access_to=None):
    def decorator(func):
        command_names = names if names != () else (func.__name__,)

        func.command_names = command_names
        func.access_to = access_to
        func.command_flag = True

        return func
    return decorator


def bot_listener(*types, access_to=None):
    def decorator(func):
        listener_types = types if types != () else (func.__name__,)

        func.listener_types = listener_types
        func.access_to = access_to
        func.lister_flag = True

        return func
    return decorator
