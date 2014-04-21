import random
import pickle
import json
import os
import glob
import sys
import math
import multiprocessing
from cpg import CPGFactory


# This runs continuously, controlling the whole evolutionary process
class evolutionary_process:
  def __init__(self, pop_size, factory, pop=None, k=2, mutation_prob=0.5, crossover_prob=[0.5,0.5]):
    """ Takes population size, number of generations, and a function to generate individuals """
    self.factory = factory # used to make the individuals randomly
    self.pop_size = pop_size
    self.cpus = multiprocessing.cpu_count()
    # specifies which indv_ids each process should run on
    self.proc_bounds = [(i,(i+int(self.pop_size/self.cpus))) if i != self.cpus else (i,(i+self.pop_size)) for i in range(0,self.pop_size,int(self.pop_size/self.cpus))]
    self.cur_gen = 0
    self.k = k
    self.pop = [] if pop == None else pop
    self.generator = generator

  def generate_pop(self):
    """ Generates pop_size individuals, separate from __init__ to allow 'warm starting' """
    self.pop = {str(i):self.factory.make(i) for i in range(self.pop_size)}

  def write_individual(self, indv):
    """ Writes the information for an individual to a file indv_id.enc """
    indv_id = indv['ident']
    file_name = 'indv_%s.enc' % (indv_id)
    dir_path = os.path.join('trial%d' % (self.trial_num), 'gen%d' % (self.cur_gen))
    if not os.path.exists(dir_path):
      os.makedirs(dir_path)                                  # create directory [current_path]/trialk/genn
    output = open(os.path.join(dir_path, file_name), 'w') # makes file file_name
    json.dump(indv, output, default=list) # hack to get numpy arrays in there
    output.close()

  def copulate(self, best_indv):
    """ Given a list of best individuals, evolves them together through combination & mutation to produce a new population of pop_size """
    # We'll use factory.mix(best_indv, ident) for ident in range(pop), with mutation probabilities and crossover probabilities set at init
    new_pop = {}
    for indv_id in range(self.pop_size):
      new_pop[indv_id] = self.factory.mix(best_indv, indv_id)

    self.pop = new_pop


  def dump(self):
    """ In case anything goes wrong, dump everything to files """
    dump_file = open(os.path.join("trial%d" % (self.trial_num), "dump.pickle"), "wb")
    pickle.dump(self, dump_file)
    dump_file.close()

  def read_fitnesses(self):
    """ Goes through all of the {indv_id}.fit in trial/gen/ and reads them into a dict of {indv_id:fit} """
    #fitness_files = glob.glob("trial%d/gen%d/*.fit" % (self.trial_num, self.cur_gen))
    # we're going to have all of them in one JSON file for now
    fitness_dict = dict()
    for i in range(self.cpus):
      fitness_file = "trial%d/gen%d/total%d.fit" % (self.trial_num, self.cur_gen, i)
      with open(fitness_file, 'r') as fo: # it's good practice to use the with keyword -- it handles closing the file object for you
        fitness_dict.update(json.load(fo))
    return fitness_dict

  def get_fitnesses(self, fitness_mode):
    """ Goes through every individual in the population and tests their fitness, storing information (i.e. individuals, results) in trial_num/cur_gen """
    # So for every individual in the population, we go through and add the call to Unity to the multiprocessing queue
    commands = ['python dickaround.py %d %d %d %d %d' (self.trial_num, self.cur_gen, self.proc_bounds[cpu][0], self.proc_bounds[cpu][1], cpu) for cpu in range(self.cpus)]
    unities = multiprocessing.Pool(self.cpus)
    unities.map(os.system, commands)
    # Read the fitnesses in once it's all done. Each individual will have their fitness in <ind>.fit, where the individual is stored in <ind>.enc
    return self.read_fitnesses()

  def run(self, n_generations):
    """ Runs the evolutionary procedure for n_generations """
    while(self.cur_gen <= self.n_generations):
      for indv in self.pop.values():
        self.write_individual(indv)
      self.fitnesses = self.get_fitnesses()
      best_indv_ids = sorted(fitness_dict.keys(), key=lambda x: -fitness_dict[x])[:self.k]
      best_indv = [self.pop[indv_id] for indv_id in best_indv_ids]
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
          with open(path, 'rb') as fo: # easier than getting the id for read_individual from the file path
            indv = self.factory.deserialize(json.load(fo))
          self.pop[indv['ident']] = indv
        # This is essentially the second part of the run() function
        self.fitnesses = self.read_fitnesses()
        best_indv_ids = sorted(fitness_dict.keys(), key=lambda x: -fitness_dict[x])[:self.k]

        best_indv = [self.pop[indv_id] for indv_id in best_indv_ids]

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
        best_indv_ids = sorted(fitness_dict.keys(), key=lambda x: -fitness_dict[x])[:self.k]
        best_indv = [self.pop[indv_id] for indv_id in best_indv_ids]

        self.copulate(best_indv)

    except:
      error = sys.exc_info()[0]
      print("Trial %d: Caught error %s on generation %d, dumping to %s/trial%d/dump.pickle" % (self.trial_num, error, self.cur_gen, os.path.abspath('.'), self.trial_num))
      self.dump()


if __name__ == "__main__":
  cpgfact = CPGFactory(3)
  # for now we're gonna leave the population at 3
  evlvr = evolutionary_process(10, cpgfact)
  # for now we're gonna go with trial set to 1, 10 generations
  evlvr.start(1, 10)




