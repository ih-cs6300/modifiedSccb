#per pixel accuracy

import pandas as pd
from sklearn import metrics
import warnings
from sklearn.metrics import accuracy_score

#ignore warnings about depracated packages
warnings.filterwarnings("ignore")

yobs=pd.read_csv("~/test/ccb-id/ccbid/support_files/ResultsTestSet.csv")
df = pd.read_csv("./ecodse-results.csv")
idx = df.groupby(['crown'])['probability'].transform(max) == df['probability']
df = df[idx]
full_data = df.merge(yobs, left_on="crown", right_on="itcID")

print "Confusion Matrix"
print metrics.confusion_matrix(full_data["SpeciesID"], full_data["species"])
print
print
print "Macro F1: " + str(metrics.f1_score(full_data["SpeciesID"], full_data["species"], average='macro'))
print
print
print "Micro F1: " + str(metrics.f1_score(full_data["SpeciesID"], full_data["species"], average='micro'))
splist = list(df['species'].unique())
splist.sort()
print
print
#print metrics.classification_report(full_data["SpeciesID"], full_data["species"], target_names=splist)
print metrics.classification_report(full_data["SpeciesID"], full_data["species"])
print "Accuracy: " + str(accuracy_score(full_data["SpeciesID"], full_data["species"]))
#print "F1: " + str(metrics.f1_score(full_data["SpeciesID"], full_data["species"]))
