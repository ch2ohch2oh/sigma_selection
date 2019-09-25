import os
import b2biiConversion as b2c
import glob
import sys
import argparse
import logging
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('script', help = 'Script to run')
parser.add_argument('--mc', help = 'Is MC or not')
parser.add_argument('--test', action = 'store_true', default = False,
                    help = 'Process the first mdst for testing')
parser.add_argument('--clear', action = 'store_true', default = False,
                   help = 'Clear output dir or not')
args = parser.parse_args()

list_mdst = []
output_dir = ''
script = args.script

if script == 'pi0_mc.py':
    # Do not need too much data for pi0
    list_mdst = b2c.parse_process_url('http://bweb3.cc.kek.jp/montecarlo.php?ex=55&rs=1&re=20&ty=Any&dt=on_resonance&bl=caseB&st=1')
    assert(len(list_mdst) == 16)
    output_dir = '../data/pi0'
else:
    assert 0, 'You should not be here!'

if args.clear == True:
    print("Clear output directory...")
    shutil.rmtree(output_dir)
    os.mkdir(output_dir)

if args.test == True:
    list_mdst = list_mdst[:1]
    print("Test: only keep the first mdst file to process")

print('Script: %s' % script)
print('Output dir: %s' % output_dir)
print('Number of mdst files: %d' % len(list_mdst))
print('Submit jobs'.center(60, '='))

for mdst_id, mdst_path in enumerate(list_mdst, 1):
    mdst_name = os.path.basename(mdst_path)
    root_name = mdst_name + '.root'
    log_name = mdst_name + '.log'
    output_path = os.path.join(output_dir, root_name)
    log_path =  os.path.join(output_dir, log_name)
    print("[%d/%d]" % (mdst_id, len(list_mdst)))
    os.system('bsub -q l -oo {log_path} basf2 {script} {mdst_path} {output_path}'.format(**locals()))

