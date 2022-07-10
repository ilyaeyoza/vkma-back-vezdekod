import sqlite3 as sql
import datetime
import uuid

def getFrom(thisDict, key):
    if key not in list(thisDict.keys()):
        return dict(user_id = key, photo = 'https://sun3-12.userapi.com/s/v1/if1/G4xihi1FT7BnS-Y0mUNUoLLVXT-48Vvd0EqjZFm_hnj4_KazXUExv8vvpCxm-y-wWkMQJJNR.jpg?size=50x50&quality=96&crop=0,0,400,400&ava=1', name = 'Администрация ВКонтакте')

    return thisDict[key]

class dbWorker(object):
    def __init__(self):
        self.connection = sql.connect("./db/bases.sqlite", check_same_thread=False)
        q = self.connection.cursor()

    def getUsersSignatures(self, userid, page):
        q = self.connection.cursor()
        q.execute('SELECT * FROM signatures WHERE user_id = ? ORDER BY datetime DESC LIMIT 100 OFFSET ?', (userid, page*100))
        result = q.fetchall()
        q.execute('SELECT DISTINCT * FROM vk_users WHERE user_id IN (SELECT from_id FROM signatures WHERE user_id = ? ORDER BY datetime DESC LIMIT 100 OFFSET ?)', (userid, page*100))
        result_users = q.fetchall()
        users = [(int(i[0]), dict(user_id=i[0], photo=i[1], name=i[2])) for i in result_users]
        users = dict(users)
        return [
            dict(
                user = i[0],
                _from = getFrom(users, i[1]),
                datetime = i[2],
                text = i[3],
                media = i[4]
            )
            for i in result
        ]

    def addTextSignature(self, userid, fromid, text):
        q = self.connection.cursor()
        timeNow = int(datetime.datetime.now().timestamp())
        q.execute('INSERT INTO signatures (user_id, from_id, datetime, text, media) VALUES (?, ?, ?, ?, "")', (
            userid,
            fromid,
            timeNow,
            text
        ))

        self.connection.commit()

        return timeNow

    def addMediaSignature(self, userid, fromid, media_link):
        q = self.connection.cursor()
        timeNow = int(datetime.datetime.now().timestamp())
        q.execute('INSERT INTO signatures (user_id, from_id, datetime, text, media) VALUES (?, ?, ?, "", ?)', (
            userid,
            fromid,
            timeNow,
            media_link
        ))

        self.connection.commit()

        return timeNow

    def countOfSignatures(self, userid):
        q = self.connection.cursor()
        q.execute('SELECT COUNT(*) FROM signatures WHERE user_id = ?', (userid,))
        result = q.fetchall()
        return result[0][0]

    def userIsWrite(self, userid):
        q = self.connection.cursor()
        q.execute('SELECT * FROM vk_users WHERE user_id = ?', (userid,))
        result = q.fetchall()
        return len(result) > 0

    def writeUser(self, userid, photo, name):
        q = self.connection.cursor()
        q.execute('''INSERT INTO vk_users (user_id, photo, name) VALUES (?, ?, ?)''', (userid, photo, name))

        q.execute('''INSERT INTO privacy (user_id, view_mode, post_mode) VALUES (?, "all","all")''', (userid,))

        self.connection.commit()

    def getVKUser(self, userid):
        q = self.connection.cursor()
        q.execute('SELECT * FROM vk_users WHERE user_id = ?', (userid,))
        result = q.fetchall()
        return dict(
            user_id = result[0][0],
            photo=result[0][1],
            name=result[0][2]
        )

    def getUserPrivacy(self, userid):
        q = self.connection.cursor()
        q.execute('SELECT * FROM privacy WHERE user_id = ?', (userid,))
        result = q.fetchall()
        if len(result) == 0:
            return dict(
                user_id=userid,
                view_mode='all',
                post_mode='all',
            )

        return dict(
            user_id = result[0][0],
            view_mode = result[0][1],
            post_mode = result[0][2],
        )

    def getUsersFriends(self, userid):
        q = self.connection.cursor()
        q.execute('SELECT * FROM friends WHERE userid = ?', (userid,))
        result = q.fetchall()
        return [i[1] for i in result]

    def getUsersWithouts(self, userid):
        q = self.connection.cursor()
        q.execute('SELECT * FROM without WHERE user_id = ?', (userid,))
        result = q.fetchall()
        return [i[1] for i in result]

    def userCanView(self, userid, profileid):
        if userid == profileid:
            return True
        privacy = self.getUserPrivacy(profileid)
        vmode = privacy['view_mode']

        if vmode == 'noone':
            return False

        if vmode == 'all':
            return True

        friends = getUsersFriends(userid)

        if vmode == 'friends':
            if userid in friends:
                return True
            else:
                return False

        withouts = getUsersWithouts(userid)

        if vmode == 'friends_without':
            if userid in friends and userid not in withouts:
                return True
            else:
                return False

        if vmode == 'all_without':
            if userid not in withouts:
                return True

        return False

    def userCanPost(self, userid, profileid):
        if userid == profileid:
            return True
        privacy = self.getUserPrivacy(profileid)
        vmode = privacy['post_mode']

        if vmode == 'noone':
            return False

        if vmode == 'all':
            return True

        friends = getUsersFriends(userid)

        if vmode == 'friends':
            if userid in friends:
                return True
            else:
                return False

        withouts = getUsersWithouts(userid)

        if vmode == 'friends_without':
            if userid in friends and userid not in withouts:
                return True
            else:
                return False

        if vmode == 'all_without':
            if userid not in withouts:
                return True

        return False

    def updatePrivacy(self, view_mode, post_mode, userid):
        q = self.connection.cursor()
        q.execute('''UPDATE privacy SET view_mode = ?, post_mode = ? WHERE user_id = ?''', (view_mode, post_mode, userid))

        self.connection.commit()

    def writeFriends(self, rows):
        q = self.connection.cursor()
        q.executemany('''INSERT INTO friends (userid, friend_id) VALUES (?, ?)''', (*rows,))

        self.connection.commit()