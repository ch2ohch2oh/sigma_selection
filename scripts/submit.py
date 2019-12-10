#!/usr/bin/env python3

# Submit jobs based on user scrpits
#
#
import b2biiConversion as b2c
import argparse
import glob
import os
import sys
import logging
import shutil
from termcolor import colored
import multiprocessing as mp
import tqdm

BELLE_EVENT_TYPES = ['Any', 'evtgen-mixed', 'evtgen-charged', 'evtgen-charm', 'evtgen-uds']
BELLE_DATA_TYPES = ['Any']

def get_mdst_list(is_data, exp, run_start = 1, run_end = 9999, 
                  event_type = 'Any', data_type = 'Any', 
                  belle_level = 'caseB', stream = 0):
    """
    Return mdst file list from Belle File Search Engine.
    """
    
    if not is_data:
        assert event_type in ['Any', 'evtgen-mixed', 'evtgen-charged', 'evtgen-charm', 'evtgen-uds']
        url =  f'http://bweb3.cc.kek.jp/montecarlo.php?ex={exp}&rs={run_start}&re={run_end}&ty={event_type}&dt={data_type}&bl={belle_level}&st={stream}'
    else:
        raise Exception("Not implemented")
    print(f'[get_mdst_list] Getting mdst from {url}')
    return b2c.parse_process_url(url)    

def submit_one(script, mdstpath, outdir, queue = 's', b2opt = ""):
    """
    Submit one job for one mdst file
    """
    base = os.path.basename(mdstpath)
    rootname = base + '.root'
    logname = base + '.log'
    rootpath = os.path.join(outdir, rootname)
    logpath = os.path.join(outdir, logname)
    return os.system(f'bsub -q {queue} -oo {logpath} basf2 {b2opt} {script} {mdstpath} {rootpath} >> /dev/null')
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    parser.add_argument('script', help = 'steering script to run')
    parser.add_argument('outdir', help = 'output dir')
    
    parser.add_argument('--is_data', action = 'store_true', default = False, help = 'MC or data')
    parser.add_argument('--exp', type=int, help = 'exp no.')
    parser.add_argument('--run_start', type = int, help = 'run number start', default = 1)
    parser.add_argument('--run_end', type = int, help = 'run number end', default = 9999)
    parser.add_argument('--event_type', help = 'event type (for MC)', 
                        default = 'Any', choices = BELLE_EVENT_TYPES)
    parser.add_argument('--data_type', help = 'data type (for data)', 
                        default = 'Any', choices = BELLE_DATA_TYPES)
    parser.add_argument('--stream',  type = int, default = 0,
                        help = 'stream number (for MC)')
    
    parser.add_argument('--one', action = 'store_true', default = False,
                        help = 'only process the first mdst in the list')
    parser.add_argument('--clear', action = 'store_true', default = False,
                        help = 'clear output dir or not')

    args = parser.parse_args()
    
    # Give user some information about the script and data set
    print("script =", args.script)
    print("outdir =", args.outdir)
    print("is_data =", args.is_data)
    print("exp =", args.exp)
    print("run_start =", args.run_start)
    print("run_end =", args.run_end)
    if not args.is_data:
        print("event_type =", args.event_type)
    else:
        print("data_type =", args.data_type)
    print("stream =", args.stream)
    
    dataset = get_mdst_list(args.is_data, 
                            args.exp, 
                            run_start = args.run_start,
                            run_end = args.run_end,
                            event_type = args.event_type,
                            data_type = args.data_type,
                            stream = args.stream)
    if len(dataset) == 0:
        print(colored('Empty dataset', 'red'))
        exit(1)

    print('The dataset contains %d mdst files' % len(dataset))
    if args.one == True:
        print(colored('Test mode on: will only run on the first mdst file', 'red'))
        dataset = dataset[:1]
    
    # Create output dir if not existing
    outdir = args.outdir
    os.makedirs(outdir, exist_ok = True)
    if not os.path.exists(outdir):
        raise Exception("Failed to create output dir")
    
    # Clear the output dir if asked
    if args.clear == True:
        print(colored('Clearing output directory...', 'red'), end = '')
        shutil.rmtree(outdir)
        os.mkdir(outdir)
        assert os.path.exists(outdir), "Output directory does not exist!"
        print(colored('Done', 'green'))
    
    # Use more workers to make submission faster
    nworkers = 8
    print("Number workers for job submission =", nworkers)
    pool = mp.Pool(nworkers)
    
    bar = tqdm.tqdm(total = len(dataset))
    def update_bar(*args):
        bar.update()
    b2opt = ""
    if args.one == True:
        b2opt = "-n 1000"

    for mdst in dataset:
        pool.apply_async(submit_one, args = (args.script, mdst, args.outdir, 's', b2opt), callback = update_bar)
    pool.close()
    pool.join()
    
