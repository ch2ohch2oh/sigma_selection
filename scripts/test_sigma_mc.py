import unittest
import os
import ROOT

input_mdst = '/group/belle/bdata_b/mcprod/dat/e000055/evtgen/charged/01/all/0127/on_resonance/00/evtgen-charged-01-all-e000055r000007-b20090127_0910.mdst'
output_name = 'test_output_mc.root'
os.system('basf2 -n 10000 sigma_mc.py %s %s' %(input_mdst, output_name))
