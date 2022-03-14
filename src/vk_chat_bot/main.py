from vk_api.bot_longpoll import VkBotEventType
from src.vk_chat_bot.vk.manager import VKGroupManage
from src.vk_chat_bot.config import GROUP_ACCESS_TOKEN_VK, GROUP_ID, oauth_link


class VKLaunchGroup(VKGroupManage):
    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                user_id = event.obj['message']['peer_id']
                user_firstname = self._get_firstname(user_id)
                text_msg = event.obj['message']['text'].strip()
                print(f"New msg from {user_id}, text: {text_msg} ")

                if text_msg.lower() not in VKLaunchGroup.COMMANDS:
                    self._unknown_command(user_id, text_msg)

                user_exist = self.userapp_token.check_user(user_id)
                user_token = self.userapp_token.get_user_token(user_id)
                step = self.userapp_token.get_step(user_id)
                start = text_msg.lower() in {'start', 'начать'}
                search = text_msg.lower() in {'search', 'поиск'}
                next_ = text_msg.lower() in {'next', 'следующий'}
                favourite = text_msg.lower() in {'доб. в избранное'}
                black = text_msg.lower() in {'доб. в чс'}

                if start and user_exist is False:
                    self._send_msg_sign_up(user_id, user_firstname)

                if start and user_exist and step == 0:
                    if self._acquaintance(user_id, user_firstname) and self._get_acquainted(user_id, user_token):
                        self.userapp_token.update_step(user_id, 1)

                if start and user_exist and step == 1:
                    self._send_msg(user_id, 'напишите -> "поиск" или "search" для поиска пользователей')

                if (search or next_) and user_exist and step == 1:
                    self._search_or_next(user_id, user_token, user_firstname)

                if favourite and user_exist and step == 1:
                    self._move_to_fav(user_id)
                    self._send_msg(user_id, 'пользователь добавлен в избраный список ⭐\nидет следующий поиск...️')
                    self._search_or_next(user_id, user_token, user_firstname)

                if black and user_exist and step == 1:
                    self._move_to_black(user_id)
                    self._send_msg(user_id, 'пользователь добавлен в черный список 🌚\nидет следующий поиск...')
                    self._send_msg(user_id, 'идет следующий поиск...')
                    self._search_or_next(user_id, user_token, user_firstname)


if __name__ == '__main__':
    test = VKLaunchGroup(GROUP_ACCESS_TOKEN_VK, GROUP_ID, oauth_link)
    test.start()
