# custom util functions
from pprint import pprint


class SpotifyItem():
    """ 
    Class for dealing with spotify (or spotipy) api search results.
    These objects are meant to be temporary, therefore not a django model
    """

    def __init__(self, result, **kwargs):
        """ result is a single item from spotipy search() """
        # try:
        #     self.type = kwargs['type']
        #     self.name = kwargs['name']
        #     self.artists = kwargs['artists']
        #     self.desc = kwargs['desc']
        #     self.img = kwargs['img']
        #     self.nested = kwargs['nested']
        #     self.favorite = kwargs.get('favorite', False)
        # except KeyError:
        #     pass

        self.type = ""  # one of track, album, playlist
        self.name = ""
        self.artists = ""  # or owner for playlist
        self.desc = ""  # duration for track, release year for album, description for playlist
        self.img = ""  # url for image
        self.nested = []  # list of SpotifyItem tracks for albums and playlists
        self.id = ""
        self.favorite = False  # if user saved

        if result['type'] == 'track':
            self.type = result['type']
            self.name = result['name']
            self.artists = ', '.join(x['name'] for x in result['artists'])
            self.desc = f"{int((result['duration_ms']/1000)/60)}:{int((result['duration_ms']/1000)%60)}"
            try:
                self.img = result['album']['images'][0]['url']
            except KeyError:  # queries from .album() doesn't return 'album' in the tracks
                pass
            self.id = result['id']
        elif result['type'] == 'album':
            self.type = result['type']
            self.name = result['name']
            self.artists = ', '.join(x['name'] for x in result['artists'])
            self.desc = result['release_date'].split('-')[0]
            self.img = result['images'][0]['url']
            self.id = result['id']
        elif result['type'] == 'playlist':
            self.type = result['type']
            self.name = result['name']
            self.artists = result['owner']['display_name']
            self.desc = result['description']
            self.img = result['images'][0]['url']
            self.id = result['id']

    def as_dict(self):
        dict = self.__dict__
        dict['nested'] = self.nested
        dict['favorite'] = self.favorite
        return dict

    def __str__(self):
        return self.as_dict().__str__()

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def fromQuery(query):
        """ returns list of SpotifyItems for whole list query """
        ls = []
        for k, v in query.items():
            for i in query[k]['items']:
                ls.append(SpotifyItem(i))
        return ls

    @staticmethod
    def nest(ls, sp):
        """ takes a list of SpotifyItem and a spotipy.Spotify() obj to do the queries with """
        lst = []
        for item in ls:
            if item.type == 'playlist':
                res = sp.playlist(item.id)
                for r in res['tracks']['items']:
                    item.nested.append(SpotifyItem(r['track']))
                lst.append(item)
            elif item.type == 'album':
                res = sp.album(item.id)
                img = res['images'][0]['url']
                for r in res['tracks']['items']:
                    i = SpotifyItem(r)
                    i.img = img
                    item.nested.append(i)

                lst.append(item)
            else:
                lst.append(item)
        return lst
