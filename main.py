from flask import *
from flask_cors import CORS
import json
from urllib.parse import urlparse, parse_qsl, urlencode
from helpers.signature_checker import is_valid
from helpers.helpers import ids_check
from db.dbWorker import dbWorker
from helpers.vk_collector import vk_collector

application = Flask(__name__)
application.config['SECRET_KEY'] = '561a055876c04b34dcb46004bc7936c5e12893d5'
CORS(application, resources={r"/*": {"origins": "*"}})

db = dbWorker()
vk = vk_collector()


@application.errorhandler(404)
def excepterror(e):
    return json.dumps(
        {'error': 1, 'code': 1404, 'message': 'Произошла ошибка'}
    ), 400


@application.errorhandler(500)
def excepterror2(e):
    return json.dumps(
        {'error': 1, 'code': 1500, 'message': str(e)}
    ), 400


@application.errorhandler(502)
def excepterror3(e):
    return json.dumps(
        {'error': 1, 'code': 1502, 'message': 'Произошла ошибка'}
    ), 400

@application.before_request
def checksignature():
    global request_user_id
    try:
        r = request.data
        data = json.loads(r)
        client_secret = "DqNBE0LjpQNw5UCixGGn"

        params = data['params']
        url = 'https://example.com/{}'.format(params)
        query_params = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
        status = is_valid(query=query_params)
        if not status:
            return json.dumps({'error': 1, 'code': 1403, 'message': 'Подделка параметров запуска'}), 403

        request_user_id = query_params['vk_user_id']
    except Exception as err:
        return json.dumps(
            {'error': 1, 'code': 1403, 'message': 'Подделка параметров запуска! ({})'.format(err)}
        ), 403

@application.route('/get_signatures', methods=['POST'])
def request_get_signatures():
    try:
        r = request.data
        data = json.loads(r)
        canView = db.userCanView(int(request_user_id), data['user_id'])

        if 'user_id' not in data or type(data['user_id']) != int:
            return json.dumps(
                {'error': True, 'code': 400, 'message': "Bad Request"}
            ), 400

        if 'page' not in data or type(data['page']) != int or data['page'] < 0:
            data['page'] = 0

        res = []
        if canView:
            res = db.getUsersSignatures(data['user_id'], data['page'])

        return json.dumps(
                    {'error': False, 'code':200, 'page':data['page'], 'signatures':res}
                )

    except Exception as err:
        return json.dumps(
                    {'error': True, 'code':101, 'message': str(err)}
                ), 400

@application.route('/get_default', methods=['POST'])
def request_get_default():
    try:
        r = request.data
        data = json.loads(r)

        if not db.userIsWrite(int(request_user_id)):
            try:
                thisUser = vk.getByIds([int(request_user_id)])[0]
                name = f"{thisUser['first_name']} {thisUser['last_name']}"
                db.writeUser(int(request_user_id), thisUser['photo_200'], name)
            except:
                pass

        privacy = db.getUserPrivacy(int(request_user_id))

        count = db.countOfSignatures(int(request_user_id))

        return json.dumps(
            dict(
                error = False,
                code = 200,
                default = dict(
                    count=count,
                    privacy=privacy
                ),
            )
        )

    except Exception as err:
        return json.dumps(
                    {'error': True, 'code':101, 'message': str(err)}
                ), 400

@application.route('/add_text_signature', methods=['POST'])
def request_add_signatures():
    try:
        r = request.data
        data = json.loads(r)

        if ('text' not in data or type(data['text']) != str) or ('user_id') not in data or type(data['user_id']) != int or data['user_id'] < 0:
            return json.dumps(
                {'error': True, 'code': 400, 'message': "Bad Request"}
            ), 400

        canPost = db.userCanPost(int(request_user_id), data['user_id'])

        if not canPost:
            return json.dumps(
                {'error': True, 'code': 400, 'message': "Нет доступа"}
            ), 400

        # if int(request_user_id) == data['user_id']:
        #     return json.dumps(
        #         {'error': True, 'code': 400, 'message': "Нельзя добавлять подписи самому себе"}
        #     ), 400

        if len(data['text']) == 0 or len(data['text']) > 1000:
            return json.dumps(
                {'error': True, 'code': 400, 'message': "Некорректная длина подписи"}
            ), 400

        res = db.addTextSignature(data['user_id'], int(request_user_id), data['text'])

        return json.dumps(
            dict(
                error = False,
                code = 200,
                message = 'Подпись добавлена!',
                signature = dict(
                    user_id = data['user_id'],
                    from_id = int(request_user_id),
                    datetime = res,
                    text = data['text'],
                    media = ''
                )
            )
        )

    except Exception as err:
        return json.dumps(
                    {'error': True, 'code':101, 'message': str(err)}
                ), 400

@application.route('/add_media_signature', methods=['POST'])
def request_add_media_signatures():
    try:
        r = request.data
        data = json.loads(r)

        canPost = db.userCanPost(int(request_user_id), data['user_id'])

        if not canPost:
            return json.dumps(
                {'error': True, 'code': 400, 'message': "Нет доступа"}
            ), 400

        res = db.addMediaSignature(data['user_id'], int(request_user_id), data['media'])
        return json.dumps(
            dict(
                error=False,
                code=200,
                message='Подпись добавлена!',
                signature=dict(
                    user_id=data['user_id'],
                    from_id=int(request_user_id),
                    datetime=res,
                    text='',
                    media=data['media']
                )
            )
        )

    except Exception as err:
        return json.dumps(
                    {'error': True, 'code':101, 'message': str(err)}
                ), 400

@application.route('/get_profile', methods=['POST'])
def request_get_profile():
    try:
        r = request.data
        data = json.loads(r)


        if 'user_id' not in data or type(data['user_id']) != int:
            return json.dumps(
                {'error': True, 'code': 400, 'message': "Bad Request"}
            ), 400

        canView = db.userCanView(int(request_user_id), data['user_id'])
        canPost = db.userCanPost(int(request_user_id), data['user_id'])

        res = []

        if canView:
            res = db.getUsersSignatures(data['user_id'], 0)

        thisUser = db.getVKUser(data['user_id'])

        count = db.countOfSignatures(data['user_id'])

        thisUser['count'] = count

        return json.dumps(
                    {'error': False, 'code':200, 'page':0, 'privacy':dict(canView=canView,canPost=canPost), 'signatures':res, 'profile':thisUser}
                )

    except Exception as err:
        return json.dumps(
                    {'error': True, 'code':101, 'message': str(err)}
                ), 400

modes = ['all','friends','noone']

@application.route('/set_privacy', methods=['POST'])
def request_set_privacy():
    try:
        r = request.data
        data = json.loads(r)

        if 'view_mode' not in data or 'post_mode' not in data:
            return json.dumps(
                    {'error': True, 'code':400, 'message':'Bad Request'}
                ), 400

        if data['view_mode'] not in modes or data['post_mode'] not in modes:
            return json.dumps(
                {'error': True, 'code': 400, 'message': 'Bad Request'}
            ), 400

        db.updatePrivacy(data['view_mode'], data['post_mode'], int(request_user_id))

        return json.dumps(
                    {'error': False, 'code':200, 'message':'Настройки приватности изменены' })

    except Exception as err:
        return json.dumps(
                    {'error': True, 'code':101, 'message': str(err)}
                ), 400

@application.route('/edit_friends', methods=['POST'])
def request_edit_friends():
    try:
        r = request.data
        data = json.loads(r)

        if 'ids' not in data or type(data['ids']) != list:
            return json.dumps(
                {'error': True, 'code': 400, 'message': 'Неверные идентификаторы'})

        if not ids_check(data['ids']):
            return json.dumps(
                    {'error': True, 'code': 400, 'message': 'Неверные идентификаторы'})

        friends = list(set(data['ids']))

        rows = [(int(request_user_id), f) for f in friends]

        db.writeFriends(rows)


        return json.dumps(
                    {'error': False, 'code':200, 'message':'Друзья записаны' })

    except Exception as err:
        return json.dumps(
                    {'error': True, 'code':101, 'message': str(err)}
                ), 400

if __name__ == "__main__":
    application.run(host='0.0.0.0', ssl_context='adhoc')