from bs_scrape_funcs import gather_player_links, append_player_data, scrape_player
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
	    f = open("full_player_stats.pkl","rb")
	    full_player_stats = pickle.load(f)
	    f.close()
	except FileNotFoundError:
	    print("Game Logs already pulled doesn't exist, starting pull from beginning")
	    full_player_stats = defaultdict(list)
	    
	for link in all_player_links:
	    
	    # will only pull if link is not in links already pulled
	    if link not in pulled_links:
	        count += 1
	        full_link = 'https://www.basketball-reference.com' + link
	        player_info, player_dict = scrape_player(full_link, years)
	        full_player_stats = append_player_data(player_dict, player_info, full_player_stats)
	        
	        # saves dictionary everytime a player is added
	        f = open("full_player_stats.pkl","wb")
	        pickle.dump(full_player_stats,f)
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
    
	df = pd.DataFrame.from_dict(full_player_stats)
	df.to_csv('data/full_player_stats.csv')