from django.db import models
from django.contrib.auth.models import User
from django.db.models.deletion import SET_NULL
from django.db.models.fields import CharField, IntegerField
from django.db.models.fields.related import ManyToManyField, OneToOneField
from django.utils.crypto import get_random_string
from time import time

# Create your models here.


class RoomManger(models.Manager):
    def create(self, host=None, **kwargs):
        rm = Room(id=get_random_string(
            length=16), lastActive=int(time()), host=host)
        rm.save()
        rm.allowed_users.add(host)
        rm.save()
        return rm

    def trimInactive(self):
        rooms = self.all()
        for rm in rooms:
            if not rm.isActive():
                rm.delete()


class Room(models.Model):
    id = CharField(max_length=16, primary_key=True)
    lastActive = IntegerField()
    password = CharField(max_length=50, blank=True)
    host = OneToOneField(User, null=True, on_delete=SET_NULL)
    allowed_users = ManyToManyField(User, related_name='allowed_users')

    def clearQueue(self):
        self.queue = []
        self.save()

    def addItem(self, item):
        """ adds item (dictified utils.SpotifyItem) to queue, 
        adds all nested for playlists and albums and returns list of titles that were added"""
        ls = []
        if item['type'] == 'playlist' or item['type'] == 'album':
            for i in item['nested']:
                self.queue.append(i)
                ls.append(i['name'])
        else:
            self.queue.append(item)
            ls.append(item['name'])
        self.save()
        return ', '.join(ls)

    def removeItem(self, item=None, id=None):
        """ removes the item either by the whole item or by id or does nothing if doesn't exist """
        if item:
            id = item.get('id', None)

        for i, x in enumerate(self.queue):
            if x['id'] == id:
                self.queue.pop(i)
                return
    # dictified SpotifyItem of last played track
    prevTrack = models.JSONField(default=dict)

    # a lit of dictified SpotifyItems
    queue = models.JSONField(default=list)

    def defaultSearch():
        return {'timestamp': 0,
                'seachTerm': '',
                'results': []}

    def addSearch(self, searchTerm, results):
        self.lastSearch = {'timestamp': int(time()),
                           'seachTerm': searchTerm,
                           'results': results}
        self.save()

    def getItemIfFresh(self, id):
        """ gets the item from lastSearch if last search within 10 mins """
        if self.lastSearch['timestamp'] < int(time() - 600):
            self.lastSearch = {'timestamp': 0,
                               'seachTerm': '',
                               'results': []}
            return None
        return next((item for item in self.lastSearch['results'] if item['id'] == id), None)

    lastSearch = models.JSONField(default=defaultSearch)

    objects = RoomManger()

    def activate(self):  # update lastActive
        self.lastActive = int(time())

    def isActive(self):  # checks if it has been more than 24 hours since last active
        return self.lastActive < int(time()) - 864000
