import string, random, unittest, requests, json, time, sys, unicodedata

import spotipy
import spotipy.util as util
from pprint import pprint

#############
##User data##
#############

print '\nThis prototype requires manual entry of authentication variables, follow the prompts or enter Access Tokens and API credentials where requested in the "User Data" section of the code.\n'

Spotify_Username = raw_input("Enter your Spotify Username:")

#Spotify API vars
#Can be requested at http://developer.spotify.com
SPOTIPY_CLIENT_ID=""
SPOTIPY_CLIENT_SECRET=""
SPOTIPY_REDIRECT_URI="https://accounts.spotify.com/authorize"

#Facebook API vars
#Can be requested at https://developers.facebook.com/tools/explorer
FACEBOOK_ACCESS_TOKEN=""

#Establish Cachex
CACHE_FNAME= 'cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}

#############
##Functions##
#############

def canonical_order(d):
    alphabetized_keys = sorted(d.keys())
    res = []
    for k in alphabetized_keys:
        res.append((k, d[k]))
    return res

def requestURL(baseurl, params = {}):
    req = requests.Request(method = 'GET', url = baseurl, params = canonical_order(params))
    prepped = req.prepare()
    return prepped.url

def getWithCachingItunes(artist):
    BASE_URL = 'https://itunes.apple.com/search'
    full_url = requestURL(BASE_URL, params={'term': artist})

    if full_url in CACHE_DICTION:
#        print 'using cache'
        # use stored response
        response_text = CACHE_DICTION[full_url]
    else:
#        print 'fetching'
        response = requests.get(full_url)
        # store the response
        CACHE_DICTION[full_url] = response.text
        response_text = response.text

        cache_file = open(CACHE_FNAME, 'w')
        cache_file.write(json.dumps(CACHE_DICTION))
        cache_file.close()
    response_dictionary = json.loads(response_text)

    return response_dictionary

def getWithCachingSpotify(query_and_function,request_type="",query_var="",username=Spotify_Username):
    token = util.prompt_for_user_token(username, client_id = SPOTIPY_CLIENT_ID, client_secret = SPOTIPY_CLIENT_SECRET, redirect_uri = SPOTIPY_REDIRECT_URI)
    if query_and_function in CACHE_DICTION:
#       print 'using cache'
        response_text = CACHE_DICTION[query_and_function]
    else:
#        print 'fetching'
        try:
            if request_type == "band_top_tracks":
                sp = spotipy.Spotify(auth=token)
                artist = sp.search(q='artist:'+ query_var, type='artist')
                artist_id = artist['artists']['items'][0]['id']
                response = sp.artist_top_tracks(artist_id)

            elif request_type == "artist_search":
                sp = spotipy.Spotify(auth=token)
                artist = sp.search(q='artist:'+ query_var, type='artist')
                response = artist['artists']['items'][0]['id']

            elif request_type == "get_user_artists":
                token = util.prompt_for_user_token(username, scope = 'user-top-read', client_id = SPOTIPY_CLIENT_ID, client_secret = SPOTIPY_CLIENT_SECRET, redirect_uri = SPOTIPY_REDIRECT_URI)
                sp = spotipy.Spotify(auth=token)
                if token:
                    response = sp.current_user_top_artists()
                else:
                    return "Can't get token for", username

            elif request_type == "get_user_followed":
                token = util.prompt_for_user_token(username, scope = 'user-follow-read', client_id = SPOTIPY_CLIENT_ID, client_secret = SPOTIPY_CLIENT_SECRET, redirect_uri = SPOTIPY_REDIRECT_URI)
                sp = spotipy.Spotify(auth=token)
                if token:
                    response = sp.current_user_followed_artists(limit=50)
                    next_page = (response['artists']['cursors']['after'])
                    followed = []
                    for item in response['artists']['items']:
                        artist = strip_accents(item['name'])
                        followed.append(artist)
                    while len(response['artists']['items']) == 50:
                        response = sp.current_user_followed_artists(limit=50,after=next_page)
                        next_page = (response['artists']['cursors']['after'])
                        for item in response['artists']['items']:
                            artist = strip_accents(item['name'])
                            followed.append(artist)
                    response = followed
                else:
                    return "Can't get token for", username

            elif request_type == "get_user_tracks":
                token = util.prompt_for_user_token(username, scope = 'user-top-read', client_id = SPOTIPY_CLIENT_ID, client_secret = SPOTIPY_CLIENT_SECRET, redirect_uri = SPOTIPY_REDIRECT_URI)
                sp = spotipy.Spotify(auth=token)
                if token:
                    response = sp.current_user_top_tracks()
                else:
                    return "Can't get token for", username

            elif request_type == "recommendations":
                if username == "":
                    username = raw_input("Enter your username: ")
                token = util.prompt_for_user_token(username= username, client_id = SPOTIPY_CLIENT_ID, client_secret = SPOTIPY_CLIENT_SECRET, redirect_uri = SPOTIPY_REDIRECT_URI)
                sp = spotipy.Spotify(auth=token)
                if token:
                    response = sp.recommendations(seed_artists = query_var, limit = 5)
                else:
                    return "Can't get token for", username
        except:
            return "Unable to return requested Spotify user data.  Check you inputs and retry."

        # store the response
        CACHE_DICTION[query_and_function] = response
        response_text = response

        cache_file = open(CACHE_FNAME, 'w')
        cache_file.write(json.dumps(CACHE_DICTION))
        cache_file.close()

    response_dictionary = response_text
    return response_dictionary

def getWithCachingFacebook():
    access_token = FACEBOOK_ACCESS_TOKEN
    book_url = "https://graph.facebook.com/v2.6/me/"
    book_params = {'limit': 1000, 'access_token': access_token, 'fields' : 'music'}
    full_url = requestURL(book_url, params=book_params)

    if full_url in CACHE_DICTION:
#        print 'using cache'
        # use stored response
        response_text = CACHE_DICTION[full_url]
    else:
#        print 'fetching'
        response = requests.get(book_url, params = book_params )
        fb_data = response.json()
        if response.status_code != 200:
            access_token = raw_input("Get a Facebook access token v2.6 from https://developers.facebook.com/tools/explorer and enter it here:  :\n")

        # store the response
        CACHE_DICTION[full_url] = response.text
        response_text = response.text

        cache_file = open(CACHE_FNAME, 'w')
        cache_file.write(json.dumps(CACHE_DICTION))
        cache_file.close()

    response_dictionary = json.loads(response_text)
    return response_dictionary

###########
##Classes##
###########

class Band():
    def __init__(self, band_dict = {}):
        if 'name' in band_dict:
            self.name = band_dict['name']
        else:
            self.name = ""
        self.genre = Band.get_genre(self)
        self.top_track = Band.get_top_track(self)

    #iTunes sourced
    def get_genre(self):
        try:
            itunes_data = getWithCachingItunes(self.name)
            genre_diction = {}
            count = 0
            for item in itunes_data['results']:
                genre =  itunes_data['results'][count]['primaryGenreName']
                count += 1
                if genre not in genre_diction:
                    genre_diction[genre] = 0
                genre_diction[genre] += 1
            key = genre_diction.items()
            sort = sorted(key, key=lambda key: key[1], reverse=True)
            genre = sort[0][0]
        except:
            genre = "Unknown"
        return genre

    #Spotify sourced
    def get_top_track(self):
        results = getWithCachingSpotify(self.name+"_top_track","band_top_tracks",self.name)
        track = results['tracks'][0]['name']
        return track

class Spotify_User():
    def __init__(self,user = ""):
        if user == "":
            self.username = raw_input('Enter your Spotify username:')
        else:
            self.username = user
        self.following = self.get_user_followed()
        self.top_artists = self.get_user_artists()
        self.top_tracks = self.get_user_tracks()

    def get_user_followed(self):
            results = getWithCachingSpotify(self.username+"_get_user_followed","get_user_followed",self.username)
            return results

    def get_user_artists(self):
            results = getWithCachingSpotify(self.username+"_get_user_artists","get_user_artists",self.username)
            top = []
            for item in results['items']:
                top.append((item['name']))
            return top

    def get_user_tracks(self):
            results = getWithCachingSpotify(self.username+"_get_user_tracks","get_user_tracks",self.username)
            top = []
            for item in results['items']:
                top.append((item['artists'][0]['name'] + " - " + item['name']))
            return top

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def band_data_conversion(lst):
    content = []
    for item in lst:
        diction = {"name": item}
        content.append(diction)
    return content

def top_tracks(artistvar):
    try:
        tracks = getWithCachingSpotify(artistvar+"_top_track","band_top_track",artistvar)
        tracks = tracks['tracks']
        top_tracks = []
        count = 0
        for item in tracks:
            top_tracks.append((tracks[count]['name'],tracks[count]['popularity']))
            count += 1
        return top_tracks
    except:
        "'Code failed collecting top tracks, please try again.'"

def facebook_rec(user, band_list):
    token = util.prompt_for_user_token(username= user, client_id = SPOTIPY_CLIENT_ID, client_secret = SPOTIPY_CLIENT_SECRET, redirect_uri = SPOTIPY_REDIRECT_URI)
    sp = spotipy.Spotify(auth=token)
    the_band_list = [item.name for item in band_list]
    upperbound = len(band_list)-1
    repeats = []
    count = 0
    try:
        lst = []
        for item in the_band_list:
            if len(the_band_list) <= 10:
                lst = the_band_list
            if count < 10:
                inte = random.randint(0,upperbound)
                artist = the_band_list[inte]
                the_band_list.remove(artist)
                count += 1
                upperbound -= 1
#                artist_search = sp.search(q='artist:'+ artist, type='artist')
                artist_search = getWithCachingSpotify(artist+"_artist_search","artist_search",artist)
                lst.append(artist_search)
                time.sleep(.25)
        #recs = sp.recommendations(seed_artists= lst, limit = 5)
        recs = getWithCachingSpotify("recs", "recommendations",lst)
        song_recs = []
        count = 0
        for item in recs['tracks']:
            time.sleep(.25)
            song_recs.append(item['artists'][0]['name'] + " - " + item['name'])
            count += 1
        return song_recs
    except:
        'Code failed on Facebook recommendations, please try again.'

def explicit_content(artist):
    tunes_data = getWithCachingItunes(artist)
    diction = {'explicit':0,'cleaned':0,'notExplicit':0}
    count = 0
    for item in tunes_data['results']:
        try:
            ex =  tunes_data['results'][count]['trackExplicitness']
            count += 1
            if ex not in diction:
                diction[ex] = 0
            diction[ex] += 1
        except:
            continue
    if diction["explicit"] >= 1:
        if diction['explicit'] > diction['notExplicit']+ diction['cleaned']:
            return "The majority of artist content is explicit."
        else:
            return "Explicit content found."
    else:
        return "No explicit content found."

def artist_percent_explicit(band_lst):
    Output_Dict = {'explicit':0,'notExplicit':0}
    for item in band_lst:
        try:
            output = explicit_content(item)
            if output == "The majority of artist content is explicit.":
                Output_Dict['explicit'] += 1
            elif output == "Explicit content found.":
                Output_Dict['explicit'] += 1
            elif output == "No explicit content found.":
                Output_Dict['notExplicit'] += 1
        except:
            continue
    total_band = len(band_lst)
    return '{0:.2f}'.format((float(Output_Dict['explicit'])/float(total_band)*100))

def missing_bands(username=""):
    fb_data = getWithCachingFacebook()
    fb_insts = [Band(item) for item in fb_data['music']['data']]
    fb_lst = [item.name.lower() for item in fb_insts]
    username = Spotify_User(username)
    spot_data = username.following
    spot_data = band_data_conversion(spot_data)
    spot_insts = [Band(item) for item in spot_data]
    spot_lst=[item.name.lower() for item in spot_insts]

    shared_artists = []
    fb_missing_artists = []
    fb_string = ""
    count=0
    for item in spot_lst:
        if item in fb_lst:
            shared_artists.append(item)
        else:
            fb_missing_artists.append(item)
            fb_string = fb_string + strip_accents(spot_insts[count].name) + ", "
            count += 1
    fb_string = fb_string.rstrip(", ")

    spot_missing_artists = []
    spot_string = ""
    count = 0
    for item in fb_lst:
        if item not in spot_lst:
            spot_missing_artists.append(item)
            spot_string = spot_string + strip_accents(spot_insts[count].name) + ", "
            count += 1
    spot_string = spot_string.rstrip(", ")

    if spot_missing_artists and fb_missing_artists == []:
        return "Your accounts have the same artists\n"
    elif spot_missing_artists == []:
        return "Your Facebook account is missing these artists: " + fb_string+"\n\n" + "Your Spotify account isn't missing artists.\n"
    elif fb_missing_artists == []:
        return "Your Spotify account is missing these artists: " + spot_string +"\n\n" + "Your Facebook account isn't missing artists.\n"
    else:
        return "Your Spotify account is missing these artists: " + spot_string+"\n\n" + "Your Facebook account is missing these artists:" + fb_string+"\n"

def most_common_genre (band_lst):
    dictionary = {}
    band_content = band_data_conversion(band_lst)
    band_lst = [Band(item) for item in band_content]
    for item in band_lst:
        if item.genre not in dictionary:
            dictionary[item.genre] = 0
        dictionary[item.genre] += 1
    key = dictionary.items()
    sort = sorted(key, key=lambda key: key[1], reverse=True)
    genres_lst = []
    string = ""
    top_score = sort[0][1]
    for item in sort:
        if item[1] == top_score and item[1] not in genres_lst:
            genres_lst.append(item)
    for item in genres_lst:
        string = string + item[0] +", "
    string = string.rstrip(", ")
    if len(genres_lst) == 1:
        return "most common genre is " + string + "."
    else:
        return "most common genres are " + string +"."

#Install cache file that lasts 10 minutes
#requests_cache.install_cache('cache', backend='memory', expire_after=600)

#############
##Main Code##
#############

#Create output file
Fname = 'output.txt'
output_file = open(Fname, 'w')
output_file.write("This program is intended to teach users a bit about their musical taste and optimize their social media to bring them information on bands.\n\n")

# Create list of instances of Bands from user's facebook
fb_data = getWithCachingFacebook()
fb_band_insts = [Band(item) for item in fb_data['music']['data']]
fb_lst = [item.name for item in fb_band_insts]

#Create a list of instances of Bands from user's Spotify
User = Spotify_User(Spotify_Username) #
spot_lst = User.following
spot_dict = band_data_conversion(spot_lst)
spot_insts = [Band(item) for item in spot_dict]

#Artist Count
total_artists = []
for item in fb_lst:
    if item not in total_artists:
        total_artists.append(item)
for item in spot_lst:
    if item not in total_artists:
        total_artists.append(item)

output_file.write("Below are lists of artists which are not shared between your user accounts so that you can be sure to keep up with the news on your favorite bands.\n\n")
output_file.write(missing_bands(Spotify_Username)+"\n")

output_file.write("According to these services some of your musical tastes tend towards the following genres.\n\n")

output_file.write("On Spotify your " + most_common_genre(spot_lst)+ "\n\n")
output_file.write("On Facebook your " + most_common_genre(fb_lst) + "\n\n")

output_file.write("According to Spotify for your top artists your " + most_common_genre(User.top_artists) + "\n\n")

output_file.write("According to the iTunes APIs definitions, roughly " + artist_percent_explicit(total_artists) + " percent of your liked and followed artists have explicit material.\n\n")

output_file.write("Based on your Facebook music likes Spotify would recommend the following tracks:\n\n")
fb_rec = facebook_rec(Spotify_Username, fb_band_insts)
for item in fb_rec:
     output_file.write(item + "\n")
output_file.write("\n")

output_file.write("The top tracks on Spotify for your facebook likes: \n\n")
for item in fb_band_insts:
    output_file.write(item.name + " - " + item.top_track)
    output_file.write('\n')
output_file.write("\n")

output_file.write("Your top tracks on Spotify are: \n\n")
for item in User.top_tracks:
    output_file.write(item)
    output_file.write("\n")

output_file.close()

print "\nExecution complete.  Check the program directory for output.txt!\n"

##############
##Unit Tests##
##############

class Func_tests(unittest.TestCase):
    def test_top_tracks(self):
        Beats = top_tracks("The Beatles")
        self.assertEqual(type(Beats), type([]), "Testing that Band genre is a string")

    def test_band_convert(self):
        lst = ["The Beatles","Ratatat"]
        new = band_data_conversion(lst)
        keys = new[0].keys()
        self.assertEqual(type(new[0]),type({}), "Testing that conversion is dictionary")
        self.assertEqual(keys[0], "name", "Testing key is name")

    def test_most_common_genre(self):
        lst = ["Ratatat"]
        new = most_common_genre(lst)
        self.assertEqual(type(new),type(u""), "Testing that conversion is list")

    def test_missing_bands(self):
        test = missing_bands(Spotify_Username)
        self.assertEqual(type(test),type(u'\xf3'), "Testing return value for missing bands")

    def test_explicit_content_percent(self):
        test = artist_percent_explicit(["The Beatles"])
        self.assertEqual(test, "0.00", "Testing return value")

    def test_explicit_content(self):
        test = explicit_content(["The Beatles"])
        self.assertEqual(test, "No explicit content found.", "Testing return value")

class Band_tests(unittest.TestCase):
    def test_band_string(self):
        Beatles = Band({"name":"The Beatles"})
        self.assertEqual(type(Beatles.genre), type(u""), "Testing that Band genre is a string")
        self.assertEqual(type(Beatles.name), type(""), "Testing that Band name is a string")
        self.assertEqual(type(Beatles.top_track), type(u""), "Testing that Band name is a string")

class Spotify_User_tests(unittest.TestCase):
     def test_user_lists(self):
         user = Spotify_User(Spotify_Username)
         self.assertEqual(type(user.top_tracks), type([]), "Testing that Band name is a string")
         self.assertEqual(type(user.top_artists), type([]), "Testing that Band name is a string")

unittest.main(verbosity=2)
