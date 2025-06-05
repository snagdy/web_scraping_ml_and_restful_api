#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from mpl_toolkits.mplot3d import Axes3D
from joblib import dump

%matplotlib notebook
#%%
dataset_frame = pd.read_csv("dataset_frame.csv")
#%%
dataset_frame.describe()
#%%
dataset_frame.info()
#%%
# We add a new parameter, which we will use to exclude anomalous lat lon coordinates from bad Open Street Map API data.
    
dataset_frame["latitude_z_score"] = (dataset_frame.latitude - dataset_frame.latitude.mean()) / dataset_frame.latitude.std()
dataset_frame["longitude_z_score"] = (dataset_frame.longitude - dataset_frame.longitude.mean()) / dataset_frame.longitude.std()
#%%
dataset_frame.latitude_z_score.describe()
#%%
dataset_frame.longitude_z_score.describe()
#%%
dropped_nas = dataset_frame.dropna()
dropped_nas.describe()
#%%
dropped_nas.info()
#%%
# We filter out any observations where our latitude or longitude values are more than 1 standard deviations away from the mean.
# All the observations are in London, so any latitude longitude coordinates beyond this range are probably wrong.
df = dropped_nas
df = df[df.latitude_z_score.abs() < 3]
df = df[df.longitude_z_score.abs() < 3]
df = df.drop(df.columns[0],axis=1)
#%%
x = df.longitude
y = df.latitude
fig1 = plt.figure()
scat = plt.scatter(x, y)
#%%
# From the above, we can see that while the first Z score based latitude longitude filtering eliminated most wholly inaccurate
# OSM API response data, it did not eliminate data which was broadly within 3.s.d. on the original dataset, but actually
# incorrect "locally" for London addresses. These anomalies appear to be off near Leeds!
# If we run a scatter graph of the Z-scores from the original dataset, our problem becomes obvious.

x2 = df.longitude_z_score
y2 = df.latitude_z_score
fig2 = plt.figure()
scat = plt.scatter(x2, y2)
#%%
# We will run our filter again by reassiging the latitude and longitude Z-scores and filtering appropriately.

df["latitude_z_score"] = (df.latitude - df.latitude.mean()) / df.latitude.std()
df["longitude_z_score"] = (df.longitude - df.longitude.mean()) / df.longitude.std()
df = df[df.latitude_z_score.abs() < 3]
df = df[df.longitude_z_score.abs() < 3]
df.drop(df.columns[0],axis=1)

x3 = df.longitude
y3 = df.latitude
fig3 = plt.figure()
scat = plt.scatter(x3, y3)
#%%
# We will also create dummy variables for all our non-numerical dataseries.
build_status_dummies = pd.get_dummies(df.build_status)
flat_type_dummies = pd.get_dummies(df.flat_type)
lease_type_dummies = pd.get_dummies(df.lease_type)
category_dummies = pd.get_dummies(df.category)
subcategory_dummies = pd.get_dummies(df.subcategory)


dataframes_set = [df, build_status_dummies, flat_type_dummies, lease_type_dummies, category_dummies, subcategory_dummies]
df = pd.concat(dataframes_set, axis=1).reset_index(drop=True)
df = df.drop(df.columns[0],axis=1)
#%%
df.head()
#%%
cols_to_drop = ["build_status",
                "flat_type",
                "lease_type",
                "category",
                "subcategory",
                "latitude_z_score",
                "longitude_z_score"]

fdf = df.drop(cols_to_drop, axis=1).reset_index(drop=True)
#%%
# We save our last dataset before using this in K-Means clustering labelling.
fdf.to_csv("final_dataset_frame.csv")
fdf.to_json("final_dataset_frame.json")
#%%
x = fdf.longitude
y = fdf.latitude
z = fdf.prices

fig1 = plt.figure()
ax = Axes3D(fig1)

ax.scatter(x, y, z)
#%%
# We will check to see if we have any more non-numeric data, if so, we will drop these series:
fdf.info()
#%%
# It looks like we forgot to get rid of the addresses, so we will do that now.
# fdf = fdf.drop(["addresses"], axis=1)
#%%
# We can now begin the process of clustering our datapoints into lat-lon clusters.

# We will create our dataframe for the K-means Clustering method for labelling our data.
kmm_X = pd.DataFrame([fdf.latitude, fdf.longitude]).T

# We will specify our model to use 10 clusters; we will not explore cluster optimisation here as it is beyond the scope of this
# exercise.

num_clusters = 10
kmeans = KMeans(n_clusters=num_clusters, max_iter=6000, algorithm = "auto", random_state=0)
kmm = kmeans.fit(kmm_X)
id_label = kmm.labels_
#%%
# We will store our model via a joblib dump

dump(kmm, 'k_means_clustering_model.joblib')
#%%
# We will now plot our clusters to see if the labels look correct. We also plot our cluster centres.
fig2 = plt.figure()
for i in range(num_clusters):
    cluster = np.where(id_label == i)[0]
    plt.scatter(kmm_X.latitude[cluster].values, kmm_X.longitude[cluster].values)
plt.scatter(kmm.cluster_centers_[:,0], kmm.cluster_centers_[:,1], c="black", marker="X")
#%%
# We will now add our cluster labels back to our orginal final dataset frame, and derive dummies.
kmm_label_dummies = pd.get_dummies(kmm.labels_)
fdf = pd.concat([fdf, kmm_label_dummies], axis=1)
#%%
# Checking our final variable set.
fdf.info()
#%%
# A final peek at our data to ensure it looks vaguely sensible.
fdf.describe()
#%%
fdf.head()
#%%
# We will save our dataset in a CSV for use in the next Scratchpad where we explore Random Forest Models, which we will pickle.
# We will use our pickled model as the basis for our RESTful API.
fdf.to_csv("random_forest_dataset.csv")
fdf.to_json("random_forest_dataset.json")