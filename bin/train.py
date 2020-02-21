#! /usr/bin/env python
"""Trains a ccbid model to classify tree species
"""

import sys
import ccbid
import numpy as np
from ccbid import args
from ccbid import prnt
from sklearn import metrics
from sklearn import model_selection
from sklearn.svm import SVC

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

    # set up the arguments for dealing with file i/o
    args.input(parser)
    args.crowns(parser)
    args.output(parser)
    args.ecodse(parser)
    args.reducer(parser)
    args.n_features(parser)
    args.models(parser)
    args.bands(parser)

    # arguments to turn on certain flags or set specific parameters
    args.remove_outliers(parser)
    args.split(parser)
    args.tune(parser)
    args.grids(parser)
    # args.feature_selection(parser)
    args.cpus(parser)
    args.verbose(parser)

    # set up the arguments for dealing with 
    return parser.parse_args(sys.argv[1:])


# set up the logic to parse command line arguments and ensure consistent logic
def arg_logic(argv):
    """Parses the command line arguments to ensure consistency prior to running the main script
    
    Args:
        args - the arguments returned from the argparse object
        
    Returns:
        None. This function updates the args object
    """

    # if the ECODSE flag is set, override whatever is set at the command line
    if argv.ecodse:
        argv.input = args.path_training
        argv.crowns = args.path_crowns
        argv.reducer = args.path_reducer
        argv.n_features = 100  # | 100 --> 93% | 50 --> 93%  | 20 --> 92% |  5 10 20 30 40 50 80 90 100 120 35
        argv.models = [args.path_gbc, args.path_rfc]
        argv.bands = args.path_bands
        argv.remove_outliers = 'PCA'
        argv.threshold = 3
        argv.split = 'sample'
        argv.tune = False
        argv.feature_selection = False


# set up the main script function
def main():
    """The main function for train.py
    
    Args:
        None - just let it fly
        
    Returns:
        None - this runs the dang script
    """

    # first read the command line arguments
    argv = parse_args()

    # parse the logic to make sure everything runs smoothly
    arg_logic(argv)

    # set the seed for reproducibility (to the year the CCB was founded)
    np.random.seed(1984)

    # -----
    # step 1. reading data
    # -----

    if argv.verbose:
        prnt.line_break()
        prnt.status("Reading input data")

    training_id, features, newFeatures = ccbid.read.training_data(argv.input)
    crown_id, species_id, species_name = ccbid.read.species_id(argv.crowns)
    wavelengths, good_bands = ccbid.read.bands(argv.bands)
    species_unique, crowns_unique, crown_labels = \
        ccbid.match_species_ids(training_id, crown_id, species_id)

    # -----
    # step 2. outlier removal
    # -----

    if argv.remove_outliers is not None:
        if argv.verbose:
            prnt.status("Removing outliers using {}".format(argv.remove_outliers))

        # currently only one version of outlier removal
        if argv.remove_outliers == 'PCA':
            mask = ccbid.outliers.with_pca(features[:, good_bands], thresh=argv.threshold)

        # subset all data using the mask for future analyses
        features = features[mask, :]
        newFeatures = newFeatures[mask, :]
        training_id = training_id[mask]
        crown_labels = crown_labels[mask]

        # report on the number of samples removed
        if argv.verbose:
            n_removed = mask.shape[0] - mask.sum()
            prnt.status("Removed {} samples".format(n_removed))

    # -----
    # step 3: data transformation and resampling
    # -----

    # first, transform the data
    if argv.reducer is not None:
        if argv.verbose:
            prnt.status("Transforming feature data")

        catMatrix = np.hstack([features[:, good_bands], newFeatures])
        reducer, features = ccbid.transform.myPca(catMatrix, argv.n_features) #ccbid.transform.from_path(argv.reducer, features[:, good_bands], argv.n_features)
        #reducer, features = ccbid.transform.from_path(argv.reducer, features[:, good_bands], argv.n_features)

    # ok, now to do something kinda weird
    # in the original submission, I had resampled the data, then split into train/test sets
    # this is bad practice, since I used the same data to train/calibrate/test the model
    # so we'll keep that consistent here for reproducibility, but we'll do it better for other runs

    if argv.verbose:
        prnt.status("Splitting train / test data")

    if argv.ecodse:
        features, crown_labels, training_id = ccbid.resample.uniform(features, crown_labels, other_array=training_id)

    # set the label to split the data on samples or crowns
    if argv.split == 'sample':
        stratify = crown_labels
    elif argv.split == 'crown':
        # ok, so, I think this is actually not quite what I want it to be, but
        # I think it will work pretty well
        stratify = training_id

    # we'll split the data into three parts - model training, model calibration, and model test data
    xtrain, xcalib, ytrain, ycalib, strain, scalib = model_selection.train_test_split(
        features, crown_labels, stratify, test_size=0.5, stratify=stratify)

    xctrain, xctest, yctrain, yctest, sctrain, sctest = model_selection.train_test_split(
        xcalib, ycalib, scalib, test_size=0.5, stratify=scalib)

    X_train, X_test, y_train, y_test = model_selection.train_test_split(features, crown_labels, test_size=0.5, random_state=0)


    # -----
    # step 4: model training
    # -----

    if argv.verbose:
        prnt.line_break()
        prnt.status("Starting model training")

    # first, load up the models
    models = []
    for m in argv.models:
        models.append(ccbid.read.pck(m))

    # then create the ccbid model object
    m = ccbid.model(models=models, average_proba=False, labels=species_unique, good_bands=good_bands)

    # pass a reducer on to the model object if set
    if argv.reducer is not None:
        m.reducer = reducer
        m.n_features_ = argv.n_features

    # tune 'em if you got 'em
    if argv.tune or 1 == 0:
        # deal with this guy later
        #prnt.error("Sorry - not yet implemented!")
        print("Tuning")
        # parameter_grid = [{
        #                         'n_estimators': [20, 50, 200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000],
        #                         'max_depth': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, None],
        #                         'min_samples_split': [2, 5, 10],
        #                         'min_impurity_split': [1e-8, 1e-7, 1e-6],
        #                         'learning_rate': [0.01, 0.1, 0.2],
        #                         'max_features': ['log2', 'sqrt', None],
        #                         'min_samples_leaf': [1, 2, 4],
        #                     },
        #
        #                     {
        #                         'n_estimators': [20, 50, 200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000],
        #                         'max_depth': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, None],
        #                         'min_samples_split': [2, 5, 10],
        #                         'min_impurity_split': [1e-8, 1e-7, 1e-6],
        #                         'criterion': ['gini', 'entropy'],
        #                         'bootstrap': [True, False],
        #                         'max_features': ['auto', 'sqrt'],
        #                         'min_samples_leaf': [1, 2, 4],
        #                     }
        # ]

        parameter_grid = []
        #parameter_grid.append(m.models_[0].get_params())
        #parameter_grid.append(m.models_[1].get_params())

        parameter_grid.append( {'max_depth': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, None]} )
        parameter_grid.append( {'max_depth':  [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, None]} )

        tuned_params = []
        for idx in range(len(m.models_)):
            print("Model " + str(idx))
            print("\n")
            print("# Tuning hyper-parameters for %s\n" % 'f1_macro')

            clf = model_selection.GridSearchCV(m.models_[idx], parameter_grid[idx], verbose=2, scoring='f1_macro', n_jobs = 2)
            #clf = model_selection.RandomizedSearchCV(estimator = m.models_[idx], param_distributions = parameter_grid[idx], n_iter = 5, cv = 5, verbose=2, random_state=42, n_jobs = 2, scoring='f1_macro')
            clf.fit(X_train, y_train)
            print("Best parameters set found on development set:")
            print("\n")
            print(clf.best_params_)

            #append save best parameters found
            tuned_params.append(clf.best_params_)
            print("\n")
            print("Grid scores on development set:")
            print("\n")
            means = clf.cv_results_['mean_test_score']
            stds = clf.cv_results_['std_test_score']
            for mean, std, params in zip(means, stds, clf.cv_results_['params']):
                print("%0.3f (+/-%0.03f) for %r" % (mean, std * 2, params))
            print("\n")

            print("Detailed classification report:")
            print("\n")
            print("The model is trained on the full development set.")
            print("The scores are computed on the full evaluation set.")
            print("\n")
            y_true, y_pred = y_test, clf.predict(X_test)
            print(metrics.classification_report(y_true, y_pred))
            print("\n")

    #set parameters to best parameters found
    #m.set_params(tuned_params)

    # calculate the sample weights then fit the model using the training data
    wtrain = ccbid.get_sample_weights(ytrain)
    m.fit(xtrain, ytrain, sample_weight=wtrain)

    # assess the fit on test data
    if argv.verbose:
        prnt.status("Assessing model training performance")
        ypred = m.predict(xctest)
        yprob = m.predict_proba(xctest)

        for i in range(m.n_models_):
            prnt.status("Model {}".format(i + 1))
            print(metrics.classification_report(yctest, ypred[:, i], target_names=species_unique))
            prnt.model_report(yctest, ypred[:, i], yprob[:, :, i])

    # next, calibrate prediction probabilities
    m.calibrate(xctrain, yctrain)

    # assess the fit on test data
    if argv.verbose:
        prnt.status("Asessing model calibration")
        ypred = m.predict(xctest, use_calibrated=True)
        yprob = m.predict_proba(xctest, use_calibrated=True)

        #keep track of m0 and m1 micro and macro f1 to calculate average
        microf1 = []
        macrof1 = []
        for i in range(m.n_models_):
            prnt.status("Model {}".format(i + 1))
            print(metrics.classification_report(yctest, ypred[:, i], target_names=species_unique))
            prnt.model_report(yctest, ypred[:, i], yprob[:, :, i])
            microf1.append(metrics.f1_score(yctest, ypred[:, i], average='micro'))
            macrof1.append(metrics.f1_score(yctest, ypred[:, i], average='macro'))
            #print("Micro F1: " + str(metrics.f1_score(yctest, ypred[:, i], average='micro')))
            #print("Macro F1: " + str(metrics.f1_score(yctest, ypred[:, i], average='macro')))
            #print()

        print("Avg micro-f1: " + str(sum(microf1)/2))
        print("Avg macro-f1: " + str(sum(macrof1)/2))
        print("\n")

    # finally, re-run the training/calibration using the full data set 
    if argv.verbose:
        prnt.status("Fitting final model")

    m.fit(np.append(xtrain, xctest, axis=0), np.append(ytrain, yctest))
    m.calibrate(xctrain, yctrain)
    m.average_proba_ = True

    # save the ccb model variable
    ccbid.write.pck(argv.output, m)

    prnt.line_break()
    prnt.status("CCB-ID model training complete!")
    prnt.status("Please see the final output file:")
    prnt.status("  {}".format(argv.output))
    prnt.line_break()

    # phew


# just run the dang script, will ya?
if __name__ == "__main__":
    main()
