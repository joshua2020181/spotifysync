from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseNotFound
from django.shortcuts import render
from spotipy.exceptions import SpotifyException
from .models import Room
from home.models import SpotifyUser
# Create your views here.


@login_required
def room(request):
    # if room alr exists
    context = {'user': request.user}
    if len(Room.objects.filter(host=request.user)) == 0:
        room = Room.objects.create(host=request.user)
        context['room'] = room
    else:
        context['room'] = Room.objects.get(host=request.user)
    return render(request, 'room/homeroom.html', context=context)


@login_required
def new(request):
    context = {'user': request.user}
    if len(Room.objects.filter(host=request.user)) == 0:
        room = Room.objects.create(host=request.user)
        context['room'] = room
    else:
        room = Room.objects.get(host=request.user)
        room.delete()
        room = Room.objects.create(host=request.user)
        context['room'] = room
    return render(request, 'room/new.html', context=context)


@login_required
def roomid(request, roomid):
    spuser = SpotifyUser.objects.get(user=request.user)
    room = Room.objects.filter(id=roomid)
    if not len(room) == 1:
        return HttpResponseNotFound('Room not found, please double check the URL')
    room = room[0]

    if spuser.room != room.id:
        # check if user can be in this room, prompt for password, etc.
        spuser.room = room
        spuser.save()
        pass

    participants = SpotifyUser.objects.filter(
        room=room.id)  # note: host is also in participants

    if request.POST and 'pause' in request.POST:
        for p in participants:
            try:
                p.getSpotify().pause_playback()
            except SpotifyException:  # user already paused
                pass
    if request.POST and 'play' in request.POST:
        for p in participants:
            try:
                p.getSpotify().start_playback()
            except SpotifyException:  # user already playing
                pass
    return render(request, 'room/room.html', {'room': room})
