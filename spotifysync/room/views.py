from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseNotFound
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
    print(request.POST)
    if request.POST and 'search' in request.POST:
        res = spuser.getSpotify().search(
            request.POST['search'], type='track,album,playlist')
        context['query'] = request.POST['search']

        results = SpotifyItem.fromQuery(res)
        results = SpotifyItem.nest(results, spuser.getSpotify())

        for r in results:
            context['results'][r.type + 's'].append(r.as_dict())
        # for re in res['tracks']['items']:
        #     r = {'title': '',
        #          'img': '',
        #          'duration': '',
        #          'artists': ''}
        #     r['title'] = re['name']
        #     r['img'] = re['album']['images'][0]['url']
        #     r['duration'] = f"{int((re['duration_ms']/1000)/60)}:{int((re['duration_ms']/1000)%60)}"
        #     r['artists'] = ', '.join(x['name'] for x in re['artists'])
        #     context['results']['songs'].append(r)

        # for re in res['albums']['items']:
        #     r = {'title': '',
        #          'img': '',
        #          'duration': '',
        #          'artists': ''}
        #     r['title'] = re['name']
        #     r['img'] = re['images'][0]['url']
        #     r['duration'] = re['release_date'].split('-')[0]
        #     r['artists'] = ', '.join(x['name'] for x in re['artists'])
        #     context['results']['albums'].append(r)

        # for re in res['playlists']['items']:
        #     r = {'title': '',
        #          'img': '',
        #          'duration': '',
        #          'artists': ''}
        #     r['title'] = re['name']
        #     r['img'] = re['images'][0]['url']
        #     r['duration'] = re['description']
        #     r['artists'] = re['owner']['display_name']
        #     context['results']['playlists'].append(r)

    return render(request, 'room/add.html', context=context)


@login_required
def roomid(request, roomid):
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

    return render(request, 'room/room.html', context=context)
