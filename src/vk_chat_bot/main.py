from vk_api.bot_longpoll import VkBotEventType
from src.vk_chat_bot.db.database import UserSearchList, session
from src.vk_chat_bot.vk.vkontakte import SearchEngine, VkUserCook
from src.vk_chat_bot.vk.manager import VKGroupManage
from src.vk_chat_bot.config import GROUP_ACCESS_TOKEN_VK, GROUP_ID, oauth_link


class VKLaunchGroup(VKGroupManage):
    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                user_id = event.obj['message']['peer_id']
                user_firstname = self._get_firstname(user_id)
                text_msg = event.obj['message']['text']
                print(f"New msg from {user_id}, text: {text_msg} ")

                if (text_msg.lower() in {'start', 'начать'}) and (not self.userapp_token.check_user(user_id)):
                    self._send_msg_sign_up(user_id, user_firstname)

                user_token = self.userapp_token.get_user_token(user_id)
                step = self.userapp_token.get_step(user_id)

                if (text_msg.lower() in {'start', 'начать'}) and (self.userapp_token.check_user(user_id)) and step == 0:
                    if self._acquaintance(user_id, user_firstname) and self._get_acquainted(user_id, user_token):
                        self.userapp_token.update_step(user_id, 1)
                if (text_msg.lower() in {'search', 'поиск'}) and (self.userapp_token.check_user(user_id)) and step == 1:
                    if self._ask_to_search(user_id, user_firstname):
                        usr_search = UserSearchList(user_id, session)
                        v_usr_cook = VkUserCook(user_token)
                        s_engine = SearchEngine(user_id, user_token)
                        while True:
                            random_id = self._generate_user(user_id, user_firstname, usr_search,
                                                            v_usr_cook, s_engine)
                            if random_id is None:
                                self._send_bye(user_id, user_firstname)
                                break
                            ask = self._ask_to_move(user_id)
                            if ask == 1:
                                usr_search.move_user_to_archive(random_id)

                            elif ask == 2:
                                usr_search.move_user_to_favourite(random_id)
                                self._send_msg(user_id, 'пользователь добавлен в избраный список ⭐️')
                                self._send_msg(user_id, 'идет следующий поиск...')

                            elif ask == 3:
                                usr_search.move_user_to_black(random_id)
                                self._send_msg(user_id, 'пользователь добавлен в черный список 🌚')
                                self._send_msg(user_id, 'идет следующий поиск...')

                            elif ask == 4:
                                usr_search.move_user_to_archive(random_id)
                                self._send_bye(user_id, user_firstname)
                                break


if __name__ == '__main__':
    test = VKLaunchGroup(GROUP_ACCESS_TOKEN_VK, GROUP_ID, oauth_link)
    test.start()
