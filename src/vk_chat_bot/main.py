from src.vk_chat_bot.vk.manager import VKLaunchGroup
from src.vk_chat_bot.config import GROUP_ACCESS_TOKEN_VK, GROUP_ID, oauth_link


def main():
    print('VKinder Bot Launched ☺️')
    project = VKLaunchGroup(GROUP_ACCESS_TOKEN_VK, GROUP_ID, oauth_link)
    project.start()


if __name__ == '__main__':
    main()
