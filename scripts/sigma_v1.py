# As we know the pi0 used to fit Sigma+ should be displaced from the IP
# We want to show when the displaced pi0 has better resolution

# The pi0:mdst from B2BII is mass constrained. Have to set updateAllDaughters to be true to 
# see the distribution of pi0 mass


# Expectations:
# - With IP constraint on the Sigma+ vertex, the cosa should be close to 1 even it is not
#   corrected for IP position
#
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

mc_vars = ['isSignal', 'isPrimarySignal', 'mcPDG', 'genMotherPDG', 'nMCMatches',
          'mcP', 'mcE', 'mcPT']
kinematic_vars = ['M', 'p', 'pt', 'pz', 'phi', 'theta', 'charge', 'xp']
vertex_vars = ['cosa', 'cosaXY', 'chiProb', 'x', 'y', 'z', 
               'distance', 'significanceOfDistance']
track_vars = ['d0', 'z0', 'd0Err']
pid_vars = ['pid_ppi', 'pid_pk', 'pid_kpi']
event_vars = ['IPX', 'IPY', 'IPZ']

# Variables
# =============================================
# sigma+
sigma_vars = kinematic_vars + vertex_vars + mc_vars + track_vars
# proton
proton_vars = create_aliases_for_selected(kinematic_vars + track_vars + pid_vars + mc_vars,
                                          'Sigma+ -> ^p+ pi0', prefix = ['p'])
variables.addAlias('p_abs_d0', 'abs(p_d0)')
variables.addAlias('p_abs_z0', 'abs(p_z0)')
proton_vars += ['p_abs_d0', 'p_abs_z0']

# pi0
pi0_vars = create_aliases_for_selected(kinematic_vars + vertex_vars + mc_vars,
                                       'Sigma+ -> p+ ^pi0', prefix = ['pi0'])
# gamma
gamma_vars = []
create_aliases_for_selected(['phi', 'theta', 'E', 'goodBelleGamma'],
                            'Sigma+ -> p+ [pi0 -> ^gamma ^gamma]', prefix = ['gamma1', 'gamma2'])
variables.addAlias('gamma_min_E', 'min(gamma1_E, gamma2_E)')
variables.addAlias('gamma_phi_diff', 'abs(formula(gamma1_phi - gamma2_phi))')
variables.addAlias('gamma_theta_diff', 'abs(formula(gamma1_theta - gamma2_theta))')
variables.addAlias('gamma_E_asym', 'abs(formula((gamma1_E - gamma2_E) / (gamma1_E + gamma2_E)))')
gamma_vars += ['gamma_min_E', 'gamma_phi_diff', 'gamma_theta_diff', 'gamma_E_asym', 'gamma1_theta', 'gamma2_theta',
              'gamma1_E', 'gamma2_E']

ntuple_vars = sigma_vars + proton_vars + pi0_vars + gamma_vars + event_vars

# Reconstruction
# ==============================================
# Standard PID cuts for charged final state particles
ma.fillParticleList('p+:good', 'pid_ppi >= 0.6 and pid_pk >= 0.6', path = mp)
ma.reconstructDecay('Sigma+:loose -> p+:good pi0:mdst', 'M >= 1.0 and M <= 1.4', path = mp)
## !!! Have to set updateAllDaughters = True because the pi0:mdst list is mass constrained
ma.vertexTree('Sigma+:loose', 0, ipConstraint = True, updateAllDaughters = True, path = mp)
ma.applyCuts('Sigma+:loose', 'M >= 1.1 and M <= 1.3', path = mp)
# ma.matchMCTruth('Sigma+:loose', path = mp)
# mp.add_module('VariablesToNtuple', particleList = 'Sigma+:loose', 
#               variables=ntuple_vars, treeName='sigma_loose', fileName=sys.argv[2])

# Eff of this cut is about 96% and rejects about 50% of the background for Sigma+
pi0_mass_cut = 'daughter(1, M) >= 0.11 and daughter(1, M) <= 0.16'
ma.cutAndCopyList('Sigma+:good', 'Sigma+:loose', pi0_mass_cut, path = mp)
ma.vertexTree('Sigma+:good', 0, ipConstraint = True, massConstraint = [111], 
              updateAllDaughters = False, path = mp)
ma.applyCuts('Sigma+:good', 'M >= 1.16 and M <= 1.22', path = mp)
ma.matchMCTruth('Sigma+:good', path = mp)
mp.add_module('VariablesToNtuple', particleList = 'Sigma+:good', 
              variables=ntuple_vars, treeName='sigma_good', fileName=sys.argv[2])

# # Mass constrain pi0 and update the daughters
# ma.vertexTree('Sigma+:good', 0, ipConstraint = True, massConstraint = [111], 
#               updateAllDaughters = True, path = mp)
# ma.matchMCTruth('Sigma+:good', path = mp)
# mp.add_module('VariablesToNtuple', particleList = 'Sigma+:good', 
#               variables=ntuple_vars, treeName='sigma_updated', fileName=sys.argv[2])

b2.process(path=mp)

print(b2.statistics)

