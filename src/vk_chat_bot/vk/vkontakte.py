# -*- coding: utf-8 -*-
import vk_api
import datetime as dt
from src.vk_chat_bot.db.database import UserSearchList, session


class VKinderUser:
    def __init__(self, user_access_token):
        self.session = vk_api.VkApi(token=user_access_token)
        self.vk_api = self.session.get_api()

    def get_info(self):
        necessary_fields = ['bdate,city,sex,relation']
        user_info = self.vk_api.users.get(fields=necessary_fields)[0]
        result = {'id': user_info['id'], 'firstname': user_info['first_name'], 'lastname': user_info['last_name'],
                  'dob': user_info.get('bdate', None), 'gender': user_info['sex'],
                  'city': user_info.get('city', {}).get('id'),
                  'relation': user_info['relation']}
        return result


class SearchEngine:
    def __init__(self, user_id, user_access_token):
        self.session = vk_api.VkApi(token=user_access_token)
        self.vk_api = self.session.get_api()
        self.app_user = UserSearchList(user_id, session)

    @staticmethod
    def __em_str(value):
        if value == '':
            return None
        return value

    @staticmethod
    def __dob(value, usr_age):
        if value is not None:
            if len(value) < 8:
                return f'{value}.{dt.datetime.now().year - usr_age}'
            return value
        return value

    def search_users_n_add_to_db(self, age: int, gender: int, city: int, relation: int):
        necessary_fields = ['bdate,relation,city,sex,followers_count,can_write_private_message,interests,music,books']
        if relation == 6:
            relation_list = (relation, 1)
        elif relation == 1:
            relation_list = (relation, 6)
        else:
            relation_list = (relation, 1, 6)
        # In order to get from up to 6k to 9k
        for status in relation_list:
            # In order to get up to 3k users
            f_age = age - 1
            for _ in range(3):
                users = self.vk_api.users.search(q='', offset=0, count=1000, fields=necessary_fields,
                                                 city=city, sex=(lambda x: 2 if x == 1 else 1)(gender),
                                                 status=status, age_from=f_age, age_to=f_age, has_photo=1, v='5.89')
                for user in users['items']:
                    if user['is_closed'] is False and user['can_write_private_message'] == 1 \
                            and user['followers_count'] < 2000:
                        self.app_user.add_user(vk_id=user['id'], firstname=user['first_name'],
                                               lastname=user['last_name'], dob=self.__dob(user.get('bdate'), age),
                                               gender=user['sex'], city=user.get('city', {}).get('id'),
                                               relation=user.get('relation'), is_closed=user['is_closed'],
                                               followers=user.get('followers_count'),
                                               msg_possible=user['can_write_private_message'],
                                               interests=self.__em_str(user.get('interests')),
                                               books=self.__em_str(user.get('books')),
                                               music=self.__em_str(user.get('music')))
                f_age += 1
        return True


class VkUserCook:
    def __init__(self, user_access_token):
        self.session = vk_api.VkApi(token=user_access_token)
        self.vk_api = self.session.get_api()

    def sort_photos(self, vk_id):
        request = self.vk_api.photos.get(owner_id=vk_id, album_id='profile', extended=1)
        result = []
        if request['count'] > 3:
            for _ in range(3):
                photo = max(request['items'], key=lambda x: x['likes']['count'])
                result.append(photo)
                request['items'].remove(photo)
        else:
            result = request['items']
        # To get Max Size photo URL (just in case)
        # sizes = {'s': 1, 'm': 2, 'x': 3, 'o': 4, 'p': 5, 'q': 6, 'r': 7, 'y': 8, 'z': 9, 'w': 10}
        # for photo in result:
        #     max_size = max(photo['sizes'], key=lambda x: sizes[x.get('type')])
        #     photo['sizes'] = max_size
        #     photo['size'] = photo.pop('sizes')
        result = list(map(lambda x: f"photo{x['owner_id']}_{x['id']}", result))
        return result

    def get_user_photos(self, vk_id):
        photos = self.sort_photos(vk_id)
        return photos


if __name__ == '__main__':
    pass
