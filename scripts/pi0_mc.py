#!/usr/bin/env python3
# Reconstruct pi0
#
# Goal:
#    Determine what should be a reasonable cut for pi0 for further reconstruction
#
import basf2 as b2
import modularAnalysis as ma
import b2biiConversion as b2c
import b2biiMonitors as b2m
import os
import sys

from variables import variables
from variables.utils import create_aliases_for_selected
from variables.utils import create_aliases

b2c.setupB2BIIDatabase(isMC = True)

def print_env(var):
	"""Print environmental variable."""
	print("%30s = %s" % (var, os.getenv(var)))

env_list = ['BELLE2_EXTERNALS_DIR',
	'BELLE2_EXTERNALS_SUBSIR',
	'BELLE2_EXTERNALS_OPTION',
	'BELLE2_EXTERNALS_VERSION',
	'BELLE2_LOCAL_DIR',
	'BELLE2_OPTION',
	'BELLE_POSTGRES_SERVER',
	'USE_GRAND_REPROCESS_DATA',
	'PANTHER_TABLE_DIR',
	'PGUSER']

# Print env variables for check
print("Environmental Variables".center(80, '='))
for v in env_list:
	print_env(v)

# Show input and output file info
print("Input: %s" % sys.argv[1])
print("Ouput: %s" % sys.argv[2])

mp = b2.create_path()

b2c.convertBelleMdstToBelleIIMdst(sys.argv[1], applyHadronBJSkim=True, path=mp)

# Aliases for the variables to make the root file easier to understand
variables.addAlias('pid_ppi', 'atcPIDBelle(4,2)')
variables.addAlias('pid_pk', 'atcPIDBelle(4,3)')
variables.addAlias('pid_kpi', 'atcPIDBelle(3,2)')

variables.addAlias('cosa', 'cosAngleBetweenMomentumAndVertexVector')
variables.addAlias('cosaXY', 'cosAngleBetweenMomentumAndVertexVectorInXYPlane')

list_mc = ['isSignal', 'mcErrors', 'mcPDG', 
	'genMotherID', 'genMotherP', 'genMotherPDG', 'genParticleID', 
	'nMCMatches', 'isPrimarySignal']
list_basics = ['M', 'ErrM', 'px', 'py', 'pz', 'pt', 'p', 'E', 'cosTheta', 'phi', 'charge', 'PDG']
list_vertex = ['distance', 'significanceOfDistance', 'x', 'y', 'z',
	'dx', 'dy', 'dz', 
	'x_uncertainty', 'y_uncertainty', 'z_uncertainty', 
	'dr', 'dphi', 'dcosTheta', 'chiProb', 'cosa', 'cosaXY']
list_event = ['IPX', 'IPY', 'IPZ']

# pi0 list before the fit
ma.cutAndCopyList('pi0:before_fit', 'pi0:mdst', '', path = mp)
ma.matchMCTruth('pi0:before_fit', path = mp)

ma.vertexKFit('pi0:mdst', 0, path = mp)
# pi0 list after the fit
ma.matchMCTruth('pi0:mdst', path = mp)

list_pi0 = list_event + list_basics + list_mc + \
    create_aliases_for_selected(list_basics + list_mc,
                                'pi0 -> ^gamma ^gamma', prefix = ['gamma1', 'gamma2'])

# Generator level information for knowledge of efficiency
# =============================================
pi0_gen = ('pi0:gen', '')
ma.fillParticleListsFromMC([pi0_gen], path = mp)

# Write ntuple
# =============================================

mp.add_module('VariablesToNtuple',
	particleList='pi0:before_fit',
	variables = list_pi0,
	treeName='pi0_before',
	fileName=sys.argv[2])
mp.add_module('VariablesToNtuple',
	particleList='pi0:mdst',
	variables = list_pi0,
	treeName='pi0_after',
	fileName=sys.argv[2])
mp.add_module('VariablesToNtuple',
	particleList='pi0:gen',
	variables = list_basics + list_mc,
	treeName='pi0_gen',
	fileName=sys.argv[2])

b2.process(path=mp)

print(b2.statistics)