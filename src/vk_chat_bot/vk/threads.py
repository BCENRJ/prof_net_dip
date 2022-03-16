from multiprocessing import Process
from src.vk_chat_bot.vk.manager import QUEUE


class AddingToDatabase(Process):
    def run(self):
        while True:
            if not QUEUE.empty():
                task = QUEUE.get()
                t = Process(target=task[0], args=task[1])
                t.start()


if __name__ == '__main__':
    listening = AddingToDatabase()
    listening.start()




