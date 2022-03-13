import requests
from flask import Flask, request
from src.vk_chat_bot.db.database import UserAppToken, session
from src.vk_chat_bot.config import SECRET_KEY_VK_APP, URL_Oauth, REDIRECT_URI, APP_ID

app = Flask(__name__)


@app.route('/vk/callback', methods=['GET'])
def index():
    if request.method == 'GET':
        code = request.args.get('code', None)
        if code is not None:
            params = {'client_id': APP_ID, 'client_secret': SECRET_KEY_VK_APP,
                      'redirect_uri': REDIRECT_URI, 'code': code}
            response = requests.get(url=URL_Oauth, params=params)
            if response.status_code == 200:
                user = response.json()
                if 'access_token' in user:
                    tmp = UserAppToken(session)
                    tmp.add_user(user['user_id'], user['access_token'])
                    return '<h2>Успешно, вернитесь к боту Vkinders и напишите еще раз start</h2>'
            elif response.status_code == 401:
                return f'{response.status_code} Client Error, Unauthorized'
            response.raise_for_status()
        return 'Error while getting code'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
