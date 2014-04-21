import sys
import os
import numpy as np
import json

if __name__ == "__main__":
  trial_num = int(sys.argv[1])
  gen_num = int(sys.argv[2])
  lower_bound = int(sys.argv[3])
  higher_bound = int(sys.argv[4])
  partition_num = int(sys.argv[5])

  path_base = os.path.join(os.environ['GEN_HOME'],'trial%d' % trial_num,'gen%d' % gen_num)

  # open the cpgs there
  fitness_dict = {}
  for cpg_id in range(lower_bound, higher_bound):
    cpg_path = os.path.join(path_base,'%d.enc' % cpg_id)
    with open(cpg_path, 'r') as cpg_enc:
      cpg = json.load(cpg_enc)

    # 'process' the cpg by summing all of the parameters
    param_total = 0
    for i in cpg:
      param_total += np.sum(cpg[i])

    fitness_dict[str(cpg_id)] = param_total

  # now write the fitness_dict to path_base/total{partition_num}.fit
  print(fitness_dict)
  write_path = os.path.join(path_base,'total%d.fit' % partition_num)
  with open(write_path, 'w') as fit_out:
    json.dump(fitness_dict, fit_out)
