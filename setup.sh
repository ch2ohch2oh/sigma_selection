#!/bin/bash
echo "Setting up BASF2 environment..."
RELEASE=release-03-02-04

source /cvmfs/belle.cern.ch/tools/b2setup
echo "Release set up to $RELEASE..."
b2setup $RELEASE

# Deal with segmentation violation for some versions
export LD_LIBRARY_PATH=/sw/belle/local/neurobayes-4.3.1/lib/:$LD_LIBRARY_PATH

# Running on data for exp 31-65
export USE_GRAND_REPROCESS_DATA=1

# Set Belle DB
export BELLE_POSTGRES_SERVER=can01

# Access to Belle DB
export PGUSER=g0db

echo "Done. Have fun :)"
