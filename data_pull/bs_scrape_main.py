from bs_scrape_funcs import gather_player_links, append_player_data_by_year, scrape_player
from collections import defaultdict
import time
import pandas as pd
import os
import pickle

if __name__ == "__main__":

	f = open('years_to_obtain.txt','r')
	years = f.read().split('\n')
	f.close()

	all_player_links = gather_player_links(years)

	all_game_ids = set()
	count = 0

	# Attempts to open pulled links and game logs by year.
	# if it doesn't exist, start pull from start
	try:
	    f = open('pulled_links.txt','r')
	    pulled_links = f.read().split('\n')
	    f.close()
	except FileNotFoundError:
	    print("Pulled Links file doesn't exist, starting pull from beginning")
	    pulled_links = []
	    
	try:
	    f = open("game_logs_by_year.pkl","rb")
	    game_logs_by_year = pickle.load(f)
	    f.close()
	except FileNotFoundError:
	    print("Game Logs already pulled doesn't exist, starting pull from beginning")
	    game_logs_by_year = defaultdict(pd.core.frame.DataFrame)
	    
	for link in all_player_links:
	    
	    # will only pull if link is not in links already pulled
	    if link not in pulled_links:
	        count += 1
	        full_link = 'https://www.basketball-reference.com' + link
	        game_logs, player_info = scrape_player(full_link, years)
	        append_player_data_by_year(game_logs, player_info, game_logs_by_year)
	        
	        # saves dictionary everytime a player is added
	        f = open("game_logs_by_year.pkl","wb")
	        pickle.dump(game_logs_by_year,f)
	        f.close()
	        
	        # updates pulled links
	        with open('pulled_links.txt', 'a+') as f:
	            f.write("%s\n" % link)
	        f.close()
	    
	    # Stops for 10 seconds for every 50 players pulled
	    if count == 50:
	        time.sleep(10)
	        count = 0

	# saves box score data into csv files and makes
	# list of game links (game_id) that we want to query
	all_game_ids = set()
	if not os.path.isdir('data'):
	    os.mkdir('data')
	for year, df in game_logs_by_year.items():
	    save_name = 'data/box_score_data_' + str(year) + '.csv'
	    all_game_ids = all_game_ids | set(df['game_id'])
	    df.to_csv(save_name)

	# Saves all game_ids / game links to a text
	# file to pull of play by play data.
	with open('gamelinks.txt', 'w') as f:
	    for link in list(all_game_ids):
	        f.write("%s\n" % link)
	    f.close()