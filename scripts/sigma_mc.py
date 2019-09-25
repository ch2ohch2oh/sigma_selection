# Reconstruct sigma+
# 
# Decay channel:
#	simga+ -> p+ pi0
#
# Selection criteria:
#	Load lambda0 using B2BII and do a vertexKFit. Keep all the candidates with chiProb>=0.
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
list_track = ['d0', 'z0', 'tanlambda', 'phi0', 'omega',
	'd0Err', 'z0Err', 'tanlambdaErr', 'phi0Err',  'omegaErr', 'pValue']
list_cluster = ['clusterE', 'clusterTheta', 'clusterPhi', 'clusterE', 'clusterR']
list_v0 = ['V0Deltad0', 'V0Deltaz0']
list_pid = ['pid_ppi', 'pid_pk', 'pid_kpi']
list_event = ['IPX', 'IPY', 'IPZ']

# All the variables that go to the final ntuple.
# =============================================
# sigma+
list_ntuple = list_basics + list_vertex + list_v0 + list_mc + list_event + ['cosa', 'cosaXY']
# proton
list_ntuple += create_aliases_for_selected(list_basics + list_track + list_pid + list_mc,
	'Sigma+ -> ^p+ pi0', prefix = ['p'])
# pion
list_ntuple += create_aliases_for_selected(list_basics + list_vertex + list_mc,
	'Sigma+ -> p+ ^pi0', prefix = ['pi0'])
# gamma
list_ntuple += create_aliases_for_selected(list_basics + list_cluster + list_mc,
	'Sigma+ -> p+ [pi0 -> ^gamma ^gamma]', prefix = ['gamma1', 'gamma2'])

# Reconstruction
# ===========================================
#ma.vertexTree('pi0:mdst', 0, massConstraint = [111],  path = mp)
# Use only proton with good PID info
ma.fillParticleList('p+:good', 'pid_ppi > 0.6 and pid_pk > 0.6', path = mp)
# Put a wide 20 MeV mass cut around the nominal mass
ma.reconstructDecay('Sigma+:ip -> p+:good pi0:mdst', 'M >= 1.18 and M <= 1.20', path = mp)
ma.vertexTree('Sigma+:ip', -1, massConstraint = [111], ipConstraint = True,
              updateAllDaughters = True, path = mp)
ma.matchMCTruth('Sigma+:ip', path = mp)
#ma.cutAndCopyList('pi0:updated', 'pi0:mdst', '', path = mp)
#ma.reconstructDecay('Sigma+:displaced -> p+:good pi0:updated', '', path = mp)
#ma.vertexTree('Sigma+:displaced', -1, massConstraint = [111], path = mp)

# Write ntuple to root file
mp.add_module('VariablesToNtuple',
	particleList='Sigma+:ip',
	variables=list_ntuple,
	treeName='sigma',
	fileName=sys.argv[2])

b2.process(path=mp)

print(b2.statistics)

