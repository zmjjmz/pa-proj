import random
import cpickle as pickle
import os

# This runs continuously, controlling the whole evolutionary process
class evolutionary_process:
  def __init__(self, pop_size, generations, generator, pop=None, k=2):
    """ Takes population size, number of generations, and a function to generate individuals """
    self.pop_size = pop_size
    self.generations = generations
    self.cur_gen = 0
    self.k = k
    self.pop = [] if pop == None else pop
    self.generator = generator

  def generate_pop(self):
    """ Generates pop_size individuals, separate from __init__ to allow 'warm starting' """
    self.pop = [generator() for i in range(self.pop)]

  def write_individual(self, indv, indv_id):
    """ Writes the information for an individual to a file indv_id.enc """
    file_name = "indv_%d.enc" % (indv_id)
    dir_path = os.path.join("trial%d" % (self.k), "gen%d" % (self.cur_gen))  # will return 'feed/address'
    os.makedirs(dir_path)                             # create directory [current_path]/feed/address
    output = open(os.path.join(dir_path, file_name), 'wb')
    pickle.dump(indv, output)
    pass

  def read_individual(self, indv, indv_id):
    """ Reads the information for an indivdial from the file indv_id.enc """
    pass

  def copulate(self, best_indv):
    """ Given a list of best individuals, evolves them together through combination & mutation to produce a new population of pop_size """
    pass

  def dump(self):
    """ In case anything goes wrong, dump everything to files """
    pass

  def get_fitnesses(self, fitness_mode):
    """ Goes through every individual in the population and tests their fitness, storing information (i.e. individuals, results) in trial_num/cur_gen """
    pass

  def run(self, trial_num):
    """ Runs through the whole process """
    # Build in ability to recover
    # Check if the trial folder exists, and if it does find the highest gen and restart it (from the previous one)

    # Read in the population

    # Otherwise start from the top, generate a population

    # Figure out the fitnesses of the population by spawning processes in a queue

    # Read the fitnesses in once it's all done. Each individual will have their fitness in <ind>.fit, where the individual is stored in <ind>.enc

    # Once this is done, find the best k individuals and have them copulate to produce the next generation

    pass





