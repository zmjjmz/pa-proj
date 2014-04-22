import sys
import time
import os
from numpy import sum
import json

def doit():
  trial_num = int(sys.argv[1])
  gen_num = int(sys.argv[2])
  lower_bound = int(sys.argv[3])
  higher_bound = int(sys.argv[4])
  partition_num = int(sys.argv[5])

  try:
    path_base = os.path.join(os.environ['GEN_HOME'],'trial%d' % trial_num,'gen%d' % gen_num)
  except KeyError as kye:
    print("You probably didn't set GEN_HOME")
    raise

  # open the cpgs there
  fitness_dict = {}
  for cpg_id in range(lower_bound, higher_bound):
    cpg_path = os.path.join(path_base,'%d.enc' % cpg_id)
    with open(cpg_path, 'r') as cpg_enc:
      cpg = json.load(cpg_enc)

    # 'process' the cpg by summing all of the parameters
    param_total = 0
    print("Generation %d: Evaluating individual %d in partition %d" % (gen_num, cpg_id, partition_num))
    for i in cpg:
      if i == 'ident':
        continue
      param_total += sum(cpg[i])

    str_cpg_id = cpg['ident']

    fitness_dict[str_cpg_id] = param_total

  # now write the fitness_dict to path_base/total{partition_num}.fit
  write_path = os.path.join(path_base,'total%d.fit' % partition_num)
  with open(write_path, 'w') as fit_out:
    json.dump(fitness_dict, fit_out)

  sys.exit(0)

if __name__ == "__main__":
  doit()
