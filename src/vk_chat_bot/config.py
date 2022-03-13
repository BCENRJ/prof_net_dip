# Server
SECRET_KEY_VK_APP = ''
URL_Oauth = ''
REDIRECT_URI = ''
APP_ID = 0000

# Database Connect (First Go to the db/database and create db ex. "Base.metadata.create_all(dc.get_engine)")
USERNAME = ''
PASSWORD = ''
HOST = ''
PORT = ''
DB_NAME = ''

# VK Group
GROUP_ACCESS_TOKEN_VK = ''
GROUP_ID = ''
oauth_link = f'https://oauth.vk.com/authorize?client_id={APP_ID}&display=page&redirect_uri={REDIRECT_URI}' \
             f'&scope=offline&response_type=code&v=5.131'
