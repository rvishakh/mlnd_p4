import random
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator

class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env):
        super(LearningAgent, self).__init__(env)  # sets self.env = env, state = None, next_waypoint = None, and a default color
        self.color = 'red'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint
        # TODO: Initialize any additional variables here
	# Initialize all states to a large number to encourage the learning agent to discover the rewards for them
	self.qmatrix = [[10 for x in range(4)] for y in range(128)]
	self.current_state = 0

    def reset(self, destination=None):
        self.planner.route_to(destination)
        # TODO: Prepare for a new trip; reset any variables here, if required

    def conv_state_decimal(self, next_waypoint, inputs):
    	"""Assigns a numeric value to each state"""
	# Define a binary conversion for the states - use for light and traffic intersection 
	to_binary = {'red': '0', 'green': '1', None: '00', 'left': '10', 'right': '01', 'forward': '11'};

	# Create a binary state value and then convert it to a decimal value
	# Since the traffic on the right does not impact traffic rules, we can drop it from the Q-state matrix
	binary_state = to_binary[next_waypoint] + to_binary[inputs['light']] + to_binary[inputs['oncoming']] + to_binary[inputs['left']]
	current_state = int(binary_state, 2)

	return current_state


    def conv_action_decimal(self, action):
    	"""Assigns a numeric value to each action"""
	# Define a decimal conversion for the action
	action_state = {None: 0, 'left': 2, 'right': 1, 'forward': 3};

	return action_state[action]
	

    def update_qmatrix(self, reward, prev_waypoint, inputs, action):
    	"""Update the Q-matrix based on assigned reward"""
	alpha       = 0.4
	prev_state  = self.conv_state_decimal(prev_waypoint, inputs)
	prev_action = self.conv_action_decimal(action)

	# Disregard the reward of 12 given on reaching the destination
	# Use the negative rewards to learn (and avoid) traffic violations 
	# Use the smaller positive rewards to learn to follow the planner route
	if (reward < 3):
		if (self.qmatrix[prev_state][prev_action] < 10):	# Consecutive updates increment the state value
			self.qmatrix[prev_state][prev_action] = ((1 - alpha)* self.qmatrix[prev_state][prev_action]) + (alpha * reward)
		else:	# First execution of the state sets the state value 
			self.qmatrix[prev_state][prev_action] = alpha * reward

	print "Updated Q Matrix for State: %s Q-Values: %s" % (prev_state, self.qmatrix[prev_state])

    def learnt_action(self, inputs):
	# Define a conversion between the action and its index
	q_action = {0: None, 2: 'left', 1: 'right', 3: 'forward'};


	current_state = self.conv_state_decimal(self.next_waypoint, inputs)
	options       = self.qmatrix[current_state]
	max_q_value   = max(options)
	max_indices   = [i for i, j in enumerate(options) if j == max_q_value]

	# If multiple actions have the maximum q_value, pick one randomly
	# The random selection is needed initially since all states have the same value
	learnt_action = q_action[random.choice(max_indices)]

	print "state: %s, options: %s, max_q_value: %s, max_indices: %s learnt action: %s" % (current_state, options, max_q_value, max_indices, learnt_action)

	return learnt_action

    def random_action(self):
    	"""Function used to pick a random action for the agent before implementing Q-learning"""
	# Define a conversion between the action and its index
	q_action = {0: None, 2: 'left', 1: 'right', 3: 'forward'};

	random_action = q_action[random.choice([0, 1, 2, 3])]
	return random_action

    def update(self, t):
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
	prev_waypoint      = self.next_waypoint		   # store the waypoint for use in qmatrix update
        inputs 		   = self.env.sense(self)
        deadline 	   = self.env.get_deadline(self)
	current_state      = self.conv_state_decimal(self.next_waypoint, inputs)
	print "-----------------------------------"
	print "Current State: %s" % (current_state)

        # TODO: Update state
	self.state = self.get_state()
        
        # TODO: Select action according to your policy
        #action = self.random_action()
        action = self.learnt_action(inputs)

        # Execute action and get reward
        reward = self.env.act(self, action)

        # TODO: Learn policy based on state, action, reward
        self.update_qmatrix(reward, prev_waypoint, inputs, action) 

        print "LearningAgent.update(): deadline = {}, inputs = {}, action = {}, reward = {}".format(deadline, inputs, action, reward)  # [debug]

def run():
    """Run the agent for a finite number of trials."""

    # Set up environment and agent
    e = Environment()  				# create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent)  		# create agent
    e.set_primary_agent(a, enforce_deadline=False)  # set agent to track

    # Now simulate it
    sim = Simulator(e, update_delay=0.01)  	# reduce update_delay to speed up simulation
    sim.run(n_trials=100)  			# press Esc or close pygame window to quit

    print a.qmatrix				# print learnt q-matrix

if __name__ == '__main__':
    run()
