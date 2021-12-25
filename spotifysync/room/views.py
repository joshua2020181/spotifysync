import json
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect
from spotipy.exceptions import SpotifyException
from .models import Room
from home.models import SpotifyUser
from time import time
from room.utils import SpotifyItem
# Create your views here.


@login_required
def room(request):
    # if room alr exists
    context = {'user': request.user}
    SpotifyUser.objects.get(user=request.user).refreshIfExpired()
    if request.POST and 'join' in request.POST:
        rmfilter = Room.objects.filter(id=request.POST['roomid'])
        if rmfilter and (rmfilter[0].allowed_users.filter(id=request.user.id) or rmfilter[0].password == request.POST['password']):
            rmfilter[0].allowed_users.add(request.user)
            return redirect(f'/room/{rmfilter[0].id}/')
        context['errormsg'] = "Incorrect Room ID or Password"
        return render(request, 'room/homeroom.html', context=context)
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
def add(request, roomid, page):
    context = {'user': request.user,
               'results': {
                   'tracks': [],
                   'albums': [],
                   'playlists': [],
               }}

    # check if user is allowed to be here --------------

    room = Room.objects.filter(id=roomid)
    if not len(room) == 1:
        return HttpResponseNotFound('Room not found, please double check the URL')
    room = room[0]
    room.activate()  # refreshes lastActive field
    context['room'] = room
    spuser = SpotifyUser.objects.get(user=request.user)
    if request.POST and 'add_id' in request.POST:  # queuing a song
        item = room.getItemIfFresh(request.POST['add_id'])
        if not item:
            item = SpotifyItem(
                spuser.getSpotify().track(request.POST['add_id'])).as_dict()
        return JsonResponse({'success': room.addItem(item)})
    if request.POST and 'search' in request.POST:
        res = spuser.getSpotify().search(
            request.POST['search'], type='track,album,playlist')
        context['query'] = request.POST['search']

        results = SpotifyItem.fromQuery(res)
        results = SpotifyItem.nest(results, spuser.getSpotify())

        room.addSearch(context['query'], [r.as_dict() for r in results])

        for r in results:
            context['results'][r.type + 's'].append(r.as_dict())
    return render(request, 'room/add.html', context=context)


@login_required
def roomid(request, roomid):
    print(f'{request.POST=}')
    spuser = SpotifyUser.objects.get(user=request.user)
    room = Room.objects.filter(id=roomid)
    if not len(room) == 1:
        return HttpResponseNotFound('Room not found, please double check the URL')
    room = room[0]
    room.activate()  # refreshes lastActive field
    context = {'room': room}

    if spuser.room != room.id:
        if room.allowed_users.filter(id=request.user.id):
            spuser.room = room
            spuser.save()
        else:
            print('user not in allowed users')
            response = redirect('/room/')
            response['Location'] += f'?room={room.id}'
            return response
        # check if password is incorrect
    participants = SpotifyUser.objects.filter(
        room=room.id)  # note: host is also in participants

    if request.POST and 'push-queue' in request.POST:
        print(f'new queue: {request.POST["push-queue"]}')
        room.queue = request.POST['push-queue'].replace(
            '[', '').replace(']', '').split()
        room.save()

    if request.POST and 'leave' in request.POST:
        spuser.room = None
        return redirect('/room/')
    if request.POST and 'sync' in request.POST:
        context['current_playback'] = SpotifyUser.objects.get(
            user=request.user).getSpotify().current_playback()
        if not context['current_playback']:
            context['errormsg'] = "Please start a playback session first (press play on Spotify)"
            print('no playback sess')
            # handle no playback
        for p in participants:
            if p == room.host:  # skips initiator so their context isn't messed up
                continue
            puser = SpotifyUser.objects.get(user=p)
            curr = puser.getSpotify().current_playback()
            puser.getSpotify().start_playback(device_id=curr['device']['id'],
                                              uris=[
                                                  context['current_playback']['item']['uri']],
                                              position_ms=context['current_playback']['progress_ms'])
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
    if request.POST and 'rewind' in request.POST:
        for p in participants:
            try:
                p.getSpotify().previous_track()
            except SpotifyException:  # user already playing
                pass
    if request.POST and 'skip' in request.POST:
        for p in participants:
            try:
                p.getSpotify().next_track()
            except SpotifyException:  # user already playing
                pass

    context['current_playback'] = SpotifyUser.objects.get(
        user=room.host).getSpotify().current_playback()

    # if host is listening to first song in queue, remove that element from the queue
    if context['current_playback'].get('item').get('id', False) and len(room.queue) > 0:
        if context['current_playback']['item']['id'] == room.queue[0].get(id, ''):
            room.queue.pop(0)
            room.save()
    context['queue'] = json.dumps(room.queue)

    return render(request, 'room/room.html', context=context)
