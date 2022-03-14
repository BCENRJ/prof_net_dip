from vk_api.bot_longpoll import VkBotEventType
from src.vk_chat_bot.vk.manager import VKGroupManage
from src.vk_chat_bot.config import GROUP_ACCESS_TOKEN_VK, GROUP_ID, oauth_link


class VKLaunchGroup(VKGroupManage):
    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                user_id = event.obj['message']['peer_id']
                user_firstname = self._get_firstname(user_id)
                text_msg = event.obj['message']['text'].strip().lower()
                print(f"New msg from {user_id}, text: {text_msg} ")

                if text_msg not in VKLaunchGroup.COMMANDS and \
                        text_msg.split()[0] not in {'/dob', '/from', '/gender', '/re'}:
                    self._unknown_command(user_id, text_msg)

                user_exist = self.userapp_token.check_user(user_id)
                user_token = self.userapp_token.get_user_token(user_id)
                step = self.userapp_token.get_step(user_id)
                start = text_msg in {'start', 'начать'}
                search = text_msg in {'search', 'поиск'}
                next_ = text_msg in {'next', 'следующий'}

                if start and user_exist is False:
                    self._send_msg_sign_up(user_id, user_firstname)

                if start and user_exist and step == 0:
                    self._send_msg_signed_in(user_id, user_firstname)

                if text_msg == 'ну...давай позже 😔' and user_exist and step == 0:
                    self._send_bye(user_id, user_firstname)
                if text_msg == 'а давай познакомимся 🐼' and user_exist and step == 0:
                    self._get_acquaintance(user_token)
                    self._re_check(user_id)
                if text_msg.split()[0] == '/dob' and user_exist and step == 0:
                    txt_c = len(text_msg.split()) == 2
                    if txt_c:
                        self._c_dob(user_id, text_msg.split()[1])
                        self._re_check(user_id)
                if text_msg.split()[0] == '/from' and user_exist and step == 0:
                    txt_c = len(text_msg.split()) == 3
                    if txt_c:
                        self._c_city(user_id, text_msg.split()[1], text_msg.split()[2])
                        self._re_check(user_id)
                if text_msg.split()[0] == '/gender' and user_exist and step == 0:
                    txt_c = len(text_msg.split()) == 2
                    if txt_c:
                        self._c_gender(user_id, text_msg.split()[1])
                        self._re_check(user_id)
                if text_msg.split()[0] == '/re' and user_exist and step == 0:
                    txt_c = len(text_msg.split()) == 2
                    if txt_c:
                        self._c_relation(user_id, text_msg.split()[1])
                        self._re_check(user_id)

                if start and user_exist and step == 1:
                    self._send_msg(user_id, 'приветствую, нажмите на кнопки снизу 🐼')
                    self._ask_to_move_msg(user_id)

                if (search or next_) and user_exist and step == 1:
                    self._search_or_next(user_id, user_token, user_firstname)
                    self._ask_to_move_msg(user_id)

                if text_msg in {'доб. в избранное'} and user_exist and step == 1:
                    self._move_to_fav(user_id)
                    self._send_msg(user_id, 'пользователь добавлен в избраный список ⭐\nидет следующий поиск...️')
                    self._search_or_next(user_id, user_token, user_firstname)

                if text_msg in {'доб. в чс'} and user_exist and step == 1:
                    self._move_to_black(user_id)
                    self._send_msg(user_id, 'пользователь добавлен в черный список 🌚\nидет следующий поиск...')
                    self._search_or_next(user_id, user_token, user_firstname)


if __name__ == '__main__':
    test = VKLaunchGroup(GROUP_ACCESS_TOKEN_VK, GROUP_ID, oauth_link)
    test.start()
