from fuzzywuzzy import fuzz
import pandas as pd
import re
from os.path import exists


def get_track_uris(sample_data, sp):
    '''Given cleaned, scraped track data, this function tries to find the best
    matching songs on Spotify. 
    
    This is done by fuzzy matching the scraped track title and artist with the
    top 5 search results when these are queried on Spotify. If the matching 
    score is above a set threshold, the Spotify URI of the matched track will
    be returned by this function. 
    
    Arguments:
        sample_data: dataframe of cleaned, scraped data
        sp: SpotifyOAuth object
        
    Returns:
         track_uris: a list of Spotify track URIs best matching inputted tracks
    '''

    # get Spotify track uris for samples
    track_uris = []
    
    # looping through input data to get Spotify URIs
    for i in range(len(sample_data.index)):
        
        print("Fetching URI for track number {}".format(i+1))
        results = sp.search(
            q=f"{sample_data['title'][i]} {sample_data['artist'][i][0]}", 
            limit=5, # get 5 responses since first isn't always accurate
            type='track') 
        
        # if track isn't on spotify as queried, go to next track
        if results['tracks']['total'] == 0:
            
            print("The query \"{}\" found no results on Spotify.".format(
                f"{sample_data['title'][i]} {sample_data['artist'][i][0]}"))

            print("Searching Spotify using only title of track...")            
            results = sp.search(
                q=f"{sample_data['title'][i]}", 
                limit=5, # get 5 new responses from only title
                type='track')
            
            if results['tracks']['total'] == 0:
                print("Still no results. Skipping track...")
                track_uris.append(None)
                continue

        found_uri = False
        
        # looping through Spotify responses to find best match
        for j in range(len(results['tracks']['items'])):

            # get number of artists in the Spotify response
            title_j = results['tracks']['items'][j]['name']
            artists_j = results['tracks']['items'][j]['artists']
            num_artists = len(artists_j)
            
            # get match scores for each artist in the Spotify response
            artists_match_scores = [
                fuzz.partial_ratio(
                    artists_j[x]['name'].lower(),
                    sample_data['artist'][i][0].lower()
                    )
                for x in range(num_artists)
                ]
            
            # get score of best artist match
            artist_match_score = max(artists_match_scores)

            # get score of title match
            # a track only has one title, so we only get a single score
            title_match_score = fuzz.partial_ratio(
                title_j.lower(), 
                sample_data['title'][i].lower()
                )


            # if either artist or title is above 90, or the sum of the two is 
            # above 175, we have a good match
            if ((artist_match_score > 90 and title_match_score > 90) or 
                artist_match_score+title_match_score > 175):
                
                track_uris.append(results['tracks']['items'][j]['uri'])
                found_uri = True
                
                # we don't want repeats of a sample ex: different versions
                break
            
            else:
                print(f"Search result {j+1} for the query "
                      f"\"{sample_data['title'][i]}\" by \"{sample_data['artist'][i][0]}\""
                      f" did not sufficiently match"
                      f"\"{title_j}\" by \"{artists_j[0]['name']}\" from Spotify.")
                continue
        if not found_uri:
            track_uris.append(None)
        
    print("Got {} track URIs from {} searches.".format(
        len(track_uris)-track_uris.count(None), 
        len(sample_data)))
    
    return track_uris


def update_track_df(weekly, sp):
    """Creates or updates a track dataframe with scraped data, along with 
    Spotify URIs. If a track is already in the dataframe, it will not be 
    considered.
    
    The dataframe is saved as both a pickle and csv file and returned by this 
    function.
    
    Arguments:
        weekly: tuple of scraped data from Andyg's website
        sp: SpotifyOAuth object

    Returns:
        df: the updated dataframe
    """
    week_info_body, time_wide_list, time_narrow_list, main = weekly
    
    # checking if we have new data
    if exists("data/scraped_dataframe.pkl"):
        old_df = pd.read_pickle("data/scraped_dataframe.pkl")

        print("Number of tracks in scrape:", len(week_info_body)) 
        print("Number of tracks in existing dataframe:", len(old_df))

        # no new data has been scraped
        if len(old_df) == len(week_info_body):
            print("No new data: most recent week is already in the dataframe. "
                  "Dataframe not updated.")
            return old_df

    title_list  = []
    artist_list = []
    for week in main:

        # finding title
        try:
            title = week.find('a', class_='track').text.strip()

        # if there is no link, the title is in an em tag
        except AttributeError:
            title = week.find('em', class_='anontrack').text.strip()

        title_list.append(re.sub(u"\u2019", "'", title))

        # finding artist(s)
        artists = week.find_all('a', class_='artist')
        sub_list = []
        for artist in artists:
            sub_list.append(re.sub(u"\u2019", "'", artist.text.strip()))
        artist_list.append(sub_list)


    # creating dataframe
    data = {'title': title_list, 
            'artist': artist_list,
            'week': week_info_body,
            'time_wide': time_wide_list,
            'time_narrow': time_narrow_list}
    df = pd.DataFrame(data)

    # special missing artist case
    df.loc[df.title == "80'eren", "artist"] = [["Bikstok"]]
    
    
    # if we do not have a dataframe in a pickle file yet, create one
    if not exists("data/scraped_dataframe.pkl"):
        
        # the week of the first unavoidable track was 1991 07
        #most_recent_week = "1991 07"
        
        # fetch Spotify URIs for all tracks
        df["uri"] = get_track_uris(df, sp)
        
        # save dataframe to pickle and csv
        df.to_pickle("data/scraped_dataframe.pkl")
        df.to_csv("data/scraped_dataframe.csv")
        print("Saved scraped dataframe for the first time!")


    # if we do have a dataframe in a pickle file, update it
    else:

        # the most recent week in the stored dataframe
        most_recent_week = old_df.iloc[0][2]

        # go backwards through weeks to preserve order
        for week in range(len(df)-1, -1, -1):
            
            # str comparison: is the most recent week in the old dataframe newer?
            if most_recent_week >= df.iloc[week][2]:
                # if so, we move on to the next week
                continue
    
            new_week = df.iloc[[week]].reset_index(drop=True)
            new_week["uri"] = get_track_uris(new_week, sp)
            
            print(f"Adding track for week {new_week['week'][0]} "
                  f"with uri {new_week['uri'][0]}...")
            
            # add new week to old dataframe
            old_df = pd.concat([new_week, old_df]).reset_index(drop=True)
        
        # save updated dataframe to pickle and csv
        df = old_df
        df.to_pickle("data/scraped_dataframe.pkl")
        df.to_csv("data/scraped_dataframe.csv")
        print("Updated scraped dataframe with new data!")
            
    return df
