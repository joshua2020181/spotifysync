from django.db import models
from django.contrib.auth.models import User
from django.db.models.deletion import SET_NULL
from django.db.models.fields import CharField, IntegerField
from django.db.models.fields.related import ManyToManyField, OneToOneField
from django.utils.crypto import get_random_string
from time import time

# Create your models here.


class RoomMangaer(models.Manager):
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

    objects = RoomMangaer()

    def activate(self):  # update lastActive
        self.lastActive = int(time())

    def isActive(self):  # checks if it has been more than 24 hours since last active
        return self.lastActive < int(time()) - 864000
