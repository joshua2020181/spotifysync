import json
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect
from spotipy.exceptions import SpotifyException
from .models import Room
from home.models import SpotifyUser
from time import time, sleep
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

    if request.POST and 'song-done' in request.POST:
        context['current_playback'] = spuser.getSpotify().current_playback()
        if context['current_playback']:
            # playing next item in queue
            if len(room.queue) > 0 and context['current_playback']['item']['id'] == room.queue[0]['id']:
                room.prevTrack = room.queue.pop(0)
                room.save()
                return JsonResponse({'song-done': True})
            # playing another song
            elif request.POST['song-done'] != context['current_playback']['item']['id']:
                return JsonResponse({'song-done': True})
        return JsonResponse({'song-done': False})

    if request.POST and 'push-queue' in request.POST:
        print(f'new queue: {request.POST["push-queue"]}')
        room.queue = json.loads(request.POST['push-queue'])
        room.save()
        return JsonResponse({})

    if request.POST and 'leave' in request.POST:
        spuser.room = None
        return redirect('/room/')
    if request.POST and 'sync' in request.POST:
        context['current_playback'] = spuser.getSpotify().current_playback()
        if not context['current_playback']:
            context['errormsg'] = "Please start a playback session first (press play on Spotify)"
            print('no playback sess')
            # handle no playback
        else:
            for p in participants:
                # if p == spuser:  # skips initiator so their context isn't messed up
                #     continue
                puser = SpotifyUser.objects.get(user=p)
                curr = puser.getSpotify().current_playback()
                puser.getSpotify().shuffle(False)
                puser.getSpotify().start_playback(device_id=curr['device']['id'],
                                                  uris=[context['current_playback']['item']['uri']] + ["spotify:track:"+track['id']
                                                                                                       for track in room.queue],
                                                  position_ms=context['current_playback']['progress_ms'])
                if not context['current_playback']['is_playing']:
                    puser.getSpotify().pause_playback()
    if request.POST and 'pause' in request.POST:
        for p in participants:
            try:
                p.getSpotify().pause_playback()
            except SpotifyException:  # user already paused
                pass
    if request.POST and 'play' in request.POST:
        # could hide a sync in here if I store the current room playback status in db
        for p in participants:
            try:
                p.getSpotify().start_playback()
            except SpotifyException:  # user already playing
                pass
    if request.POST and 'rewind' in request.POST:
        context['current_playback'] = spuser.getSpotify().current_playback()
        if not context['current_playback']:
            context['errormsg'] = "Please start a playback session first (press play on Spotify)"
            print('no playback sess')
            # handle no playback
        for p in participants:
            puser = SpotifyUser.objects.get(user=p)
            curr = puser.getSpotify().current_playback()
            puser.getSpotify().shuffle(False)
            if room.prevTrack:
                puser.getSpotify().start_playback(device_id=curr['device']['id'],
                                                  uris=["spotify:track:"+track['id']
                                                        for track in [room.prevTrack] + room.queue],
                                                  position_ms=0)
            else:
                puser.getSpotify().start_playback(device_id=curr['device']['id'],
                                                  uris=[context['current_playback']['item']['uri']] + ["spotify:track:"+track['id']
                                                                                                       for track in room.queue],
                                                  position_ms=0)
        if room.prevTrack:
            room.queue.insert(0, SpotifyItem(
                context['current_playback']['item']).as_dict())
            room.prevTrack = {}
            room.save()
    if request.POST and 'skip' in request.POST:
        context['current_playback'] = spuser.getSpotify().current_playback()
        if not context['current_playback'] or not context['current_playback']['item']:
            context['errormsg'] = "Please start a playback session first (press play on Spotify)"
            print('no playback sess')
            # handle no playback
        room.prevTrack = SpotifyItem(
            context['current_playback']['item']).as_dict()
        for p in participants:
            puser = SpotifyUser.objects.get(user=p)
            curr = puser.getSpotify().current_playback()
            puser.getSpotify().shuffle(False)
            puser.getSpotify().start_playback(device_id=curr['device']['id'],
                                              uris=["spotify:track:"+track['id']
                                                    for track in room.queue],
                                              position_ms=0)
        if room.queue:
            room.queue.pop(0)
            room.save()
        print(f'{room.prevTrack=}')

    context['current_playback'] = spuser.getSpotify().current_playback()
    context['queue'] = json.dumps(room.queue)

    return render(request, 'room/room.html', context=context)
