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
import variables.collections as vc

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

mc_vars = ['isSignal', 'isPrimarySignal', 'mcPDG', 'genMotherPDG', 'nMCMatches']
kinematic_vars = ['M', 'p', 'px', 'py', 'pz', 'phi', 'theta', 'charge', 'xp']
vertex_vars = ['cosa', 'cosaXY', 'chiProb', 'x', 'y', 'z', 
               'distance', 'significanceOfDistance']
track_vars = ['d0', 'z0']
pid_vars = ['pid_ppi', 'pid_pk', 'pid_kpi']
event_vars = ['IPX', 'IPY', 'IPZ']

# Variables
# =============================================
# sigma+
sigma_vars = kinematic_vars + vertex_vars + mc_vars
# proton
proton_vars = create_aliases_for_selected(kinematic_vars + track_vars + pid_vars + mc_vars,
                                          'Sigma+ -> ^p+ pi0', prefix = ['p'])
# pi0
pi0_vars = create_aliases_for_selected(kinematic_vars + vertex_vars + mc_vars,
                                       'Sigma+ -> p+ ^pi0', prefix = ['pi0'])
# gamma
gamma_vars = create_aliases_for_selected(['phi', 'theta', 'E', 'goodBelleGamma'],
                                         'Sigma+ -> p+ [pi0 -> ^gamma ^gamma]', prefix = ['gamma1', 'gamma2'])

ntuple_vars = sigma_vars + proton_vars + pi0_vars + gamma_vars + event_vars

# Reconstruction
# ==============================================
# Use only proton with good PID info and some distance away from IP
ma.fillParticleList('p+:good', 'pid_ppi >= 0.6 and pid_pk >= 0.6', path = mp)

# Vertex pi0s to IP so that we have a mass distribution of pi0s
# The pi0:mdst list is mass constrained by default
#ma.vertexTree('pi0:mdst', 0, path = mp)

# Put a 20 MeV mass cut around the nominal mass
ma.reconstructDecay('Sigma+:loose -> p+:good pi0:mdst', 'M >= 1.1 and M <= 1.3', path = mp)
ma.vertexTree('Sigma+:loose', 0, ipConstraint = True, updateAllDaughters = True, path = mp)

# Save the variables before mass constraint
mp.add_module('VariablesToNtuple', 
              particleList = 'Sigma+:loose', 
              variables=ntuple_vars,
              treeName='sigma_loose', 
              fileName=sys.argv[2])

# Select good pi0 with displaced vertex
pi0_cut = 'daughter(1, M) >= 0.12 and daughter(1, M) <= 0.15'
ma.cutAndCopyList('Sigma+:good', 'Sigma+:loose', pi0_cut, path = mp)
ma.vertexTree('Sigma+:good', 0, ipConstraint = True, massConstraint = [111], path = mp)
ma.matchMCTruth('Sigma+:good', path = mp)

mp.add_module('VariablesToNtuple', 
              particleList = 'Sigma+:good', 
              variables=ntuple_vars,
              treeName='sigma_good', 
              fileName=sys.argv[2])

b2.process(path=mp)

print(b2.statistics)

