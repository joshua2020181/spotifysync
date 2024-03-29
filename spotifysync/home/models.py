from django.db import models
from django.contrib.auth.models import User
from django.db.models.deletion import SET_NULL
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
from spotifysync.settings import SCOPE, CLIENTID, CLIENTSECRET, REDIRECTURI
from time import time


class SpotifyUserManager(models.Manager):
    def create_spotifyuser(self, user, **kwargs):
        spusr = self.create(user=user)
        return spusr


class SpotifyUser(models.Model):
    user = models.OneToOneField(
        User, primary_key=True, on_delete=models.RESTRICT)
    access_token = models.CharField(blank=True, max_length=255)
    token_type = models.CharField(blank=True, max_length=255)
    expires_in = models.SmallIntegerField(null=True)
    refresh_token = models.CharField(blank=True, max_length=255)
    scope = models.CharField(blank=True, max_length=255)
    expires_at = models.IntegerField(null=True)

    room = models.ForeignKey('room.Room', on_delete=SET_NULL, null=True)

    def getCachePath(self):
        return f'/home/caches/{self.user.username}'

    def getTokenInfo(self):
        return {'access_token': self.access_token,
                'token_type': self.token_type,
                'expires_in': self.expires_in,
                'refresh_token': self.refresh_token,
                'scope': self.scope,
                'expires_at': self.expires_at}

    def deleteCache(self):
        self.access_token = ''
        self.token_type = ''
        self.expires_in = None
        self.refresh_token = ''
        self.scope = ''
        self.expires_at = None
        self.save()

    def saveCache(self, token_info):
        self.access_token = token_info['access_token']
        self.token_type = token_info['token_type']
        self.expires_in = token_info['expires_in']
        self.refresh_token = token_info['refresh_token']
        self.scope = token_info['scope']
        self.expires_at = token_info['expires_at']
        self.save()

    def getCache(self):
        return MemoryCacheHandler(token_info=self.getTokenInfo())

    def getOAuth(self):
        return SpotifyOAuth(scope=SCOPE, client_id=CLIENTID, client_secret=CLIENTSECRET, redirect_uri=REDIRECTURI,
                            cache_handler=self.getCache(), show_dialog=True)

    def getSpotify(self):
        self.refreshIfExpired()
        return Spotify(auth_manager=self.getOAuth())

    def refresh(self):
        self.saveCache(
            self.getOAuth().refresh_access_token(self.refresh_token))

    def refreshIfExpired(self):
        if self.expires_at < time():
            self.refresh()

    objects = SpotifyUserManager()


# usr = SpotifyUser.objects.create_spotifyuser(args)
