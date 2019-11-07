
import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    """inserts filtered artist data into artist_table from song_data

    Parameters:
    query: cursor, filepath

    Returns:NONE

   """
    df = pd.read_json(filepath, typ='series')
    
    song_columns = ['song_id'
        , 'title'
        , 'artist_id'
        , 'year'
        , 'duration']

    song_data = df[song_columns]

    try: 
        cur.execute(song_table_insert, song_data)

    except psycopg2.Error as e: 
        print("Error: Issue creating table")
        print (e)
    
    artist_columns = ['artist_id'
        , 'artist_name'
        , 'artist_location'
        , 'artist_latitude'
        , 'artist_longitude']

    artist_data = df[artist_columns]

    try: 
        cur.execute(artist_table_insert, artist_data)

    except psycopg2.Error as e: 
        print("Error: Issue creating table")
        print (e)

        
def process_log_file(cur, filepath):
    """inserts filtered data records into time table from log_data
    inserts user id data records into user table from log_data
    inserts filtered songplay records into songplay table from log_data

    Parameters:
    query: cursor, filepath

    Returns:NONE

   """
    df = pd.read_json(filepath, lines=True)

    df = df[df['page'] == 'NextSong']
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')

    time_data = [df['ts']
        , df['ts'].dt.hour
        , df['ts'].dt.day
        , df['ts'].dt.weekofyear
        , df['ts'].dt.month
        , df['ts'].dt.year
        , df['ts'].dt.weekday]

    column_labels = ['ts'
        , 'hour'
        , 'day'
        , 'week of year'
        , 'month'
        , 'year'
        , 'weekday']

    dictionary = dict(zip(column_labels, time_data))
    time_df = pd.DataFrame.from_dict(dictionary)

    for i, row in time_df.iterrows():
        try: 
            cur.execute(time_table_insert, list(row))
            
        except psycopg2.Error as e: 
            print("Error: Issue creating table")
            print (e)

    user_columns = ['userId'
        , 'firstName'
        , 'lastName'
        , 'gender'
        , 'level']

    user_df = df[user_columns]

    for i, row in user_df.iterrows():
        try: 
            cur.execute(user_table_insert, row)
            
        except psycopg2.Error as e: 
            print("Error: Issue creating table")
            print (e)

    mylist = list(df.select_dtypes(include=['object']).columns)

    for column in mylist:
        df[column] = df[column].astype(str)

    for index, row in df.iterrows():
        cur.execute(song_artist_select, (row.song, row.artist, row.length))
        results = cur.fetchone()

        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        songplay_data = (row.ts
                         , row.userId
                         , row.level
                         , songid
                         , artistid
                         , row.sessionId
                         , row.location
                         , row.userAgent)
        try: 
            cur.execute(songplay_table_insert, songplay_data)
            
        except psycopg2.Error as e: 
            print("Error: Issue creating table")
            print (e)
        


def process_data(cur, conn, filepath, func):
    """get all files, process selected filepath for different data, selects functions 

    Parameters:
    query: cursor,connection, filepath, functions

    Returns:NONE

   """
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root, '*.json'))
        for f in files:
            all_files.append(os.path.abspath(f))

    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    conn = psycopg2.connect(
        "host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    cur.close()
    conn.close()
    print("el fin")


if __name__ == "__main__":
    main()
