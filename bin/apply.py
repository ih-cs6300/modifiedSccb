#! /usr/bin/env python
"""
"""

import os
import sys
import ccbid
import argparse
import numpy as np
import multiprocessing
from ccbid import args
from ccbid import prnt
from sklearn import metrics
from sklearn import model_selection

"""steps
-read model
-read input spectra (from csv or from image)
-apply model to samples
-average by crown
-output predictions (as csv or image)

things to add to model object
-reducer
-bands

create ccbid model input argument
"""


# set up the argument parser to read command line inputs
def parse_args():
    """Function to read CCB-ID command line arguments
    
    Args:
        None - reads from sys.argv
        
    Returns:
        an argparse object
    """
    
    # create the argument parser
    parser = args.create_parser(description='Train and save a CCB-ID species classification model.')
    #parser = argparse.ArgumentParser(description='Train and save a CCB-ID species classification model.')
    
    # set up the arguments for dealing with file i/o
    args.input(parser)
    args.mask(parser) # write this, option to pass a good-data mask
    args.output(parser)
    args.ecodse(parser)
    args.ccbid_model(parser)

    # arguments to turn on certian flags or set specific parameters
    args.remove_outliers(parser)
    args.aggregate(parser) # write this, option to aggregate the data to other scales (e.g., crown scale)
    args.aggregate_labels(parser) # write this, option to read image with crown labels
    #args.feature_selection(parser)
    args.cpus(parser)
    args.verbose(parser)

    # parse the inputs from sys.argv
    return parser.parse_args(sys.argv[1:])


# set up the logic to parse command line arguments and ensure consistent logic
def arg_logic(args):
    """Parses the command line arguments to ensure consistency prior to running the main script
    
    Args:
        args - the arguments returned from the argparse object
        
    Returns:
        None. This function updates the args object
    """
    
    # if the ECODSE flag is set, override whatever is set at the command line
    if args.ecodse:
        args.input = args.path_training
        args.remove_outliers = False
        #args.feature_selection = False


# set up the main script function
def main():
    """The main function for ccbid apply
    
    Args:
        None - just let it fly
        
    Returns:
        None - this runs the dang script
    """
    
    # first read the command line arguments
    args = parse_args()
    
    # parse the logic to make sure everything runs smoothly
    arg_logic(args)
    
    # set the seed for reproducibility (to the year the CCB was founded)
    np.random.seed(1984)
    
    #-----
    # step 1. reading data
    #-----
    
    if args.verbose:
        prnt.line_break()
        prnt.status("Reading input data")
    
    # first read the model data
    model = ccbid.read.pck(args.ccbid_model)
    
    # set up a dummy variable to determine if data should be output on a per-crown or per-=pixel basis
    
    # then read the feature data, which may come as a raster or a csv
    if ccbid.read.is_raster(args.input):
        features = ccbid.read.raster(args.input)
        # work on this later
        
    if ccbid.read.is_csv(args.input):
        testing_id, features = ccbid.read.training_data(args.input)
        crowns_unique = np.unique(testing_id)
        
    #-----
    # step 2. outlier removal
    #-----
    
    if args.remove_outliers is not None:
        if args.verbose:
            prnt.status("Removing outliers using {}".format(args.remove_outliers))
            
        # currently only one version of outlier removal
        if args.remove_outliers == 'PCA':
            mask = ccbid.outliers.with_pca(features[:, model.good_bands])
            
        # subset all data using the mask for future analyses
        features = features[mask, :]
        testing_id = training_id[mask]
        
        # report on the number of samples removed
        if args.verbose:
            n_removed = mask.shape[0] - mask.sum()
            prnt.status("Removed {} samples".format(n_removed))
        
    #-----
    # step 3: data transformation
    #-----
    
    if model.reducer is not None:
        if args.verbose:
            prnt.status("Transforming feature data")
        
        features = model.reducer.transform(features[:, model.good_bands])
        
    #-----
    # step 4: applying the model
    #-----
    
    if args.verbose:
        prnt.line_break()
        prnt.status("Applying CCBID model to input features")
    
    pred = model.predict(features)
    prob = model.predict_proba(features)
        
    # ensemble the pixels to the crown scale
    if 
    
    # save the ccb model variable
    ccbid.write.pck(args.output, m)
    
    prnt.line_break()
    prnt.status("CCB-ID model training complete!")
    prnt.status("Please see the final output file:")
    prnt.status("  {}".format(args.output))
    prnt.line_break()
    
    # phew


# just run the dang script, will ya?
if __name__ == "__main__":
    main()