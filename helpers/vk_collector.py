import vk_api

token = 'b317c050b317c050b317c050f0b36a932dbb317b317c050d1de888a6e07d007d200d9a0'

class vk_collector(object):
    def __init__(self):
        self.vk_session = vk_api.VkApi(token=token)

    def getByIds(self, ids):
        ids = [str(id) for id in ids]
        users = self.vk_session.method('users.get', dict(user_ids=','.join(ids), fields='photo_200', lang='ru'))
        return users