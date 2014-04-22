import numpy as np
import bisect

class CPGFactory:
  def __init__(self, n): # this is equivalent to starting a random one
    """ Only changeable constraint on the factory is the number of oscillators """
    self.n = n
    # From table S1 in the supplemental materials
    # each c parameters is [body,limb]
    self.cv0 = [0.3, 0.0]
    self.cv1 = [0.2, 0.2]
    self.cR0 = [0.196,0.131]
    self.cR1 = [0.065,0.131]
    #[[dbodylow,dbodyhigh],[dlimblow,dlimbhigh]]
    self.d_params = [[1,5],[1,3]]
    # which oscillators are limb oscillators and which ones are body oscillators is pretty constant
    n_body = n - 4
    self.osc_class = [0 if i < n_body else 1 for i in range(self.n)] # 0 for body oscillator, 1 for limb oscillator
    # list of keys that can be mutated during evolution
    self.evolvables = ['w', 'phi', 'a', 'gsl', 'gsh', 'gb1', 'gb2', 'theta', 'ampl', 'ampl_dot']
    self.scalars = set(['gsl', 'gsh', 'gb1', 'gb2'])
    self.shapes = {'w':(n,n),
        'phi':(n,n),
        'a':n,
        'theta':n,
        'ampl':n,
        'ampl_dot':n}
    self.sizes = {'w':n*n,
        'phi':n*n,
        'a':n,
        'theta':n,
        'ampl':n,
        'ampl_dot':n}

  def deserialize(self, indv):
    """ Converts things back into numpy """
    for key in indv:
      if key in self.evolvables and not key in self.scalars:
        if not isinstance(indv[key], np.ndarray):
          indv[key] = np.array(indv[key])

    return indv



  def make(self, ident):
    """ Randomly generates the parameters for a CPG """
    CPG = dict()
    CPG['ident'] = str(ident)
    # will not be updated during simulation
    CPG['w'] = np.random.rand(self.n, self.n) # (n,n)
    CPG['phi'] = np.random.rand(self.n, self.n) # (n,n)
    CPG['a'] = np.random.rand(self.n) # (n)
    CPG['gsl'] = np.random.rand() # scalar
    CPG['gsh'] = np.random.rand() # scalar
    CPG['gb1'] = np.random.rand() # scalar
    CPG['gb2'] = np.random.rand() # scalar
    # low (sub-linear) slope, high (supra-linear) slope, bound 1, bound 2
    # angles within bound 1 and bound 2 are considered 'swing' angles.
    # Initial vectors, will be updated as simulation goes
    # the initial values of these will be determined by evolution. Not sure if that's the best idea
    CPG['theta'] = np.random.rand(self.n) # (n)
    CPG['ampl'] = np.random.rand(self.n) # (n)
    CPG['ampl_dot'] = np.random.rand(self.n) # (n)

    CPG = self._set_constants(CPG)

    return CPG


  def _set_constants(self, CPG):
    # constants
    CPG['n'] = self.n
    CPG['cv0'] = self.cv0
    CPG['cv1'] = self.cv1
    CPG['cR0'] = self.cR0
    CPG['cR1'] = self.cR1
    CPG['d_params'] = self.d_params
    CPG['osc_class'] = self.osc_class

    return CPG

  def cumulative_sum(lis):
    """ Because you can't refer to the current list in a list comprehension """
    new_list = []
    for i in range(len(lis)):
      if i == 0:
        new_list.append(lis[i])
      else:
        new_list.append(new_list[i-1] + lis[i])
    return new_list

  def safe_rand():
    """ Gets a random number, but makes sure it's not 1 """
    rand_n = np.random.rand()
    if rand_n == float(1):
      rand_n -= 1e-10
    return rand_n

  def mix(self, cpgs, ident, method='avg', mutation_prob=0.5, crossover_prob=[0.5, 0.5]):
    """ Takes a list of cpgs (sorted from lowest fitness to highest) and mixes them into one.
    Note that crossover_prob is assumed to be sorted from lowest to highest and must sum to 1 """
    # Available methods:
    # note that mutation means selecting a new random scalar for a particular value
    # avg -- takes the average of all of the keys in self.evolvables and then goes through all of their values and chooses whether or not to mutate them by mutation_prob
    # crossover -- goes through all of the values and chooses from the nth cpg in cpgs with probability crossover_prob[n], then mutates them
    # defaults to choosing from the first two cpgs with equal probability

    n_cpgs = float(len(cpgs))


    new_CPG = dict()
    new_CPG['ident'] = str(ident)
    new_CPG = self._set_constants(new_CPG)

    if method == 'avg':
      for key in self.evolvables:
        avg_params = sum([cpg[key] for cpg in cpgs]) / n_cpgs
        new_CPG[key] = avg_params

    if method == 'crossover':
      # assume the current crossover_prob apply to cpgs[:len(crossover_prob)]
      # anything past that can be thrown out
      cpgs = cpgs[len(cpgs) - len(crossover_prob):]
      cdf = cumulative_sum(crossover_prob)
      choose_cpg = lambda rand: cpgs[bisect.bisect(cdf, rand)] # bisect will return the index of the value to the right of the given number in the sorted list
      # Now go through the keys
      for key in self.evolvables:
        if key in self.scalars:
          # then we'll just choose the cpg
          new_CPG[key] = choose_cpg(safe_rand())[key]
        else:
          new_CPG[key] = np.zeros(self.shapes[key])
          for param in range(self.sizes[key]):
            # Since CPGs that are read in don't have their lists in numpy.ndarray form
            this_cpg = choose_cpg(safe_rand())
            if not isinstance(this_cpg[key], np.ndarray):
              this_cpg[key] = np.array(this_cpg[key])
            new_CPG[key].flat[param] = choose_cpg(safe_rand())[key].flat[param]

    # mutate step
    for key in self.evolvables:
      if key in self.scalars:
        if np.random.rand() <= mutation_prob:
          new_CPG[key] = new_CPG[key] * np.random.rand()
      else:
        for param in range(self.sizes[key]):
          if np.random.rand() <= mutation_prob:
            new_CPG[key].flat[param] = new_CPG[key].flat[param] * np.random.rand()
    # That's all folks!
    return new_CPG


