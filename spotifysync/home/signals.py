from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import SpotifyUser


@receiver(post_save, sender=get_user_model)
def create_spotify_user(sender, instance, created, **kwargs):
    print('here' + '-'*100)
    if created:
        SpotifyUser.objects.create(user=instance)
