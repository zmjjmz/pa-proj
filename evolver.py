import random
import cpickle as pickle
import os
import glob

# This runs continuously, controlling the whole evolutionary process
class evolutionary_process:
  def __init__(self, pop_size, generations, generator, trial_num, pop=None, k=2):
    """ Takes population size, number of generations, and a function to generate individuals """
    self.pop_size = pop_size
    self.generations = generations
    self.cur_gen = 0
    self.k = k
    self.pop = [] if pop == None else pop
    self.generator = generator
    self.trial_num = trial_num

  def generate_pop(self):
    """ Generates pop_size individuals, separate from __init__ to allow 'warm starting' """
    self.pop = [generator() for i in range(self.pop_size)]

  def write_individual(self, indv, indv_id):
    """ Writes the information for an individual to a file indv_id.enc """
    file_name = 'indv_%d.enc' % (indv_id)
    dir_path = os.path.join('trial%d' % (self.k), 'gen%d' % (self.cur_gen))
    os.makedirs(dir_path)                                  # create directory [current_path]/trialk/genn
    output = open(os.path.join(dir_path, file_name), 'wb') # makes file file_name
    
    pickle.dump(indv, output)
    output.close();

  def read_individual(self, indv, indv_id):
    """ Reads the information for an indivdial from the file indv_id.enc """
    pkl_file = open('indv_%d.enc' % (indv_id), 'rb')
    indiv = pickle.load(pkl_file)
    return indiv

  def copulate(self, best_indv):
    """ Given a list of best individuals, evolves them together through combination & mutation to produce a new population of pop_size """
    pass

  def dump(self):
    """ In case anything goes wrong, dump everything to files """
    dump_file = open(os.path.join("trial%d" % (self.trial_num), "dump.pickle"), "wb")
    pickle.dump(self, dump_file)
    dump_file.close()

  def get_fitnesses(self, fitness_mode):
    """ Goes through every individual in the population and tests their fitness, storing information (i.e. individuals, results) in trial_num/cur_gen """
    pass

  def run(self):
    """ Runs through the whole process """
    # Build in ability to recover    
    try:
      # Check if the trial folder exists, and if it does find the highest gen and restart it (from the previous one)
      if os.path.isdir("trial%d" % (trial_num)):
        # how to find highest gen? not sure if this is right - Ian
        highest_gen = sorted(glob("trial%d/gen*/" % (trial_num)))[-1]
        # Read in the population
        for path in glob("%s*.enc" % (highest_gen)):
          indv = pickle.load(path)
          pop.append(indv)
      # Otherwise start from the top, generate a population
      else:
        generate_pop()

      # Figure out the fitnesses of the population by spawning processes in a queue
      get_fitnesses("max_distance")
      # Read the fitnesses in once it's all done. Each individual will have their fitness in <ind>.fit, where the individual is stored in <ind>.enc
      
      # Once this is done, find the best k individuals and have them copulate to produce the next generation
    finally:
      dump()
