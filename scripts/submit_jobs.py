#!/usr/bin/env python3
# 
# Submit jobs based on user scrpits
#
#
import os
import b2biiConversion as b2c
import glob
import sys
import argparse
import logging
import shutil
from termcolor import colored
from multiprocessing import Pool
import tqdm

def get_dataset(name):
    """Retrieve list of mdst files based on the name of the dataset"""
    if name == 'mc_exp55':
        return b2c.parse_process_url('http://bweb3.cc.kek.jp/montecarlo.php?ex=55&rs=1&re=50&ty=Any&dt=Any&bl=caseB&st=0')
    elif name == 'mc_background':
        return b2c.parse_process_url('http://bweb3.cc.kek.jp/montecarlo.php?ex=55&rs=1&re=30&ty=Any&dt=Any&bl=caseB&st=0')
    elif name == 'mc_exp65':
        return b2c.parse_process_url('http://bweb3.cc.kek.jp/montecarlo.php?ex=65&rs=1&re=25&ty=Any&dt=Any&bl=caseB&st=0')
    elif name == 'exp65_4S':
        return b2c.parse_process_url('http://bweb3.cc.kek.jp/mdst.php?ex=65&rs=1&re=100&skm=HadronBorJ&dt=on_resonance&bl=caseB')
    elif name == 'exp65_1S':
        return b2c.parse_process_url('http://bweb3.cc.kek.jp/mdst.php?ex=65&rs=1000&re=1050&skm=HadronBorJ&dt=1S_scan&bl=caseB')
    elif name == 'exp65_cont':
        return b2c.parse_process_url('http://bweb3.cc.kek.jp/mdst.php?ex=65&rs=0&re=9999&skm=HadronBorJ&dt=continuum&bl=caseB')
    else:
        raise Exception(f'Dataset ({name}) not found')

def submit_one(script, mdstpath, outdir, b2opt=""):
    """Submit one job for one mdst file"""
#     print(mdstpath)
    base = os.path.basename(mdstpath)
    rootname = base + '.root'
    logname = base + '.log'
    rootpath = os.path.join(outdir, rootname)
    logpath = os.path.join(outdir, logname)
    os.system(f'bsub -q s -oo {logpath} basf2 {b2opt} {script} {mdstpath} {rootpath} >> /dev/null')
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('script', help = 'Script to run')
    parser.add_argument('data', help = 'Which data set to use?')
    parser.add_argument('--one', action = 'store_true', default = False,
                        help = 'Process the first mdst for testing')
    parser.add_argument('--clear', action = 'store_true', default = False,
                       help = 'Clear output dir or not')
    parser.add_argument('outdir', help = 'Output dir')

    args = parser.parse_args()
    
    # Give user some information about the script and data set
    print(f'Script to run: {args.script}')
    print(f'Dataset: {args.data}')
    dataset = get_dataset(args.data)
    assert len(dataset) > 0, "Empty dataset!"
    print('The dataset contains %d mdst files' % len(dataset))
    if args.one == True:
        print(colored('Test mode on: will only run on the first mdst file', 'red'))
        dataset = dataset[:1]
    
    outdir = args.outdir
    print(f'Output dir: {outdir}')
    
    # Create output dir if not existing
    os.makedirs(outdir, exist_ok = True)
    if not os.path.exists(outdir):
        raise Exception("Failed to create output dir")
    
    # Clear the output dir if asked
    if args.clear == True:
        print(colored('Clearing output directory...', 'red'))
        shutil.rmtree(outdir)
        os.mkdir(outdir)
        assert os.path.exists(outdir), "Output directory does not exist!"
        print(colored('Done', 'green'))

    bar = tqdm.tqdm(total = len(dataset))
    b2opt = ""
    if args.one == True:
        b2opt = "-n 1000"
    for mdst in dataset:
        submit_one(args.script, mdst, args.outdir, b2opt)
        bar.update()