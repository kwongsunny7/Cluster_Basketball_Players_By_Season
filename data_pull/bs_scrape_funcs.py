import pandas as pd
import re
import urllib
from bs4 import BeautifulSoup
from collections import defaultdict
from string import ascii_lowercase

def scrape_player(link, years):
    '''
    This function takes an input of a link to a player on basketball 
    reference and years desired and returns two tables with player physical 
    information and logs of all games. 
    '''

   	# Intializes Variables for acquriing data
    links_list = set()
    player_info = defaultdict(str)
    game_logs = defaultdict(defaultdict)

    # Gathers HTML of player page
    player = urllib.request.urlopen(link)
    player_html = BeautifulSoup(player, 'html.parser')

    # Adds Player_id and player name to player physical information
    link_split = link.split('/')
    player_id = link_split[len(link_split)-1]
    player_id = player_id.replace('.html','') 
    player_name = player_html.find('title').get_text().split('|')[0].replace(' Stats','')
    player_info['player_id'] = player_id
    player_info['player_name'] = player_name

    # variables to fill in when the player doesn't play the game.
    fill_in_cols = ['gs', 'mp', 'fg','fga', 'fg_pct', 'fg3', 'fg3a', 'fg3_pct',
                'ft', 'fta', 'ft_pct', 'orb', 'drb', 'trb', 'ast', 'stl',
                'blk','tov','pf','pts','game_score','plus_minus']
    
    # gathers physical attributes of player
    for link in player_html.findAll('p'):
        html_txt = link.get_text()
        search = True
        if 'Position:' in html_txt and search == True:
            position_dom_hand = html_txt.split()
            pos_index = position_dom_hand.index('Position:')
            shoots_index = position_dom_hand.index('Shoots:')
            player_info['position'] = " ".join(position_dom_hand[pos_index + 1 
                                               : shoots_index - 1])
            player_info['dominant_hand'] = position_dom_hand[shoots_index + 1]
            search = False
        else:
            try:
                for span in link.findAll('span'):
                    if span['itemprop'] in 'height':
                        player_info['height'] = span.get_text()
                    elif span['itemprop'] in 'weight':
                        player_info['weight'] = span.get_text()
            except:
                continue
    
    # gathers lists of all of all links of game logs from a player
    # links are seperated by year
    stop_tag = False
    for link in player_html.findAll('li'):
        try:
            a_tag = link.find('a')
            if 'gamelog' in a_tag['href'] and 'gamelog-playoffs' not in a_tag['href']:
                stop_tag = True
                links_list.add('https://www.basketball-reference.com' + a_tag['href'])
            elif stop_tag:
                break
        except:
            continue
    
    links_list = sorted(list(links_list))
    
    # for all links, gathers box score statistics for a player on every year
    for link in links_list:
        year = link[len(link)-4:len(link)]
        if year in years:
            player_year = urllib.request.urlopen(link)
            player_year_html = BeautifulSoup(player_year, 'html.parser')
            player_bs_data = defaultdict(list)
            for table in player_year_html.findAll('tbody'):
                for row in table.findAll('tr'):
                    for col in row.findAll('td'):
                        if col['data-stat'] == 'reason':
                            for col_name in fill_in_cols:
                                if col_name in player_bs_data.keys():
                                    player_bs_data[col_name].append('-')
                                else:
                                    player_bs_data[col_name] = ['-']
                        else:                 
                            if col['data-stat'] in player_bs_data.keys():
                                player_bs_data[col['data-stat']].append(col.get_text())
                                if col['data-stat'] == 'date_game':
                                    player_bs_data['game_id'].append(col.find('a')['href'])
                            else:
                                player_bs_data[col['data-stat']] = [col.get_text()]
                                if col['data-stat'] == 'date_game':
                                    player_bs_data['game_id'] = [col.find('a')['href']]

            game_logs[year] = player_bs_data
            
    return game_logs, player_info 



def gather_player_links(years):
    '''
    Given a list of years in string, this function finds 
    all players who played within those years
    '''
    
    url = 'https://www.basketball-reference.com/players/'
    all_links = []
    years = list(map(int, years)) 
    
    for letter in list(ascii_lowercase):
        players = urllib.request.urlopen(url + letter)
        players_html = BeautifulSoup(players, 'html.parser')
        for link in players_html.findAll('tr'):
            try:
                if link.find('a') is not None:
                    player_link = link.find('a')['href']
                for cols in link.findAll('td'):
                    if cols['data-stat'] == 'year_min':
                        min_year = int(cols.get_text())
                    elif cols['data-stat'] == 'year_max':
                        max_year = int(cols.get_text())
                        break
                years_range1 = list(range(min(years), max(years)+1))
                years_range2 = list(range(min_year, max_year+1))
                if any(item in years_range1 for item in years_range2):
                    all_links.append(player_link)
            except:
                continue
    
    return all_links

def append_player_data_by_year(game_logs, player_info, final_data_frames):
    '''
    Adds game log and physical player data belonging to a single player, to 
    dictionary of data frames of all game log data split by year. Updates in place!
    '''
    
    for years in game_logs.keys():
        gl_data = pd.DataFrame.from_dict(game_logs[years])
        for items in player_info.items():
            gl_data[items[0]] = items[1]
        if years not in final_data_frames.keys():
            final_data_frames[years] = gl_data
            continue
        final_data_frames[years] = final_data_frames[years].append(gl_data)
        
    return
    