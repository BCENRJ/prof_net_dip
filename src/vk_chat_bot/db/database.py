# -*- coding: utf-8 -*-
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.ext.declarative import declarative_base
from random import randrange
from src.vk_chat_bot.config import USERNAME, PASSWORD, HOST, PORT, DB_NAME


Base = declarative_base()

# Association Tables
vkinder_to_search = sq.Table('vkinder_to_search', Base.metadata,
                             sq.Column('id', sq.Integer, primary_key=True),
                             sq.Column('vkinder_user_id', sq.ForeignKey('vkinder_users.id')),
                             sq.Column('search_list_id', sq.ForeignKey('search_list.id')),)

vkinder_to_archive = sq.Table('vkinder_to_archive', Base.metadata,
                              sq.Column('id', sq.Integer, primary_key=True),
                              sq.Column('vkinder_user_id', sq.ForeignKey('vkinder_users.id')),
                              sq.Column('archive_list_id', sq.ForeignKey('archive_list.id')),)

vkinder_to_black = sq.Table('vkinder_to_black', Base.metadata,
                            sq.Column('id', sq.Integer, primary_key=True),
                            sq.Column('vkinder_user_id', sq.ForeignKey('vkinder_users.id')),
                            sq.Column('black_list_id', sq.ForeignKey('black_list.id')),)

vkinder_to_favourite = sq.Table('vkinder_to_favourite', Base.metadata,
                                sq.Column('id', sq.Integer, primary_key=True),
                                sq.Column('vkinder_user_id', sq.ForeignKey('vkinder_users.id')),
                                sq.Column('favourite_list_id', sq.ForeignKey('favourite_list.id')),)


# Main Tables
class VKinderUserToken(Base):
    __tablename__ = 'vkinder_user_token'

    id = sq.Column('id', sq.Integer, primary_key=True)
    vk_usr_id = sq.Column('vk_usr_id', sq.BigInteger)
    access_token = sq.Column('access_token', sq.String(300))
    step = sq.Column('step', sq.Integer)
    last_searched_id = sq.Column('last_searched', sq.BigInteger, default=None)


class VKinderUsers(Base):
    __tablename__ = 'vkinder_users'

    id = sq.Column('id', sq.Integer, primary_key=True)
    vk_usr_id = sq.Column('vk_usr_id', sq.BigInteger)
    firstname = sq.Column('firstname', sq.String(90))
    lastname = sq.Column('lastname', sq.String(90))
    dob = sq.Column('dob', sq.Date)
    gender = sq.Column('gender', sq.Integer)
    city = sq.Column('city', sq.Integer)
    relation = sq.Column('relation', sq.Integer)

    search_list = relationship('SearchList', secondary=vkinder_to_search, back_populates='vkinder_users')
    archive_list = relationship('ArchiveList', secondary=vkinder_to_archive, back_populates='vkinder_users')
    black_list = relationship('BlackList', secondary=vkinder_to_black, back_populates='vkinder_users')
    favourite_list = relationship('FavouriteList', secondary=vkinder_to_favourite, back_populates='vkinder_users')


class SearchList(Base):
    __tablename__ = 'search_list'

    id = sq.Column('id', sq.Integer, primary_key=True)
    vk_usr_id = sq.Column('vk_usr_id', sq.BigInteger)
    firstname = sq.Column('firstname', sq.String(90))
    lastname = sq.Column('lastname', sq.String(90))
    dob = sq.Column('dob', sq.Date)
    gender = sq.Column('gender', sq.Integer)
    city = sq.Column('city', sq.Integer)
    relation = sq.Column('relation', sq.Integer)
    is_closed = sq.Column('is_closed', sq.Boolean)
    followers_count = sq.Column('followers_count', sq.Integer)
    msg_possible = sq.Column('can_write_private_message', sq.Integer)
    interests = sq.Column('interests', sq.Text, default=None)
    books = sq.Column('books', sq.Text, default=None)
    music = sq.Column('music', sq.Text, default=None)

    vkinder_users = relationship(VKinderUsers, secondary=vkinder_to_search, back_populates='search_list')


class ArchiveList(Base):
    __tablename__ = 'archive_list'

    id = sq.Column('id', sq.Integer, primary_key=True)
    vk_usr_id = sq.Column('vk_usr_id', sq.BigInteger)
    firstname = sq.Column('firstname', sq.String(90))
    lastname = sq.Column('lastname', sq.String(90))

    vkinder_users = relationship(VKinderUsers, secondary=vkinder_to_archive, back_populates='archive_list')


class BlackList(Base):
    __tablename__ = 'black_list'

    id = sq.Column('id', sq.Integer, primary_key=True)
    vk_usr_id = sq.Column('vk_usr_id', sq.BigInteger)
    firstname = sq.Column('firstname', sq.String(90))
    lastname = sq.Column('lastname', sq.String(90))

    vkinder_users = relationship(VKinderUsers, secondary=vkinder_to_black, back_populates='black_list')


class FavouriteList(Base):
    __tablename__ = 'favourite_list'

    id = sq.Column('id', sq.Integer, primary_key=True)
    vk_usr_id = sq.Column('vk_usr_id', sq.BigInteger)
    firstname = sq.Column('firstname', sq.String(90))
    lastname = sq.Column('lastname', sq.String(90))

    vkinder_users = relationship(VKinderUsers, secondary=vkinder_to_favourite, back_populates='favourite_list')


# Database Scripts
class DatabaseControl:
    def __init__(self, username, password, host, port, db_name) -> None:
        self.username, self.password, self.host, self.port, self.db_name = username, password, host, port, db_name

    @property
    def get_engine(self):
        url = f'postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}'
        if not database_exists(url):
            create_database(url)
        engine_ = sq.create_engine(url=url, client_encoding='utf8', pool_size=50, echo=False)
        return engine_

    @property
    def get_session(self):
        session_ = sessionmaker(autocommit=False, bind=self.get_engine)
        return session_()


class UserAppToken:
    def __init__(self, get_session) -> None:
        self.session = get_session

    def add_user(self, vk_id: int, access_token: str):
        if self.check_user(vk_id) is False:
            new_user = VKinderUserToken(vk_usr_id=vk_id, access_token=access_token, step=0)
            self.session.add(new_user)
            self.session.commit()

    def check_user(self, vk_id: int) -> bool:
        checking = self.session.query(VKinderUserToken).filter(VKinderUserToken.vk_usr_id == vk_id).first()
        if checking is None:
            return False
        return True

    def get_user_token(self, vk_id: int):
        if self.check_user(vk_id):
            user = self.session.query(VKinderUserToken).filter(VKinderUserToken.vk_usr_id == vk_id).first()
            return user.access_token
        print('Requested VKinder user does not exist.')
        return None

    def get_step(self, vk_id: int):
        if self.check_user(vk_id):
            user = self.session.query(VKinderUserToken).filter(VKinderUserToken.vk_usr_id == vk_id).first()
            return user.step
        print('Requested VKinder user does not exist.')
        return None

    def update_step(self, vk_id: int, step_n: int):
        if self.check_user(vk_id) and step_n in range(1, 2):
            self.session.query(VKinderUserToken).filter(VKinderUserToken.vk_usr_id == vk_id).update({'step': step_n})
            self.session.commit()

    def update_last_searched(self, vk_id: int, last_id: int or None):
        if self.check_user(vk_id):
            self.session.query(VKinderUserToken).filter(VKinderUserToken.vk_usr_id == vk_id).\
                update({'last_searched_id': last_id})
            self.session.commit()

    def get_last_searched_id(self, vk_id: int):
        if self.check_user(vk_id):
            user = self.session.query(VKinderUserToken).filter(VKinderUserToken.vk_usr_id == vk_id).first()
            return user.last_searched_id
        print('Requested VKinder user does not exist.')
        return None


class UserApp:
    def __init__(self, get_session) -> None:
        self.session = get_session

    def add_user(self, vk_id: int, firstname: str, lastname: str, dob:
                 str, gender: int, city: int, relation: int) -> bool:

        if self.check_user(vk_id) is False:
            new_user = VKinderUsers(vk_usr_id=vk_id, firstname=firstname, lastname=lastname, dob=dob,
                                    gender=gender, city=city, relation=relation)
            self.session.add(new_user)
            self.session.commit()
        return True

    def check_user(self, vk_id: int) -> bool:
        checking = self.session.query(VKinderUsers).filter(VKinderUsers.vk_usr_id == vk_id).first()
        if checking is None:
            return False
        return True

    def get_user(self, vk_id: int):
        if self.check_user(vk_id):
            return self.session.query(VKinderUsers).filter(VKinderUsers.vk_usr_id == vk_id).first()
        print('Requested VKinder user does not exist.')
        return None


class UserSearchList:
    def __init__(self, app_user_vk_id: int, get_session) -> None:
        self.session = get_session
        app_user = self.session.query(VKinderUsers).filter(VKinderUsers.vk_usr_id == app_user_vk_id).first()
        if app_user is None:
            raise Exception(f'AppUser VK ID: "{app_user_vk_id}" does not exist.')
        self.app_user = app_user
        self.app_user_id = app_user_vk_id

    def __check_user(self, vk_id: int) -> bool:
        check_rep = (sq.select(VKinderUsers.vk_usr_id).join(vkinder_to_search).join(SearchList).
                     where(VKinderUsers.vk_usr_id == self.app_user_id).where(SearchList.vk_usr_id == vk_id))
        check_result = self.session.execute(check_rep)
        if tuple(check_result) == ():
            return True
        return False

    def __check_blacked_or_archived(self, vk_id) -> bool:
        black = self.session.query(BlackList).join(vkinder_to_black).join(VKinderUsers). \
            where(VKinderUsers.vk_usr_id == self.app_user_id).where(BlackList.vk_usr_id == vk_id).first()
        archived = self.session.query(ArchiveList).join(vkinder_to_archive).join(VKinderUsers). \
            where(VKinderUsers.vk_usr_id == self.app_user_id).where(ArchiveList.vk_usr_id == vk_id).first()
        if black is not None or archived is not None:
            return False
        return True

    def check_users_existence(self):
        q = self.session.query(SearchList).join(vkinder_to_search).join(VKinderUsers). \
            where(VKinderUsers.vk_usr_id == self.app_user_id).count()
        if q == 0:
            return None
        return q

    def add_user(self, vk_id: int, firstname: str, lastname: str, dob: str, gender: int,  city: int, relation: int,
                 is_closed: bool, followers: int, msg_possible: int, interests=None, books=None, music=None) -> bool:

        if self.__check_user(vk_id) and self.__check_blacked_or_archived(vk_id):
            new_user = SearchList(vk_usr_id=vk_id, firstname=firstname, lastname=lastname, dob=dob, gender=gender,
                                  city=city, relation=relation, is_closed=is_closed, followers_count=followers,
                                  msg_possible=msg_possible, interests=interests, books=books, music=music)

            self.app_user.search_list.append(new_user)
            self.session.add(self.app_user)
            self.session.commit()
            return True
        return False

    def get_all_users(self):
        request = (sq.select(SearchList).join(vkinder_to_search).join(VKinderUsers).
                   where(VKinderUsers.vk_usr_id == self.app_user_id))
        request_result = self.session.execute(request)
        return request_result

    def select_random_row(self):
        query = self.check_users_existence()
        if query is not None:
            row_n = randrange(0, query)
            row = self.session.query(SearchList).join(vkinder_to_search).\
                join(VKinderUsers).where(VKinderUsers.vk_usr_id == self.app_user_id)[row_n]
            return row
        return None

    def remove_user(self, vk_id) -> bool:
        request = self.session.query(SearchList).filter(SearchList.vk_usr_id == vk_id).first()
        if request is not None:
            check = sq.select(SearchList.id).join(vkinder_to_search).join(VKinderUsers).\
                where(VKinderUsers.vk_usr_id == self.app_user_id).where(SearchList.vk_usr_id == vk_id)
            check_result = self.session.execute(check)
            id_ = tuple(check_result)
            if id_ != ():
                defined = self.session.query(SearchList).filter(SearchList.id == id_[0][0]).one()
                self.session.delete(defined)
                self.session.commit()
            else:
                print(f'App User (id: {self.app_user_id}) does not have permission to delete {vk_id}.')
                return False
            return True
        print(f'VK user ID: {vk_id} does not exist.')
        return False

    def move_user_to_archive(self, vk_id: int):
        request = (sq.select(SearchList).join(vkinder_to_search).join(VKinderUsers).
                   where(VKinderUsers.vk_usr_id == self.app_user_id).where(SearchList.vk_usr_id == vk_id))
        request_result = self.session.execute(request).fetchone()
        if request_result is not None:
            for row in request_result:
                temp = UserArchiveList(self.app_user_id, self.session)
                if temp.add_user(row.vk_usr_id, row.firstname, row.lastname):
                    self.remove_user(row.vk_usr_id)
                    return True
        else:
            print('User not found.')
            return None

    def move_user_to_black(self, vk_id: int):
        request = (sq.select(SearchList).join(vkinder_to_search).join(VKinderUsers).
                   where(VKinderUsers.vk_usr_id == self.app_user_id).where(SearchList.vk_usr_id == vk_id))
        request_result = self.session.execute(request).fetchone()
        if request_result is not None:
            for row in request_result:
                temp = UserBlackList(self.app_user_id, self.session)
                if temp.add_user(row.vk_usr_id, row.firstname, row.lastname):
                    self.remove_user(row.vk_usr_id)
                    return True
        else:
            print('User not found.')
            return None

    def move_user_to_favourite(self, vk_id: int):
        request = (sq.select(SearchList).join(vkinder_to_search).join(VKinderUsers).
                   where(VKinderUsers.vk_usr_id == self.app_user_id).where(SearchList.vk_usr_id == vk_id))
        request_result = self.session.execute(request).fetchone()
        if request_result is not None:
            for row in request_result:
                temp = UserFavouriteList(self.app_user_id, self.session)
                if temp.add_user(row.vk_usr_id, row.firstname, row.lastname):
                    self.remove_user(row.vk_usr_id)
                    return True
        else:
            print('User not found.')
            return None


class UserArchiveList:
    def __init__(self, app_user_vk_id: int, get_session) -> None:
        self.session = get_session
        app_user = self.session.query(VKinderUsers).filter(VKinderUsers.vk_usr_id == app_user_vk_id).first()
        if app_user is None:
            raise Exception(f'AppUser VK ID: "{app_user_vk_id}" does not exist.')
        self.app_user = app_user
        self.app_user_id = app_user_vk_id

    def add_user(self, vk_id: int, firstname: str, lastname: str) -> bool:
        if self.__check_user(vk_id):
            new_user = ArchiveList(vk_usr_id=vk_id, firstname=firstname, lastname=lastname)
            self.app_user.archive_list.append(new_user)
            self.session.add(self.app_user)
            self.session.commit()
            return True
        return False

    def __check_user(self, vk_id: int) -> bool:
        checking = (sq.select(VKinderUsers.vk_usr_id).join(vkinder_to_archive).join(ArchiveList).
                    where(VKinderUsers.vk_usr_id == self.app_user_id).where(ArchiveList.vk_usr_id == vk_id))
        check_result = self.session.execute(checking)
        if tuple(check_result) == ():
            return True
        return False

    def get_all_users(self):
        request = (sq.select(ArchiveList).join(vkinder_to_archive).join(VKinderUsers).
                   where(VKinderUsers.vk_usr_id == self.app_user_id))
        request_result = self.session.execute(request)
        return request_result

    def remove_user(self, vk_id) -> bool:
        request = self.session.query(ArchiveList).filter(ArchiveList.vk_usr_id == vk_id).first()
        if request is not None:
            check = sq.select(ArchiveList.id).join(vkinder_to_archive).join(VKinderUsers).\
                where(VKinderUsers.vk_usr_id == self.app_user_id).where(ArchiveList.vk_usr_id == vk_id)
            check_result = self.session.execute(check)
            id_ = tuple(check_result)
            if id_ != ():
                defined = self.session.query(ArchiveList).filter(ArchiveList.id == id_[0][0]).one()
                self.session.delete(defined)
                self.session.commit()
            else:
                print(f'App User (id: {self.app_user_id}) does not have permission to delete {vk_id}.')
                return False
            return True
        print(f'VK user ID: {vk_id} does not exist.')
        return False


class UserFavouriteList:
    def __init__(self, app_user_vk_id: int, get_session) -> None:
        self.session = get_session
        app_user = self.session.query(VKinderUsers).filter(VKinderUsers.vk_usr_id == app_user_vk_id).first()
        if app_user is None:
            raise Exception(f'AppUser VK ID: "{app_user_vk_id}" does not exist.')
        self.app_user = app_user
        self.app_user_id = app_user_vk_id

    def add_user(self, vk_id: int, firstname: str, lastname: str) -> bool:
        if self.__check_user(vk_id):
            new_user = FavouriteList(vk_usr_id=vk_id, firstname=firstname, lastname=lastname)
            self.app_user.favourite_list.append(new_user)
            self.session.add(self.app_user)
            self.session.commit()
            return True
        return False

    def __check_user(self, vk_id: int) -> bool:
        checking = (sq.select(VKinderUsers.vk_usr_id).join(vkinder_to_favourite).join(FavouriteList).
                    where(VKinderUsers.vk_usr_id == self.app_user_id).where(FavouriteList.vk_usr_id == vk_id))
        check_result = self.session.execute(checking)
        if tuple(check_result) == ():
            return True
        return False

    def get_all_users(self):
        request = (sq.select(FavouriteList).join(vkinder_to_favourite).join(VKinderUsers).
                   where(VKinderUsers.vk_usr_id == self.app_user_id))
        request_result = self.session.execute(request)
        return request_result

    def remove_user(self, vk_id) -> bool:
        request = self.session.query(FavouriteList).filter(FavouriteList.vk_usr_id == vk_id).first()
        if request is not None:
            check = sq.select(FavouriteList.id).join(vkinder_to_favourite).join(VKinderUsers).\
                where(VKinderUsers.vk_usr_id == self.app_user_id).where(FavouriteList.vk_usr_id == vk_id)
            check_result = self.session.execute(check)
            id_ = tuple(check_result)
            if id_ != ():
                defined = self.session.query(FavouriteList).filter(FavouriteList.id == id_[0][0]).one()
                self.session.delete(defined)
                self.session.commit()
            else:
                print(f'App User (id: {self.app_user_id}) does not have permission to delete {vk_id}.')
                return False
            return True
        print(f'VK user ID: {vk_id} does not exist.')
        return False


class UserBlackList:
    def __init__(self, app_user_vk_id: int, get_session) -> None:
        self.session = get_session
        app_user = self.session.query(VKinderUsers).filter(VKinderUsers.vk_usr_id == app_user_vk_id).first()
        if app_user is None:
            raise Exception(f'AppUser VK ID: "{app_user_vk_id}" does not exist.')
        self.app_user = app_user
        self.app_user_id = app_user_vk_id

    def add_user(self, vk_id: int, firstname: str, lastname: str) -> bool:
        if self.__check_user(vk_id):
            new_user = BlackList(vk_usr_id=vk_id, firstname=firstname, lastname=lastname)
            self.app_user.black_list.append(new_user)
            self.session.add(self.app_user)
            self.session.commit()
            return True
        return False

    def __check_user(self, vk_id: int) -> bool:
        checking = (sq.select(VKinderUsers.vk_usr_id).join(vkinder_to_black).join(BlackList).
                    where(VKinderUsers.vk_usr_id == self.app_user_id).where(BlackList.vk_usr_id == vk_id))
        check_result = self.session.execute(checking)
        if tuple(check_result) == ():
            return True
        return False

    def get_all_users(self):
        request = (sq.select(BlackList).join(vkinder_to_black).join(VKinderUsers).
                   where(VKinderUsers.vk_usr_id == self.app_user_id))
        request_result = self.session.execute(request)
        return request_result

    def remove_user(self, vk_id) -> bool:
        request = self.session.query(BlackList).filter(BlackList.vk_usr_id == vk_id).first()
        if request is not None:
            check = sq.select(BlackList.id).join(vkinder_to_black).join(VKinderUsers).\
                where(VKinderUsers.vk_usr_id == self.app_user_id).where(BlackList.vk_usr_id == vk_id)
            check_result = self.session.execute(check)
            id_ = tuple(check_result)
            if id_ != ():
                defined = self.session.query(BlackList).filter(BlackList.id == id_[0][0]).one()
                self.session.delete(defined)
                self.session.commit()
            else:
                print(f'App User (id: {self.app_user_id}) does not have permission to delete {vk_id}.')
                return False
            return True
        print(f'VK user ID: {vk_id} does not exist.')
        return False


dc = DatabaseControl(USERNAME, PASSWORD, HOST, PORT, DB_NAME)
session = dc.get_session


if __name__ == '__main__':
    Base.metadata.create_all(dc.get_engine)
    # Base.metadata.drop_all(dc.get_engine)
    pass
