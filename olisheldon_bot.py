
import random
import numpy as np
from itertools import permutations

class Bot(object):

	def __init__(self):
		self.name = "olisheldon" # Put your id number her. String or integer will both work
		# Add your own variables here, if you want to. 

		# value variables
		self.targetvalue = 0
		self.increase_factor = 1.1
		self.decrease_factor = 0.75
		self.previous_bids = []
		self.aimed_score = 0
		self.regretfactor = 1.1
		self.regret = 1.1
		self.previous_bids = []
		self.bidded_with_intention = []
		self.tolerance = 0.1

		# collection variables
		self.advantage = False
		self.highbid = False

	# returns the sum of all agents budgets
	def total_budget(self, current_round, bots, game_type, winner_pays, artists_and_values, round_limit,
		starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid):
		total_budget = 0
		for bot in bots:
			total_budget += bot['budget']
		return total_budget

	# returns the total score available in the game
	def total_painting_value(self, current_round, bots, game_type, winner_pays, artists_and_values, round_limit,
		starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid):
		total = 0
		for i in range(current_round, round_limit):
			painting = painting_order[i]
			value = artists_and_values[painting]
			total += value
		return total

	# competition for the current painting on auction
	def painting_competition(self, current_round, bots, game_type, winner_pays, artists_and_values, round_limit,
		starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid):
		bot_required_paintings = self.all_bots_required_paintings(current_round, bots, game_type, winner_pays, artists_and_values, round_limit,
															starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid)
		competition_dict = {key:0 for key in artists_and_values.keys()}
		for bot in bot_required_paintings.keys():
			for item in bot_required_paintings[bot]:
				competition_dict[item] += 1
		return competition_dict

	# returns a dictionary with the required paintings of all agents
	def all_bots_required_paintings(self, current_round, bots, game_type, winner_pays, artists_and_values, round_limit,starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid):
		returndict = {}
		for bot in bots:
			paintings = bot['paintings']
			returndict[bot['bot_unique_id']] = self.required_paintings(paintings)
		return returndict

	# returns a nested dictionary with bots and their 'importance' of the painting currently on auction
	def painting_importance_collection(self, current_round, bots, game_type, winner_pays, artists_and_values, round_limit,starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid):
		# returns dict of bots with score for how important next painting is
		roundnum_dict = {}
		current_rounds_til_terminate = self.rounds_til_earliest_terminate(current_round, bots, game_type, winner_pays, artists_and_values, round_limit,starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid)
		current_round = current_round + 1
		# assume bot won the painting of the current round
		for bot in bots:
			bot['paintings'][painting_order[current_round]] += 1
		next_round_rounds_til_terminate = self.rounds_til_earliest_terminate(current_round, bots, game_type, winner_pays, artists_and_values, round_limit,starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid)
		for key in current_rounds_til_terminate:
			roundnum_dict[key] =  next_round_rounds_til_terminate[key] + 1 - current_rounds_til_terminate[key] # +1 to make sure it is strictly positive.
		return roundnum_dict

	# returns a dictionary with agents as keys and smallest number of rounds required to terminate the game for that agent
	def rounds_til_earliest_terminate(self, current_round, bots, game_type, winner_pays, artists_and_values, round_limit,starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid):
		# returns dict of bots with number of rounds til they could potentially terminate
		roundnum_dict = {unique_id:0 for unique_id in [bot['bot_unique_id'] for bot in bots]}
		if game_type == 'value':
			return 200 - current_round
		else:
			for bot in bots:
				paintings = bot['paintings'].copy()
				i=0
				# loop until number of rounds til earliest completion is found
				while 0 == roundnum_dict[bot['bot_unique_id']]:
					if painting_order[current_round+i] in self.required_paintings(paintings):
						paintings[painting_order[current_round+i]] += 1
					if len(self.required_paintings(paintings)) == 0:
						roundnum_dict[bot['bot_unique_id']] = i
						break
					i += 1
			return roundnum_dict

	# returns the L1 distance of a set of paintings and any target collection. a higher score is closer to a terminating bundle
	def bot_collection_l1value(self,paintings):
		perms = permutations([num_paintings for artist, num_paintings in paintings.items()])
		return 8 - min([np.linalg.norm(np.maximum(np.zeros(4),np.array([3,3,1,1])-np.array(perm)), ord=1) for perm in perms])

	# returns a list of paintings that improves a bundle of paintings
	def required_paintings(self,paintings):
		#returns set of paintings an agent wants
		perms = permutations([num_paintings for artist, num_paintings in paintings.items()])
		if (1,1,3,3) in perms:
			return set()
		returnset = set()
		for painting in paintings.keys():
			temp_paintings = paintings.copy()
			temp_paintings[painting]+=1
			if self.bot_collection_l1value(temp_paintings) > self.bot_collection_l1value(paintings):
				returnset.add(painting)
		return returnset

	# returns a dictionary of paintings with the average price the painting has sold for
	def total_painting_avg_prices(self,current_round, bots, game_type, winner_pays, artists_and_values, round_limit,starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid):
		paintings_and_paid = {painting:0 for painting in artists_and_values}
		painting_avg_price = {}
		for i in range(len(amounts_paid)):
			amount_paid = amounts_paid[i]
			paintings_and_paid[painting_order[i]] += amount_paid
		for painting in paintings_and_paid:
			count = painting_order[:current_round].count(painting)
			if count != 0:
				painting_avg_price[painting] = paintings_and_paid[painting]/count
			else:  
				painting_avg_price[painting] = 0
		return painting_avg_price
		
	def cap_budget_distribution(self,current_round, bots, game_type, winner_pays, artists_and_values, round_limit, starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid):
		tpv = self.total_painting_value(current_round, bots, game_type, winner_pays, artists_and_values, round_limit, starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid)
		return {painting:artists_and_values[painting]*tpv/len(bots)/200 for painting in artists_and_values}

	# returns list of rounds in which if all are won, target_score is guaranteed.
	def least_paintings_path(self,target_score, current_round, bots, game_type, winner_pays, artists_and_values, round_limit,starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid):
		tot_value = my_bot_details['score']
		upcoming_paintings = painting_order[current_round:]
		ordered_paintings = []
		round_buy_markers = []
		for painting in ['Picasso','Van Gogh','Rembrandt','Da Vinci']: #paintings ordered by value
			for i in range(len(upcoming_paintings)):
				if target_score < 0:
					break
				elif upcoming_paintings[i] == painting:
					round_buy_markers.append(i+current_round)
					target_score -= artists_and_values[painting]
		return sorted(round_buy_markers)

	# returns upcoming score available in auction
	def total_upcoming_painting_value(self,current_round, bots, game_type, winner_pays, artists_and_values, round_limit,
		starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid):
		total = 0
		for i in range(current_round,round_limit):
			painting = painting_order[i]
			value = artists_and_values[painting]
			total += value
		return total



	def get_bid_for_collection_game(self, current_round, bots, game_type, winner_pays, artists_and_values, round_limit,
		starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid):
		"""Strategy for collection type games. 

		Parameters:
		current_round(int): 			The current round of the auction game
		bots(dict): 					A dictionary holding the details of all of the bots in the auction
										For each bot, you are given these details:
										bot_name(str):		The bot's name
										bot_unique_id(str):	A unique id for this bot
										paintings(dict):	A dict of the paintings won so far by this bot
										budget(int):		How much budget this bot has left
										score(int):			Current value of paintings (for value game)
		game_type(str): 				Will be "collection" for collection type games
		winner_pays(int):				Rank of bid that winner plays. 1 is 1st price auction. 2 is 2nd price auction.
		artists_and_values(dict):		A dictionary of the artist names and the painting value to the score (for value games)
		round_limit(int):				Total number of rounds in the game - will always be 200
		starting_budget(int):			How much budget each bot started with - will always be 1001
		painting_order(list str):		A list of the full painting order
		target_collection(list int):	A list of the type of collection required to win, for collection games - will always be [3,3,1,1]
										[5] means that you need 5 of any one type of painting
										[4,2] means you need 4 of one type of painting and 2 of another
										[3,2,1] means you need 3 of one type of painting, 2 of another, and 1 of another
		my_bot_details(dict):			Your bot details. Same as in the bots dict, but just your bot. 
										Includes your current paintings, current score and current budget
		current_painting(str):			The artist of the current painting that is being bid on
		winner_ids(list str):			A list of the ids of the winners of each round so far 
		amounts_paid(list int):			List of amounts paid for paintings in the rounds played so far 

		Returns:
		int:Your bid. Return your bid for this round. 
		"""

		# WRITE YOUR STRATEGY HERE FOR COLLECTION TYPE GAMES - FIRST TO COMPLETE A FULL COLLECTION
		
		if current_round > 0 and winner_ids[current_round-1] == my_bot_details['bot_unique_id'] and amounts_paid[current_round-1] == 1:
			self.advantage = True

		my_budget = my_bot_details["budget"]
		my_paintings = my_bot_details['paintings']

		print('budget:',my_budget,', advantage:',self.advantage,', highbid:',self.highbid)

		# count paintings i have
		num_paintings = 0
		for painting in my_paintings.keys():
			num_paintings += my_paintings[painting]
		
		rounds_til_terminate = self.rounds_til_earliest_terminate(current_round, bots, game_type, winner_pays, artists_and_values, round_limit,starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid)
		painting_importance = self.painting_importance_collection(current_round, bots, game_type, winner_pays, artists_and_values, round_limit,starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid)


		print('rounds til earliest terminate',rounds_til_terminate)
		print('painting importance',painting_importance)

		current_competition = self.painting_competition(current_round, bots, game_type, winner_pays, artists_and_values, round_limit,starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid)
		
		print('required paintings:',self.required_paintings(my_paintings))

		# if the next painting terminates the game with me as a winner, use all budget
		if rounds_til_terminate[my_bot_details['bot_unique_id']] == 0:
			bid_amount = my_budget
			return bid_amount


		# if an opponent is about to win and i have excess budget, try to outbid them even if it does not improve my position
		for bot in bots:
			if rounds_til_terminate[bot['bot_unique_id']] == 0 and self.advantage == True:
				return bot['budget'] + 1


		print('My collection:',my_paintings)
		# if painting improves my position
		if current_painting in self.required_paintings(my_paintings):
			print('I want this painting')
			if self.advantage == True: # need to check if i have managed to get a painting for a price of 1.
				print('I have exploited somebody previously')
				bid_amount = 127 # guarantees i win
			elif current_competition[current_painting] == 1:
				print('I detect no competition')
				bid_amount = 1
			elif self.highbid == False and painting_importance[my_bot_details['bot_unique_id']] > len(bots):
					print('###########################################################################')
					print('I AM BIDDING 126')
					print('###########################################################################')
					bid_amount = 126
					self.highbid = True
			else:
				bid_amount = 125
		elif current_competition[current_painting] == 1: #i am not interested in this painting, but denying another player could be a good strategy and i have saved funds to achieve this.
			if self.advantage == True:
				print('I am trying to deny another player')
				bid_amount = 2 # i have extra budget, so i can afford to try to deny anonther agent
			else:
				print('I see the opportunity to deny another player, but I do not have a budget advantage :(')
				bid_amount = 0
		else: # do not want this painting under any circumstance
			print('Not interested')
			bid_amount = 0

		
		return bid_amount

	def get_bid_for_value_game(self, current_round, bots, game_type, winner_pays, artists_and_values, round_limit,
		starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid):
		"""Strategy for value type games. 

		Parameters:
		current_round(int): 			The current round of the auction game
		bots(dict): 					A dictionary holding the details of all of the bots in the auction
										For each bot, you are given these details:
										bot_name(str):		The bot's name
										bot_unique_id(str):	A unique id for this bot
										paintings(dict):	A dict of the paintings won so far by this bot
										budget(int):		How much budget this bot has left
										score(int):			Current value of paintings (for value game)
		game_type(str): 				Will be either "collection" or "value", the two types of games we will play
		winner_pays(int):				Rank of bid that winner plays. 1 is 1st price auction. 2 is 2nd price auction.
		artists_and_values(dict):		A dictionary of the artist names and the painting value to the score (for value games)
		round_limit(int):				Total number of rounds in the game
		starting_budget(int):			How much budget each bot started with
		painting_order(list str):		A list of the full painting order
		target_collection(list int):	A list of the type of collection required to win, for collection games
										[5] means that you need 5 of any one type of painting
										[4,2] means you need 4 of one type of painting and 2 of another
										[3,2,1] means you need 3 of one type of painting, 2 of another, and 1 of another
		my_bot_details(dict):			Your bot details. Same as in the bots dict, but just your bot. 
										Includes your current paintings, current score and current budget
		current_painting(str):			The artist of the current painting that is being bid on
		winner_ids(list str):			A list of the ids of the winners of each round so far 
		amounts_paid(list int):			List of amounts paid for paintings in the rounds played so far 

		Returns:
		int:Your bid. Return your bid for this round. 
		"""
		# WRITE YOUR STRATEGY HERE FOR VALUE GAMES - MOST VALUABLE PAINTINGS WON WINS

		
		total_score = self.total_painting_value(current_round, bots, game_type, winner_pays, artists_and_values, round_limit, starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid)
		current_budget = my_bot_details['budget']		
		current_score = my_bot_details['score']
		avg_painting_prices = self.total_painting_avg_prices(current_round, bots, game_type, winner_pays, artists_and_values, round_limit, starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid)
		
		highest_score_cap = np.floor(total_score/1.9)+1 # slightly higher for the case when len(room) == 2

		lowest_score_cap = np.floor(total_score/len(bots))+1

		# Initialized aimed_score to highest_score_cap at the beginning of the game (assume rational play intially)
		if self.aimed_score == 0:
			self.aimed_score = highest_score_cap
		aimed_score = self.aimed_score
		
		# if i was not pursuing the previous painting, 
		if current_round > 0 and self.bidded_with_intention[current_round-1] == 1:
			# if i won the previous round, increase my bid
			if winner_ids[current_round-1] == my_bot_details['bot_unique_id']:
				aimed_score *= self.increase_factor
				# do not let my bot aim higher than highest_score_cap
				if aimed_score > highest_score_cap:
					aimed_score = highest_score_cap
			else:
				# if i lost the previous round, decrease my bid.
				aimed_score *= self.decrease_factor
				if aimed_score < lowest_score_cap:
					aimed_score = lowest_score_cap
		

		# in case I have overcome the aimed_score, increase the aimed_score. this will decrease my bids even further to exploit irrational play even more
		if current_score >= aimed_score:
			aimed_score *= self.increase_factor
			# dont let the aimed_score go above highest_score_cap
			if aimed_score > highest_score_cap:
				aimed_score = highest_score_cap

		self.aimed_score = aimed_score


		# increase regret and play more aggressively if i failed to win a painting i intended to win
		if current_round > 0 and self.bidded_with_intention[current_round-1] == 1:
			if winner_ids[current_round-1] == my_bot_details['bot_unique_id']:
				self.regret = 1.1
			else:
				self.regret *= self.regretfactor

		#returns list of rounds of minimal length to achieve aimed_score
		rounds_required_to_achieve_target = self.least_paintings_path(aimed_score, current_round, bots, game_type, winner_pays, artists_and_values, round_limit,starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid)
		
		# is the current painting regarded as very important to winning
		if current_round in rounds_required_to_achieve_target and aimed_score-current_score != 0:
			item_value = np.floor((artists_and_values[current_painting]/(aimed_score-current_score))*current_budget)
			self.bidded_with_intention.append(1)
			bid_amount = np.floor((item_value + 1) * self.regret)
		else:
			self.bidded_with_intention.append(0)
			if current_round > 0 and aimed_score-current_score != 0:
				item_value = np.floor((artists_and_values[current_painting]/(aimed_score-current_score))*current_budget)
				bid_amount = np.floor(self.tolerance*(item_value + 1))
			else:
				bid_amount = 0


		# towards the end of the game, play conservatively with remaining budget
		
		if my_bot_details['budget'] < 500/len(bots)+100:
			remaining_score = self.total_upcoming_painting_value(current_round, bots, game_type, winner_pays, artists_and_values, round_limit,starting_budget, painting_order, target_collection, my_bot_details, current_painting, winner_ids, amounts_paid)
			bid_amount = artists_and_values[current_painting]/remaining_score*my_bot_details['budget']
		
		#always bid all of remaining budget in final round
		if current_round == 199:
			print('round 200')
			bid_amount = my_bot_details['budget']
		self.previous_bids.append(bid_amount)

		return bid_amount