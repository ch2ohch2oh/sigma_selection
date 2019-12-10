# Difference compared with v7
# - Removed clusterTiming and clusterErrorTiming since there are all 0
# + Randomly discard 99% of the background to make sig:bkg ~ 1:1
# + More files processed exp55 run 1-500
# 
# This is the first fully working version of the Sigma+ reconstruction script
# - The number of candidates per event is not absurdly large
# - The output size is reasonable and the mass peaks are not truncated at the tail
# - Two tree fits are used
# 
# MC sample: http://bweb3.cc.kek.jp/montecarlo.php?ex=55&rs=1&re=500&ty=Any&dt=Any&bl=caseB&st=0

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

b2c.setupB2BIIDatabase(isMC = False)

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
pi0_vars = create_aliases_for_selected(['p', 'M', 'mcPDG', 'genMotherPDG', 'isSignal'],
                                       'Sigma+ -> p+ ^pi0', prefix = ['pi0'])
# gamma
gamma_vars = create_aliases_for_selected(['theta', 'E', 'genMotherPDG', 'isSignal'],
                            'Sigma+ -> p+ [pi0 -> ^gamma ^gamma]', prefix = ['gamma1', 'gamma2'])

ntuple_vars = sigma_vars + proton_vars + pi0_vars + gamma_vars + event_vars

# RECONSTRUCTION
# ==============================================
ma.fillParticleList('p+:all', '', path = mp)
ma.fillParticleList('pi+:all', '', path = mp)
# M Berger: standard pairwise PID > 0.6 and impact parameter > 0.003
ma.cutAndCopyList('p+:berger', 'p+:all', 'pid_ppi > 0.6 and pid_pk > 0.6', path = mp)
# M Berger: photons > 40 MeV and pi0 lab frame momentum > 100 MeV
ma.cutAndCopyList('pi0:loose',  'pi0:mdst', '', path = mp)
ma.reconstructDecay('Sigma+:loose -> p+:berger pi0:loose', 'M >= 1.15 and M <= 1.23', path = mp)
# Set updateAllDaughters = True because the pi0:mdst list is mass constrained
ma.vertexTree('Sigma+:loose', 0, ipConstraint = True, updateAllDaughters=True, path = mp)

# M Berger: discard condidates with wrong sign of flight distance
ma.cutAndCopyList('Sigma+:good', 'Sigma+:loose',
                  'gamma1_E > 0.03 and gamma2_E > 0.03 and pi0_M >= 0.11 and pi0_M <= 0.16 and pi0_p > 0.05', 
                   path = mp)
ma.vertexTree('Sigma+:good', 0, ipConstraint = True, massConstraint = [111], path = mp)
ma.applyCuts('Sigma+:good', 'M >= 1.17 and M <= 1.21', path = mp)
# ma.matchMCTruth('Sigma+:good', path = mp)

mp.add_module('MVAExpert', listNames=['Sigma+:good'], extraInfoName='Sigma_mva', 
              identifier='MVA_Sigma_p.root')
variables.addAlias('Sigma_mva', 'extraInfo(Sigma_mva)')

ma.applyCuts('Sigma+:good', 'extraInfo(Sigma_mva) > 0.2', path = mp)

lamc_pi_vars = create_aliases_for_selected(['p', 'M', 'dr', 'dz', 'pid_ppi', 'pid_kpi', 'pid_pk',
                                             'mcPDG', 'genMotherPDG', 'isSignal'],
                                             'Lambda_c+:loose -> Sigma+:good ^pi+:all ^pi-:all', 
                                             prefix = ['pi_plus', 'pi_minus'])
lamc_sigma_vars = create_aliases_for_selected(['p', 'M', 'dr', 'dz', 
                                               'mcPDG', 'genMotherPDG', 'isSignal',
                                               'Sigma_mva'],
                                             'Lambda_c+:loose -> ^Sigma+:good pi+:all pi-:all', 
                                             prefix = ['sigma'])
ma.reconstructDecay('Lambda_c+:loose -> Sigma+:good pi+:all pi-:all', 
                    'pi_plus_pid_ppi < 0.6 and pi_plus_pid_kpi < 0.6 and '
                    'pi_minus_pid_ppi < 0.6 and pi_minus_pid_kpi < 0.6 and '
                    'M >= 2.2 and M <= 2.4', path = mp)
ma.vertexTree('Lambda_c+:loose', 0, massConstraint = [3222], path = mp)
ma.applyCuts('Lambda_c+:loose', 'M >= 2.24 and M <= 2.34', path = mp)

# Dalitz variables
variables.addAlias('m_sigma_pi_plus', 'daughterInvM(0, 1)')
variables.addAlias('m_sigma_pi_minus', 'daughterInvM(0, 2)')
variables.addAlias('m_pi_pi', 'daughterInvM(1, 2)')

dalitz_vars = ['m_sigma_pi_plus', 'm_sigma_pi_minus', 'm_pi_pi']
lamc_vars = ['M', 'p', 'distance', 'significanceOfDistance', 'chiProb', 'xp', 'mcPDG', 'genMotherPDG', 'isSignal']

ntuple_vars = lamc_pi_vars + lamc_sigma_vars + dalitz_vars + lamc_vars

ma.matchMCTruth('Lambda_c+:loose', path = mp)

# ma.cutAndCopyList('Sigma+:sig', 'Sigma+:good', 'isSignal == 1', path = mp)
# Randomly throw away 99% of the background to make sig:bkg ~ 1:1
# ma.cutAndCopyList('Sigma+:bkg', 'Sigma+:good', 'isSignal == 0 and random < 0.01', path = mp)
# ma.copyLists('Sigma+:merged', ['Sigma+:sig', 'Sigma+:bkg'], path = mp)

mp.add_module('VariablesToNtuple', particleList = 'Lambda_c+:loose', 
              variables=ntuple_vars, treeName='lambda_c', fileName=sys.argv[2])

b2.process(path=mp)
print(b2.statistics)

