from django.shortcuts import render
from home.models import SpotifyUser

# Create your views here.

from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
from spotifysync.settings import SCOPE, CLIENTID, CLIENTSECRET, REDIRECTURI


def signin(request):
    print(request.POST)
    if request.POST:
        user = authenticate(
            username=request.POST['uname'], password=request.POST['password'])
        if user is not None:
            login(request, user)
            return redirect('/home')
        else:
            return render(request, "signin.html", {"errormsg": "Incorrect username or password"})
    return render(request, "account/signin.html")


def create(request):
    if request.POST:
        username = request.POST['uname']
        password = request.POST['password']
        if password != request.POST['confirm']:
            return render(request, "account/create.html", {"errormsg": "Passwords don't match"})
        # check if username is duplicate

        User.objects.create_user(username=username, password=password)
        user = authenticate(username=username, password=password)
        if user is not None:  # prob not needed
            login(request, user)
            u = SpotifyUser.objects.filter(user=user)
            if not u:  # receiver signal not working
                spusr = SpotifyUser.objects.create(user=user)
                spusr.save()

            return redirect('/account/link')
    return render(request, "account/create.html")


@login_required
def link(request):
    spuser = SpotifyUser.objects.get(user=request.user)
    auth = spuser.getOAuth()

    if auth.validate_token(spuser.getCache().get_cached_token()):  # alr linked
        return redirect('/home/')

    if request.GET.get('code'):  # redirected from spotify
        auth.get_access_token(code=request.GET['code'])
        print(auth.validate_token(request.GET['code']))
        sp = Spotify(auth_manager=auth)
        spuser.saveCache(auth.get_cached_token())
        spuser.save()
        return redirect('/home/')

    if not auth.validate_token(spuser.getCache().get_cached_token()):  # need to login
        return render(request, "link.html", context={'link_url': auth.get_authorize_url()})
    return render(request, "account/link.html")


@ login_required
def unlink(request):
    spuser = SpotifyUser.objects.get(user=request.user)
    spuser.deleteCache()
    return render(request, "account/unlink.html")
