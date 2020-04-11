"""Methods for transforming/decomposing reflectance data (e.g., using PCA)
"""
from sklearn.decomposition import PCA as _PCA
from sklearn.preprocessing import StandardScaler
from . import read as _read
import matplotlib.pyplot as plt
import numpy as np

def pca(features, n_pcs=100):
    """PCA transformation function
    
    Args:
        features - the input feature data to transform
        n_pcs    - the number of components to keep after transformation
        
    Returns:
        an array of PCA-transformed features
    """
    reducer = _PCA(n_components=n_pcs, whiten=True)
    return reducer.fit_transform(features)

def myPca(features, n_pcs=100):
    reducer = _PCA(whiten=True)
    #features = StandardScaler().fit_transform(features)
    transformed = reducer.fit_transform(features)

    # plt.figure()
    # plt.plot(np.cumsum(reducer.explained_variance_ratio_))
    # plt.xlabel('Number of Components')
    # plt.ylabel('Variance (%)') #for each component
    # plt.title('Stanford-CCB Explained Variance')
    # plt.grid()
    # plt.show()

    n_pcs = features.shape[1]
    return reducer, transformed[:, 0:n_pcs]

def from_path(path, features, n_features=None):
    """Transformation using a saved decomposition object
    
    Args:
        path       - the path to the saved decomposition object
        features   - the input feature data to transform
        n_features - the number of features to keep after transformation
    """
    # read the object and perform the transformation
    reducer = _read.pck(path)
    transformed = reducer.fit_transform(features)

    # ship the transformed data
    if n_features is None:
        return reducer, transformed
    else:
        return reducer, transformed[:, 0:n_features]

