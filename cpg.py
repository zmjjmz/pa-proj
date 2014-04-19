import numpy as np

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
    n_body = 16
    self.osc_class = [0 if i < n_body else 1 for i in range(self.n)] # 0 for body oscillator, 1 for limb oscillator
    # list of keys that can be mutated during evolution
    self.evolvables = ['w', 'phi', 'a', 'gsl', 'gsh', 'gb1', 'gb2', 'theta', 'ampl', 'ampl_dot']

  def make(self, ident):
    """ Randomly generates the parameters for a CPG """
    CPG = dict()
    CPG['ident'] = ident
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

  def mix(self, cpgs, ident, method='avg', mutation_prob=0.5, crossover_prob=[0.5, 0.5]):
    """ Takes a list of cpgs and mixes them into one """
    # Available methods:
    # note that mutation means selecting a new random scalar for a particular value
    # avg -- takes the average of all of the keys in self.evolvables and then goes through all of their values and chooses whether or not to mutate them by mutation_prob
    # crossover -- goes through all of the values and chooses from the nth cpg in cpgs with probability crossover_prob[n], then mutates them
    # defaults to choosing from the first two cpgs with equal probability

    n_cpgs = float(len(cpgs))


    new_CPG = dict()
    new_CPG['ident'] = ident
    new_CPG = self._set_constants(new_CPG)
    cfd =

    if method == 'avg':
      for key in self.evolvables:
        avg_params = sum([cpg[key] for cpg in cpgs]) / n_cpgs
        new_CPG[key] = avg_params

    return new_CPG
"""
    if method == 'crossover':
      # Pad crossover_prob
      if len(crossover_prob) < len(cpgs):
        # assume the cpgs

      s_cpgs = [i[1] for i in sorted(enumerate(cpgs), key=lambda x: crossover_prob[x[0]])]
"""

