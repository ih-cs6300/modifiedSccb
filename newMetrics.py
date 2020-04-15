import pandas as pd
from sklearn import metrics
import warnings

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
print metrics.classification_report(full_data["SpeciesID"], full_data["species"], target_names=splist)
print "accuracy: " + str(metrics.accuracy_score(full_data["SpeciesID"], full_data["species"], normalize=True))

incorrectDf = full_data[full_data["SpeciesID"] != full_data["species"]]
incorrectDf = incorrectDf[["itcID", "SpeciesID", "GenusID"]]
incorrectDf = incorrectDf.rename(columns= {"itcID": "crown_id", "SpeciesID": "species_id", "GenusID": "genus_id"})
incorrectDf.to_csv("testSetErrors.csv", header=True, index=False)
