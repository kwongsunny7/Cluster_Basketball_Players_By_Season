import pandas as pd
import re
import urllib
from bs4 import BeautifulSoup, Comment
from collections import defaultdict
from string import ascii_lowercase

def is_comment(element): 
    return isinstance(element, Comment)

def player_physical(player_html, link):
    '''
    Gathers player physical information,
    such as dominant hand, height, weight
    '''

    player_info = defaultdict(str)

    # Adds Player_id and player name to player physical information
    link_split = link.split('/')
    player_id = link_split[len(link_split)-1]
    player_id = player_id.replace('.html','') 
    player_name = player_html.find('title').get_text().split('|')[0].replace(' Stats','')
    player_info['player_id'] = player_id
    player_info['player_name'] = player_name

    for link in player_html.findAll('p'):
        html_txt = link.get_text()
        search = True
        if 'Position:' in html_txt and search == True:
            position_dom_hand = html_txt.split()
            shoots_index = position_dom_hand.index('Shoots:')
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

    return player_info

def scrape_player(link):
    '''
    Scrapes statistics for a single player, such as per-game, per possession
    and advanced statistics
    '''

    player_dict = defaultdict(list)
    
    player = urllib.request.urlopen(link)
    player_html = BeautifulSoup(player, 'html.parser')

    # Gathers player info
    player_info = player_physical(player_html, link)
    
    for table in player_html.findAll('table',{'id':'per_game'}):
        for row in table:
            try:
                for tr in row.findAll('tr',{'class':'full_table'}):
                    for col in tr:
                        player_dict[col['data-stat']].append(col.get_text())
            except AttributeError:
                pass

    # sets variables to skip for next tables to prevent unequal column lengths
    skip_vars = ['season', 'age', 'team_id', 'lg_id', 'pos', 'g', 
                    'gs','fg_pct','ft_pct','fg2_pct','fg3_pct','mp',
                'DUMMY1','DUMMY2','DUMMY3','DUMMY4','DUMMY', 'efg_pct']

    # List all table names
    table_names = ['all_per_minute', 'all_per_poss', 'all_advanced', 
                 'all_adj_shooting', 'all_pbp', 'all_shooting']

    for table_name in table_names:
        for div in player_html.findAll('div',{'id':table_name}):
            comment_to_soup = BeautifulSoup(div.find(text=is_comment) , 'html.parser')
            if table_name in ['all_pbp', 'all_adj_shooting']:
                all_rows = comment_to_soup.find('tbody').findAll('tr')
            else:
                all_rows = comment_to_soup.findAll('tr',{'class':'full_table'})         
            for tr in all_rows:
                try:
                    if not tr.attrs['class'] in [['light_text', 'partial_table'],
                    ['italic_text', 'partial_table']]:
                        for col in tr:
                            if col['data-stat'] not in skip_vars:
                                player_dict[col['data-stat']].append(col.get_text())
                except KeyError:
                        for col in tr:
                            if col['data-stat'] not in skip_vars:
                                player_dict[col['data-stat']].append(col.get_text())
            if table_name == "all_advanced":
                skip_vars.append('ts_pct')
    
    return player_info, player_dict


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

def append_player_data(player_dict, player_info, final_data_frames):
    '''
    Adds game log and physical player data belonging to a single player, to 
    dictionary of a single data frame. 
    '''
    times_to_add = len(player_dict['season'])
    
    for k,v in player_dict.items():
        final_data_frames[k].extend(v) 
    gl_data = pd.DataFrame.from_dict(player_dict)
    for _ in range(times_to_add):
        for items in player_info.items():
            final_data_frames[items[0]].append(items[1])
            
    return final_data_frames
    