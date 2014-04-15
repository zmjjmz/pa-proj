import random
import pickle
import os
import glob
import sys
import math

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
    self.pop = {i:generator() for i in range(self.pop_size)}

  def write_individual(self, indv, indv_id):
    """ Writes the information for an individual to a file indv_id.enc """
    file_name = 'indv_%d.enc' % (indv_id)
    dir_path = os.path.join('trial%d' % (self.trial_num), 'gen%d' % (self.cur_gen))
    if not os.path.exists(dir_path):
      os.makedirs(dir_path)                                  # create directory [current_path]/trialk/genn
    output = open(os.path.join(dir_path, file_name), 'wb') # makes file file_name

    pickle.dump(indv, output)
    output.close();

  def read_individual(self, indv, indv_id):
    """ Reads the information for an indivdial from the file indv_id.enc """
    dir_path = os.path.join('trial%d' % (self.trial_num), 'gen%d' % (self.cur_gen))
    pkl_file = open(os.path.join(dir_path, 'indv_%d.enc' % (indv_id)), 'rb')
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

  def read_fitnesses(self):
    """ Goes through all of the {indv_id}.fit in trial/gen/ and reads them into a dict of {indv_id:fit} """
    fitness_files = glob.glob("trial%d/gen%d/*.fit" % (self.trial_num, self.cur_gen))
    fitness_dict = {}
    for fitness_file in fitness_files:
      with open(fitness_file, 'r') as fo: # it's good practice to use the with keyword -- it handles closing the file object for you
        fitness = float(fo.read())
      indv_id = int(fitness_file.split('/')[-1].split('.')[-1])
      fitness_dict[indv_id] = fitness

    return fitness_dict




  def get_fitnesses(self, fitness_mode):
    """ Goes through every individual in the population and tests their fitness, storing information (i.e. individuals, results) in trial_num/cur_gen """
    # So for every individual in the population, we go through and add the call to Unity to the multiprocessing queue

    # Read the fitnesses in once it's all done. Each individual will have their fitness in <ind>.fit, where the individual is stored in <ind>.enc
    return self.read_fitnesses()

  def run(self, n_generations):
    """ Runs the evolutionary procedure for n_generations """
    while(self.cur_gen <= self.n_generations)
      for indv_id, indv in self.pop.items():
        self.write_individual(self, indv, indv_id)
      self.fitnesses = self.get_fitnesses()
      best_indv = sorted(fitness_dict.values(), key=lambda x: -x[1])[:self.k]
      self.copulate(best_indv)
      self.cur_gen += 1


  def start(self, trial_num, n_generations):
    """ Runs through the whole process """
    # Build in ability to recover
    self.trial_num = trial_num
    try:
      # Check if the trial folder exists, and if it does find the highest gen and restart it (from the previous one)
      if os.path.isdir("trial%d" % (trial_num)):
        # how to find highest gen? not sure if this is right - Ian
        # Good start, fixed it. Never heard of the glob module before. Never sort something then take the last element -- that's what max is for
        # sorted is O(nlogn), max is O(n)
        # If you consider us having something like trial4/gen40 vs trial4/gen5, just taking the last elt will choose the latter -- which is wrong.
        # thus we can instead map this function which pulls out the gen number over the glob results, and then take the max.
        highest_gen = max(map(lambda x: int(x.split('/')[3:]), glob.glob("trial%d/gen*" % (trial_num))))
        # Go back one generation and try again from there. This is because we might have failed on some individual m << n, so that could fuck up everything
        # We will however not recompute all the fitnesses.
        self.cur_gen = highest_gen - 1
        # Read in the population
        for path in glob.glob("trial%d/gen%s/*.enc" % (self.trial_num, highest_gen)):
          indv = pickle.load(path)
          self.pop.append(indv)
        # This is essentially the second part of the run() function
        self.fitnesses = self.read_fitnesses()
        best_indv = sorted(fitness_dict.values(), key=lambda x: -x[1])[:self.k]

        self.copulate(best_indv)
        self.cur_gen += 1
        self.run(n_generations - highest_gen)
      # Otherwise start from the top, generate a population
      else:
        self.generate_pop()
        self.cur_gen = 0
        self.run(n_generations)

        # Figure out the fitnesses of the population by spawning processes in a queue
        fitness_dict = self.get_fitnesses("max_distance")
        # Move this into using the SortedCollections recipe http://code.activestate.com/recipes/577197-sortedcollection/
        # if it proves to be too slow. Probably won't be an issue
        best_indv = sorted(fitness_dict.values(), key=lambda x: -x[1])[:self.k]

        self.copulate(best_indv)

    except:
      error = sys.exc_info()[0]
      print("Trial %d: Caught error %s on generation %d, dumping to %s/trial%d/dump.pickle" % (self.trial_num, error, self.cur_gen, os.path.abspath('.'), self.trial_num)
    finally:
      self.dump()

