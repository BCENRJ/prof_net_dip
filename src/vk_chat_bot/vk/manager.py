import vk_api
import datetime as dt
import flag
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from src.vk_chat_bot.db.database import UserAppToken, UserApp, session
from src.vk_chat_bot.vk.vkontakte import VKinderUser


class VKGroupManage:
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

    # Messaging
    def _send_msg(self, peer_id, message) -> None:
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

    def _send_msg_signed_in(self, peer_id, message) -> None:
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('а давай познакомимся 🐼 ', color=VkKeyboardColor.POSITIVE)
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

    def _ask_gender_msg(self, peer_id, message) -> None:
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('девушка', color=VkKeyboardColor.SECONDARY)
        keyboard.add_button('парень', color=VkKeyboardColor.SECONDARY)
        self.vk_api.messages.send(peer_id=peer_id, message=message, keyboard=keyboard.get_keyboard(),
                                  random_id=get_random_id())

    def _ask_relation_msg(self, peer_id):
        message = ('Ваше семейное положение? Отправьте цифру от 1 - 8\n\n1 - не женат/не замужем\n'
                   '2 - есть друг/есть подруга\n3 - помолвлен/помолвлена\n4 - женат/замужем\n5 - всё сложно\n'
                   '6 - в активном поиске\n7 - влюблён/влюблена\n8 - в гражданском браке')

        self.vk_api.messages.send(peer_id=peer_id, message=message, keyboard=None,
                                  random_id=get_random_id())

    def _ask_to_search_msg(self, peer_id, message) -> None:
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('да', color=VkKeyboardColor.SECONDARY)
        keyboard.add_button('нет', color=VkKeyboardColor.SECONDARY)
        self.vk_api.messages.send(peer_id=peer_id, message=message, keyboard=keyboard.get_keyboard(),
                                  random_id=get_random_id())

    def _ask_to_move_msg(self, peer_id, message) -> None:
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('следующий', color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('доб. в избранное', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('доб. в чс', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('выход', color=VkKeyboardColor.SECONDARY)
        self.vk_api.messages.send(peer_id=peer_id, message=message, keyboard=keyboard.get_keyboard(),
                                  random_id=get_random_id())

    def _acquaintance(self, u_id, firstname):
        self._send_msg_signed_in(u_id, f'{firstname}, мы все еще не знакомы... давай познакомимся? 🐼\n'
                                       f'(нужно познакомится с пандой, чтобы перейти к поиску)')
        for further_event in self.long_poll.listen():
            if further_event.type == VkBotEventType.MESSAGE_NEW:
                if u_id == further_event.obj['message']['peer_id']:
                    answer = further_event.obj['message']['text']
                    if answer == 'ну...давай позже 😔':
                        self._send_bye(u_id, firstname)
                        return False
                    elif answer == 'а давай познакомимся 🐼':
                        return True
                    else:
                        self._send_msg(u_id, 'Не очень вас понимаю...')
                        return self._acquaintance(u_id, firstname)

    def _get_acquainted(self, u_id, u_token):
        user = VKinderUser(u_token).get_info()
        if user['dob'] is None or len(user['dob'].split('.')) != 3 or not 1942 <= int(user['dob'].split('.')[2]) < 2014:
            user['dob'] = self._ask_dob(u_id)
        if user['city'] is None:
            user['city'] = self._ask_city(u_id)
        if user['gender'] == 0:
            user['gender'] = self._ask_gender(u_id)
        if user['relation'] == 0:
            user['relation'] = self._ask_relation(u_id)
        self.user_app.add_user(vk_id=user['id'], firstname=user['firstname'], lastname=user['lastname'],
                               dob=user['dob'], gender=user['gender'], city=user['city'], relation=user['relation'])
        return True

    def _ask_dob(self, u_id):
        self._send_msg(u_id, 'Напиште дату рождения в формате: -> D.M.YYYY (от 9 до 80 лет допускается) ')
        for further_event in self.long_poll.listen():
            if further_event.type == VkBotEventType.MESSAGE_NEW:
                if u_id == further_event.obj['message']['peer_id']:
                    answer = further_event.obj['message']['text'].strip()
                    if '.' in answer:
                        num = answer.split('.')
                        if len(num) == 3:
                            d, m, y = num[0], num[1], num[2]
                            if d.isdigit() and m.isdigit() and y.isdigit():
                                if 1 <= int(d) <= 31 and 1 <= int(m) <= 12 and 1942 <= int(y) <= 2013:
                                    return answer
                    self._send_msg(u_id, 'Дата указана неверено')
                    return self._ask_dob(u_id)

    def _get_city_id(self, u_id, c_id):
        self._send_msg(u_id, 'а из какого вы города?\nесли страна выбрана неверено то отправьте => "q" в ответ')
        for further_event in self.long_poll.listen():
            if further_event.type == VkBotEventType.MESSAGE_NEW:
                if u_id == further_event.obj['message']['peer_id']:
                    answer = further_event.obj['message']['text']
                    if answer.lower() == 'q':
                        self._ask_city(u_id)
                    data = self.u_vk_api.database.getCities(country_id=c_id, q=answer, count=3)['items']
                    for n, elem in enumerate(data):
                        self._send_msg(u_id, f"№ {n + 1}: город: {elem['title']}\n"
                                             f"{elem.get('area', '')} {elem.get('region', '')}")
                    n = self._city_c(u_id)
                    return data[n-1]['id']

    def _city_c(self, u_id):
        self._send_msg(u_id, 'Выберите подходящий № города из списка и отправьте \n№ от 1 - 3')
        for further_event in self.long_poll.listen():
            if further_event.type == VkBotEventType.MESSAGE_NEW:
                if u_id == further_event.obj['message']['peer_id']:
                    answer = further_event.obj['message']['text']
                    if answer.isdigit() and int(answer) in range(1, 4):
                        return int(answer)
                    self._send_msg(u_id, 'Неверно')
                    return self._city_c(u_id)

    def _ask_city(self, u_id):
        self._send_msg(u_id, 'Откуда вы? (из какой страны) в формате => RU,UA,BY,UZ или '
                             'можете скинуть флаг страны =>  🇷🇺🇺🇦🇧🇾🇺🇿')
        vk = vk_api.VkApi(token=self.userapp_token.get_user_token(u_id))
        self.u_vk_api = vk.get_api()
        for further_event in self.long_poll.listen():
            if further_event.type == VkBotEventType.MESSAGE_NEW:
                if u_id == further_event.obj['message']['peer_id']:
                    answer = further_event.obj['message']['text']
                    c_flag = flag.dflagize(f"{answer.strip()}", subregions=True)
                    country = self.u_vk_api.database.getCountries(code=c_flag)
                    c_id = country['items'][0]['id']
                    if c_id != 0:
                        self._send_msg(u_id, f"{country['items'][0]['title']} 👍")
                        return self._get_city_id(u_id, c_id)
                    self._send_msg(u_id, 'Вы указали неверный формат')
                    return self._ask_city(u_id)

    def _ask_gender(self, u_id):
        self._ask_gender_msg(u_id, 'Укажите ваш пол?')
        for further_event in self.long_poll.listen():
            if further_event.type == VkBotEventType.MESSAGE_NEW:
                if u_id == further_event.obj['message']['peer_id']:
                    answer = further_event.obj['message']['text']
                    if answer.lower() == 'девушка':
                        return 1
                    elif answer.lower() == 'парень':
                        return 2
                    self._send_msg(u_id, 'Неверный пол (девушка / парень)')
                    return self._ask_gender(u_id)

    def _ask_relation(self, u_id):
        self._ask_relation_msg(u_id)
        for further_event in self.long_poll.listen():
            if further_event.type == VkBotEventType.MESSAGE_NEW:
                if u_id == further_event.obj['message']['peer_id']:
                    answer = further_event.obj['message']['text']
                    if answer.isdigit() and int(answer) in range(1, 9):
                        return int(answer)
                    self._send_msg(u_id, 'Семейное положение указан неверно')
                    return self._ask_relation(u_id)

    def _ask_to_search(self, u_id, usr_name):
        self._ask_to_search_msg(u_id, f'{usr_name}, 🐼 перейдем к поиску?')
        for further_event in self.long_poll.listen():
            if further_event.type == VkBotEventType.MESSAGE_NEW:
                if u_id == further_event.obj['message']['peer_id']:
                    answer = further_event.obj['message']['text']
                    if answer.lower() == 'да':
                        self._send_msg(u_id, 'Идет поиск...')
                        return True
                    elif answer.lower() == 'нет':
                        self._send_bye(u_id, usr_name)
                        return False
                    self._send_msg(u_id, 'Неверная команда')
                    return self._ask_to_search(u_id, usr_name)

    def _ask_to_move(self, u_id):
        self._ask_to_move_msg(u_id, '🐼🥰')
        for further_event in self.long_poll.listen():
            if further_event.type == VkBotEventType.MESSAGE_NEW:
                if u_id == further_event.obj['message']['peer_id']:
                    answer = further_event.obj['message']['text']
                    if answer.lower() == 'следующий':
                        return 1
                    elif answer.lower() == 'доб. в избранное':
                        return 2
                    elif answer.lower() == 'доб. в чс':
                        return 3
                    elif answer.lower() == 'выход':
                        return 4
                    self._send_msg(u_id, 'Неверная команда')
                    return self._ask_to_move(u_id)

    def _generate_user(self, u_id, name, usr_search_list, usr_cook, search_engine):
        if usr_search_list.check_users_existence() is None:
            self._send_msg(u_id, f'{name}, ищем потенциально '
                                 f'подходящих пользователей для знакомств...')
            usr = self.user_app.get_user(u_id)
            search_engine.search_users_n_add_to_db(age=dt.datetime.now().year - usr.dob.year,
                                                   gender=usr.gender, city=usr.city, relation=usr.relation)
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


if __name__ == '__main__':
    pass
