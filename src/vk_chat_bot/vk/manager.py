import vk_api
import datetime as dt
import flag
from multiprocessing import Queue
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from src.vk_chat_bot.db.database import UserAppToken, UserSearchList, UserApp, session
from src.vk_chat_bot.vk.vkontakte import SearchEngine, VKinderUser, VkUserCook


QUEUE = Queue(100)


class VKGroupManage:
    COMMANDS = {'start', 'начать', 'search', 'свайп вправо', 'доб. в избранное', 'доб. в чс',
                'ну...давай позже 😔', 'а давай познакомимся 🐼'}

    def __init__(self, vk_group_token, group_id, oauth_link):
        self.vk = vk_api.VkApi(token=vk_group_token)
        self.long_poll = VkBotLongPoll(self.vk, group_id=group_id)
        self.vk_api = self.vk.get_api()
        self.userapp_token = UserAppToken(session)
        self.user_app = UserApp(session)
        self.oauth_link = oauth_link
        self.u_vk_api = None

    def _get_firstname(self, user_id):
        return self.vk_api.users.get(user_ids=user_id)[0]['first_name']

    def _next(self, user_id, user_token, user_firstname) -> None:
        usr_search = UserSearchList(user_id, session)
        v_usr_cook = VkUserCook(user_token)
        s_engine = SearchEngine(user_id, user_token)
        random_id = self._generate_user(user_id, user_firstname, usr_search, v_usr_cook, s_engine)
        get_id = self.userapp_token.get_last_searched_id(user_id)
        if get_id is not None:
            usr_search.move_user_to_archive(get_id)
            self.userapp_token.update_last_searched(user_id, random_id)
        else:
            self.userapp_token.update_last_searched(user_id, random_id)
        self._ask_to_move_msg(user_id)

    def _move_to_fav(self, user_id) -> None:
        usr_search = UserSearchList(user_id, session)
        get_id = self.userapp_token.get_last_searched_id(user_id)
        if user_id is not None:
            usr_search.move_user_to_favourite(get_id)
            self.userapp_token.update_last_searched(user_id, None)
        self._ask_to_move_msg(user_id)

    def _move_to_black(self, user_id) -> None:
        usr_search = UserSearchList(user_id, session)
        get_id = self.userapp_token.get_last_searched_id(user_id)
        if user_id is not None:
            usr_search.move_user_to_black(get_id)
            self.userapp_token.update_last_searched(user_id, None)
        self._ask_to_move_msg(user_id)

    # Messaging
    def _send_msg(self, peer_id, message) -> None:
        self.vk_api.messages.send(peer_id=peer_id, message=message, keyboard=None,
                                  random_id=get_random_id())

    def _resend(self, peer_id, value: str):
        message = f'Неверный формат, правильный формат: {value}'
        self.vk_api.messages.send(peer_id=peer_id, message=message, keyboard=None,
                                  random_id=get_random_id())

    def _send_msg_sign_up(self, peer_id, usr_name) -> None:
        message = f'Хаю-Хай 🐍 {usr_name}, для работы с ботом перейдите по кнопке снизу "sign up 📝" и ' \
                  f'выдайте необходимые права 🐼 после нажмите на зеленую кнопку "start" '
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_openlink_button(label='sign up 📝', link=self.oauth_link)
        keyboard.add_button('start', color=VkKeyboardColor.POSITIVE)
        self.vk_api.messages.send(peer_id=peer_id, message=message, keyboard=keyboard.get_keyboard(),
                                  random_id=get_random_id())

    def _send_msg_signed_in(self, peer_id, firstname) -> None:
        message = f'{firstname}, мы все еще не знакомы... давай познакомимся? 🐼\n' \
                  f'(нужно познакомится с пандой, чтобы перейти к поиску)'
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('а давай познакомимся 🐼', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('ну...давай позже 😔', color=VkKeyboardColor.NEGATIVE)
        self.vk_api.messages.send(peer_id=peer_id, message=message, keyboard=keyboard.get_keyboard(),
                                  random_id=get_random_id())

    def _send_bye(self, peer_id, usr_name) -> None:
        message = f'{usr_name}, гуд бай  вызвать меня сможете написав -> start или по кнопке из меню чата'
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('start', color=VkKeyboardColor.SECONDARY)
        self.vk_api.messages.send(peer_id=peer_id, message=message, keyboard=keyboard.get_keyboard(),
                                  random_id=get_random_id())

    def _unknown_command(self, peer_id, txt_msg) -> None:
        message = f"неизвестная команда '{txt_msg}' 😞\nнапишите -> start"
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('start', color=VkKeyboardColor.SECONDARY)
        self.vk_api.messages.send(peer_id=peer_id, message=message, keyboard=keyboard.get_keyboard(),
                                  random_id=get_random_id())

    def _ask_relation_msg(self, peer_id) -> None:
        message = ('Ваше семейное положение? Отправьте "/re" и цифру от 1 - 8\n\n1 - не женат/не замужем\n'
                   '2 - есть друг/есть подруга\n3 - помолвлен/помолвлена\n4 - женат/замужем\n5 - всё сложно\n'
                   '6 - в активном поиске\n7 - влюблён/влюблена\n8 - в гражданском браке\n\nпр. "/re 6"')
        self.vk_api.messages.send(peer_id=peer_id, message=message, keyboard=None,
                                  random_id=get_random_id())

    def _ask_to_move_msg(self, peer_id) -> None:
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('свайп вправо', color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('доб. в избранное', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('доб. в чс', color=VkKeyboardColor.NEGATIVE)
        self.vk_api.messages.send(peer_id=peer_id, message='✔️', keyboard=keyboard.get_keyboard(),
                                  random_id=get_random_id())

    def _get_acquaintance(self, u_token):
        user = VKinderUser(u_token).get_info()
        if user['dob'] is None or len(user['dob'].split('.')) != 3 or not 1942 <= int(user['dob'].split('.')[2]) < 2014:
            user['dob'] = None
        if user['gender'] == 0:
            user['gender'] = None
        if user['relation'] == 0:
            user['relation'] = None
        self.user_app.add_user(vk_id=user['id'], firstname=user['firstname'], lastname=user['lastname'],
                               dob=user['dob'], gender=user['gender'], city=user['city'], relation=user['relation'])
        return True

    def _check_new_usr_info(self, u_id):
        usr = self.user_app.get_user(u_id)
        usr_info = {'dob': usr.dob, 'city': usr.city, 'gender': usr.gender, 'relation': usr.relation}
        if usr_info['dob'] is None:
            self._send_msg(u_id, 'Напишите дату рождения в формате: -> /dob D.M.YYYY (от 9 до 80 лет допускается)'
                                 '\nпр. "/dob 15.7.1990" ')
            return False
        if usr_info['city'] is None:
            self._send_msg(u_id, 'Откуда вы? в формате => (RU,UA,BY,UZ) или (🇷🇺🇺🇦🇧🇾🇺🇿) и напишите город'
                                 '\nпр. "/from 🇺🇦 Киев" или "/from 🇷🇺 Москва" или "/from BY Минск"')
            return False
        if usr_info['gender'] is None:
            self._send_msg(u_id, 'Ваш пол?\n пр. "/gender 1" -> девушка, "/gender 2" -> парень')
            return False
        if usr_info['relation'] is None:
            self._ask_relation_msg(u_id)
            return False
        self._ask_to_move_msg(u_id)
        return True

    def _re_check(self, u_id, u_token):
        if self._check_new_usr_info(u_id):
            self.userapp_token.update_step(u_id, 1)
            QUEUE.put((self._search_users, (u_id, u_token)))
            return True
        return False

    def _c_dob(self, u_id, answer) -> bool:
        if '.' in answer:
            num = answer.split('.')
            if len(num) == 3:
                d, m, y = num[0], num[1], num[2]
                if d.isdigit() and m.isdigit() and y.isdigit():
                    if 1 <= int(d) <= 31 and 1 <= int(m) <= 12 and 1942 <= int(y) <= 2013:
                        self.user_app.update(u_id, answer, 'dob')
                        self._send_msg(u_id, 'я запомню вашу днюху ☺️')
                        return True
        self._send_msg(u_id, 'Дата указана неверено')
        return False

    def _c_city(self, u_id, country, city) -> bool:
        vk = vk_api.VkApi(token=self.userapp_token.get_user_token(u_id))
        self.u_vk_api = vk.get_api()
        country_flag = flag.dflagize(f"{country.strip()}", subregions=True)
        country = self.u_vk_api.database.getCountries(code=country_flag)
        country_id = country['items'][0]['id']
        if country_id != 0:
            ci = self.u_vk_api.database.getCities(country_id=country_id, q=city, count=1)['items']
            self.user_app.update(u_id, ci[0]['id'], 'city')
            self._send_msg(u_id, f'{country} {city} ☺️')
            return True
        self._send_msg(u_id, 'Страна/город указан неверено')
        return False

    def _c_gender(self, u_id, gender) -> bool:
        if gender.isdigit() and int(gender) in range(1, 3):
            self.user_app.update(u_id, int(gender), 'gender')
            return True
        self._send_msg(u_id, 'Неверный пол')
        return False

    def _c_relation(self, u_id, relation) -> bool:
        if relation.isdigit() and int(relation) in range(1, 9):
            self.user_app.update(u_id, int(relation), 'relation')
            return True
        self._send_msg(u_id, 'Семейное положение указан неверно')
        return False

    def _search_users(self, u_id, user_token):
        usr_search = UserSearchList(u_id, session)
        s_engine = SearchEngine(u_id, user_token)
        if usr_search.check_users_existence() is None:
            usr = self.user_app.get_user(u_id)
            s_engine.search_users_n_add_to_db(age=dt.datetime.now().year - usr.dob.year,
                                              gender=usr.gender, city=usr.city, relation=usr.relation)

    def _generate_user(self, u_id, name, usr_search_list, usr_cook, search_engine):
        if usr_search_list.check_users_existence() is None:
            self._send_msg(u_id, f'{name}, подходящих пользователей не найдено... вернитесь чуть позже😓')
            return None
        r_usr = usr_search_list.select_random_row()
        attach = usr_cook.get_user_photos(r_usr.vk_usr_id)
        if len(attach) != 3:
            usr_search_list.move_user_to_archive(r_usr.vk_usr_id)
            return self._generate_user(u_id, name, usr_search_list, usr_cook, search_engine)
        self._send_msg(u_id, f'{name}, успешно нашли подходящего пользователей 🐼')
        self.vk_api.messages.send(peer_id=u_id, message=f'[id{r_usr.vk_usr_id}|{r_usr.firstname} {r_usr.lastname}]',
                                  attachment=attach, random_id=get_random_id())
        return r_usr.vk_usr_id


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
                else:
                    user_exist = self.userapp_token.check_user(user_id)
                    user_token = self.userapp_token.get_user_token(user_id)
                    step = self.userapp_token.get_step(user_id)
                    start = text_msg in {'start', 'начать'}
                    next_ = text_msg in {'next', 'свайп вправо'}

                    if start and user_exist is False:
                        self._send_msg_sign_up(user_id, user_firstname)

                    elif step == 0 and user_exist:
                        if start:
                            self._send_msg_signed_in(user_id, user_firstname)
                        elif text_msg == 'ну...давай позже 😔':
                            self._send_bye(user_id, user_firstname)
                        elif text_msg == 'а давай познакомимся 🐼':
                            self._get_acquaintance(user_token)
                            self._re_check(user_id, user_token)
                        elif text_msg.split()[0] == '/dob':
                            txt_c = len(text_msg.split()) == 2
                            if txt_c:
                                self._c_dob(user_id, text_msg.split()[1])
                                self._re_check(user_id, user_token)
                            else:
                                self._resend(user_id, '/dob D.M.YYYY')
                        elif text_msg.split()[0] == '/from':
                            txt_c = len(text_msg.split()) == 3
                            if txt_c:
                                self._c_city(user_id, text_msg.split()[1], text_msg.split()[2])
                                self._re_check(user_id, user_token)
                        elif text_msg.split()[0] == '/gender':
                            txt_c = len(text_msg.split()) == 2
                            if txt_c:
                                self._c_gender(user_id, text_msg.split()[1])
                                self._re_check(user_id, user_token)
                            else:
                                self._resend(user_id, '/gender 1 или /gender 2')
                        elif text_msg.split()[0] == '/re':
                            txt_c = len(text_msg.split()) == 2
                            if txt_c:
                                self._c_relation(user_id, text_msg.split()[1])
                                self._re_check(user_id, user_token)
                            else:
                                self._resend(user_id, '/re 1-6')
                    elif step == 1 and user_exist:
                        if start:
                            self._send_msg(user_id, 'приветствую, нажмите на кнопки снизу 🐼')
                            self._ask_to_move_msg(user_id)
                        elif next_:
                            self._next(user_id, user_token, user_firstname)
                            self._ask_to_move_msg(user_id)
                        elif text_msg == 'доб. в избранное':
                            self._move_to_fav(user_id)
                            self._send_msg(user_id, 'пользователь добавлен в избраный список ⭐\n'
                                                    'идет следующий поиск...️')
                            self._next(user_id, user_token, user_firstname)
                        elif text_msg == 'доб. в чс':
                            self._move_to_black(user_id)
                            self._send_msg(user_id, 'пользователь добавлен в черный список 🌚\n'
                                                    'идет следующий поиск...')
                            self._next(user_id, user_token, user_firstname)


if __name__ == '__main__':
    pass
