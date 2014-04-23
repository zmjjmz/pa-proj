import random
import time
import traceback
import pickle
import json
import os
import glob
import sys
import math
import multiprocessing
import gc
from cpg import CPGFactory


# This runs continuously, controlling the whole evolutionary process
class evolutionary_process:
  def __init__(self, pop_size, factory, pop=None, k=2, mutation_prob=0.5, crossover_prob=[0.5,0.5]):
    """ Takes population size, number of generations, and a function to generate individuals """
    self.factory = factory # used to make the individuals randomly
    self.pop_size = pop_size
    self.cpus = multiprocessing.cpu_count()
    # specifies which indv_ids each process should run on
    self.proc_bounds = [(i,(i+int(self.pop_size/self.cpus))) if ind < (self.cpus-1) else (i,self.pop_size) for ind, i in enumerate(range(0,self.pop_size,int(self.pop_size/self.cpus)))][:self.cpus]
    self.cur_gen = 0
    self.k = k
    self.pop = {} if pop == None else pop

  def generate_pop(self):
    """ Generates pop_size individuals, separate from __init__ to allow 'warm starting' """
    self.pop = {str(i):self.factory.make(i) for i in range(self.pop_size)}

  def write_individual(self, indv):
    """ Writes the information for an individual to a file indv_id.enc """
    indv_id = indv['ident']
    file_name = '%s.enc' % (indv_id)
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
      new_pop[str(indv_id)] = self.factory.mix(best_indv, indv_id)
    del self.pop
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
    fitness_dict = {}
    for i in range(self.cpus):
      fitness_file = "trial%d/gen%d/total%d.fit" % (self.trial_num, self.cur_gen, i)
      if not os.path.isfile(fitness_file): # in case of recovery scenario
        continue
      with open(fitness_file, 'r') as fo: # it's good practice to use the with keyword -- it handles closing the file object for you
        fitness_dict.update(json.load(fo))
    return fitness_dict

  def get_fitnesses(self, fitness_mode='max speed'):
    """ Goes through every individual in the population and tests their fitness, storing information (i.e. individuals, results) in trial_num/cur_gen """
    # So for every individual in the population, we go through and add the call to Unity to the multiprocessing queue
    print("Generation %d: Evaluating fitnesses" % self.cur_gen)
    commands = ['./distanceEvolver.x86_64 -batchmode %d %d %d %d %d' % (self.trial_num, self.cur_gen, self.proc_bounds[cpu][0], self.proc_bounds[cpu][1], cpu) for cpu in range(self.cpus)]
    unities = multiprocessing.Pool(self.cpus)
    print("finding fitnesses")
    unities.map(os.system, commands)
    print("done")
    del commands
    del unities
    return self.read_fitnesses()

  def run(self, n_generations):
    """ Runs the evolutionary procedure for n_generations """
    print("Running for %d generations from generation %d" % (n_generations - self.cur_gen, self.cur_gen))
    while(self.cur_gen < n_generations):
      for indv in self.pop.values():
        self.write_individual(indv)
      fitness_dict = self.get_fitnesses()
      best_indv_ids = sorted(fitness_dict.keys(), key=lambda x: -fitness_dict[x])[:self.k]
      print([fitness_dict[i] for i in best_indv_ids])
      print("Generation %d: Best fitness %d from individual %s" % (self.cur_gen, fitness_dict[best_indv_ids[0]], best_indv_ids[0]))
      best_indv = [self.pop[indv_id] for indv_id in best_indv_ids]
      del fitness_dict
      self.copulate(best_indv)
      self.cur_gen += 1

  def start(self, trial_num, n_generations):
    """ Runs through the whole process """
    # Build in ability to recover
    self.trial_num = trial_num
    if os.path.isdir("trial%d" % trial_num):
      highest_gen = max(map(lambda x: int(x.split('/')[-1][3:]), glob.glob("trial%d/gen*" % (trial_num))))
    else:
      highest_gen = 0
    try:
      # Check if the trial folder exists, and if it does find the highest gen and restart it (from the previous one)
      if highest_gen > 0:
        # Go back one generation and try again from there. This is because we might have failed on some individual m << n, so that could fuck up everything
        # We will however not recompute all the fitnesses.
        self.cur_gen = highest_gen - 1
        # Read in the population
        for path in glob.glob("trial%d/gen%s/*.enc" % (self.trial_num, highest_gen)):
          with open(path, 'r') as fo: # easier than getting the id for read_individual from the file path
            indv = self.factory.deserialize(json.load(fo))
          self.pop[indv['ident']] = indv
        # This is essentially the second part of the run() function
        fitness_dict = self.read_fitnesses()
        best_indv_ids = sorted(fitness_dict.keys(), key=lambda x: -fitness_dict[x])[:self.k]

        best_indv = [self.pop[indv_id] for indv_id in best_indv_ids]

        self.copulate(best_indv)
        self.cur_gen += 1
        self.run(n_generations)
      else:
        # Otherwise start from the top, generate a population
        self.generate_pop()
        self.cur_gen = 0
        self.run(n_generations)
    except:
      error = traceback.format_exc()
      print("Trial %d: Caught error %s on generation %d, dumping to %s/trial%d/dump.pickle" % (self.trial_num, error, self.cur_gen, os.path.abspath('.'), self.trial_num))
      self.dump()


if __name__ == "__main__":
  trial_num = int(sys.argv[1])
  generations = int(sys.argv[2])
  # smaller size for now
  cpgfact = CPGFactory(20)
  # for now we're gonna leave the population at 10
  evlvr = evolutionary_process(10, cpgfact)
  # for now we're gonna go with trial set to 1, 10 generations
  evlvr.start(trial_num, generations)




