# This is the first fully working version of the Sigma+ reconstruction script
# - The number of candidates per event is not absurdly large
# - The output size is reasonable and the mass peaks are not truncated at the tail
# - Two tree fits are used
# 
# MC sample: http://bweb3.cc.kek.jp/montecarlo.php?ex=55&rs=1&re=50&ty=Any&dt=Any&bl=caseB&st=0
# => 1.4M candidates, 14K matched 
# => 57 columns 
# => 337MB output in total :-)
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

def print_env():
    """
    Print relevant environmental variables.
    """
    import datetime
    envs = ['BELLE2_EXTERNALS_DIR',
            'BELLE2_EXTERNALS_SUBSIR',
            'BELLE2_EXTERNALS_OPTION',
            'BELLE2_EXTERNALS_VERSION',
            'BELLE2_LOCAL_DIR',
            'BELLE2_OPTION',
            'BELLE2_RELEASE',
            'BELLE_POSTGRES_SERVER',
            'USE_GRAND_REPROCESS_DATA',
            'PANTHER_TABLE_DIR',
            'PGUSER']
    print("Current time is %s" % datetime.datetime.now())
    print()
    print("[Environmental variables]")
    for var in envs:
        print("%30s = %s" % (var, os.getenv(var)))
    print()

print_env()

# Show input and output file info
print("Input: %s" % sys.argv[1])
print("Ouput: %s" % sys.argv[2])

mp = b2.create_path()

b2c.convertBelleMdstToBelleIIMdst(sys.argv[1], applyHadronBJSkim=True, path=mp)


variables.addAlias('pid_ppi', 'atcPIDBelle(4,2)')
variables.addAlias('pid_pk', 'atcPIDBelle(4,3)')
variables.addAlias('pid_kpi', 'atcPIDBelle(3,2)')

variables.addAlias('cosa', 'cosAngleBetweenMomentumAndVertexVector')
variables.addAlias('cosaXY', 'cosAngleBetweenMomentumAndVertexVectorInXYPlane')

mc_vars = ['isSignal', 'isPrimarySignal', 'mcPDG', 'genMotherPDG', 'nMCMatches']
kinematic_vars = ['M', 'p', 'pt', 'pz', 'phi', 'theta', 'charge', 'xp']
vertex_vars = ['cosa', 'cosaXY', 'chiProb', 'dr', 'dz', 'x', 'y', 'z', 
               'distance', 'significanceOfDistance']
track_vars = ['d0', 'z0', 'd0Err']
pid_vars = ['pid_ppi', 'pid_pk', 'pid_kpi']
event_vars = ['IPX', 'IPY', 'IPZ']

# Variables
# =============================================
# sigma+
sigma_vars = ['p', 'pt', 'pz', 'E', 'M',
              'charge', 'distance', 'significanceOfDistance',
              'cosa', 'cosaXY',
              'mcPDG', 'genMotherPDG', 'isSignal']
# proton
proton_vars = create_aliases_for_selected(['p', 'dr', 'dz', 'pid_ppi', 'pid_pk', 'pid_kpi', 'isSignal', 'genMotherPDG'],
                                          'Sigma+ -> ^p+ pi0', prefix = ['p'])

# pi0
pi0_vars = create_aliases_for_selected(['p', 'M', 'mcPDG', 'genMotherPDG', 'isSignal', 'distance', 'significanceOfDistance'],
                                       'Sigma+ -> p+ ^pi0', prefix = ['pi0'])
# gamma
gamma_vars = create_aliases_for_selected(['phi', 'theta', 'E', 'goodBelleGamma', 'clusterReg', 'clusterE9E21', 
                             'clusterTiming', 'clusterErrorTiming', 'genMotherPDG', 'isSignal'],
                            'Sigma+ -> p+ [pi0 -> ^gamma ^gamma]', prefix = ['gamma1', 'gamma2'])

ntuple_vars = sigma_vars + proton_vars + pi0_vars + gamma_vars + event_vars

# RECONSTRUCTION
# ==============================================
ma.fillParticleList('p+:all', '', path = mp)
# M Berger: standard pairwise PID > 0.6 and impact parameter > 0.003
ma.cutAndCopyList('p+:berger', 'p+:all', 'pid_ppi > 0.6 and pid_pk > 0.6', path = mp)
# M Berger: photons > 40 MeV and pi0 lab frame momentum > 100 MeV
ma.cutAndCopyList('pi0:loose',  'pi0:mdst', '', path = mp)
ma.reconstructDecay('Sigma+:loose -> p+:berger pi0:loose', 'M >= 1.15 and M <= 1.23', path = mp)
# Set updateAllDaughters = True because the pi0:mdst list is mass constrained
ma.vertexTree('Sigma+:loose', 0, ipConstraint = True, updateAllDaughters=True, path = mp)

# M Berger: discard condidates with wrong sign of flight distance
ma.cutAndCopyList('Sigma+:good', 'Sigma+:loose',
                  'gamma1_E > 0.05 and gamma2_E > 0.05 and pi0_M >= 0.11 and pi0_M <= 0.16 and pi0_p > 0.1', 
                   path = mp)
ma.vertexTree('Sigma+:good', 0, ipConstraint = True, massConstraint = [111], path = mp)
ma.applyCuts('Sigma+:good', 'M >= 1.17 and M <= 1.21', path = mp)
ma.matchMCTruth('Sigma+:good', path = mp)
mp.add_module('VariablesToNtuple', particleList = 'Sigma+:good', 
              variables=ntuple_vars, treeName='good', fileName=sys.argv[2])

b2.process(path=mp)
print(b2.statistics)

