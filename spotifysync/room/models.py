from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class SpotifyUserManager(models.Manager):
    def create_spotifyuser(self, user, **kwargs):
        spusr = self.create(user=user)
        return spusr


class SpotifyUser(models.Model):
    user = models.OneToOneField(
        User, primary_key=True, on_delete=models.RESTRICT)
    auth_token = models.CharField(blank=True, max_length=255)
    refresh_token = models.CharField(blank=True, max_length=255)

    def getCachePath(self):
        return f'/caches/{self.user.username}'
    objects = SpotifyUserManager()


# usr = SpotifyUser.objects.create_spotifyuser(args)
