#%%
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error as MAE
from datetime import datetime
from matplotlib import pyplot as plt
from joblib import dump

%matplotlib notebook
#%%
# First we load our dataset from the previous scratchpad with K-means Cluster Lables.

data_filepath = "random_forest_dataset.csv"
df = pd.read_csv(data_filepath)
#%%
# We will check our data's profile before proceeding.

df.info()
#%%
# We need to drop our first unnamed column, which is an artefact of importing the dataset from a CSV.

df = df.drop(df.columns[0], axis=1)
df.head()
#%%
# We need to convert our sales_dates back to datetime objects:

df.sale_dates = [datetime.strptime(date, "%Y-%m-%d") for date in df.sale_dates]
#%%
# Our sales dates should now look a lot better.

df.info()
#%%
df.head()
#%%
# We will now look at the summary stats of our data to see if we have something sensible.

df.describe()
#%%
# We will now set up our dependent variable y, and our independent variables X.

y = df.prices
X = df.drop(["prices"], axis=1)

# We will sadly need to drop sale_dates too, as datetime variables are not appropriate for this type of model.
# Another day, we can explore the impact of date of sale category dummies on the sale price.

X = X.drop(["sale_dates"], axis=1)
#%%
# We will inspect our final list of X variables feeding our model.
X.info()
#%%
# We describe our summary stats for price data, to get a feel for the distribution, and what could be sensible as model output.
y.describe()
#%%
# We also explore our numerical (these should be the only type!) independent variables for a gauge of their distribution.
X.describe()
#%%
forest_model_naive = RandomForestRegressor(random_state=1)
forest_model_naive.fit(X, y)
y_hat = forest_model_naive.predict(X)
#%%
# We can observe the Mean Absolute Error of our naive model without splitting  the data into a training set.

MAE(y, y_hat)
#%%
# We will now split our data and look at the out of sample predictive power of our trained model instead.

train_X, val_X, train_y, val_y = train_test_split(X, y, random_state=0)

forest_model_trained = RandomForestRegressor(random_state=1)
forest_model_trained.fit(train_X, train_y)
y_hat_trained = forest_model_trained.predict(val_X)
#%%
# We can now look at our out-of-sample model prediction MAE for verification.

MAE(val_y, y_hat_trained)
#%%
# It becomes abundantly clear that our naive model is better in this low sample size situation.
# We will optimise it as best as we can given other parameters we can control, like maximum tree leaf nodes.

def get_MAE(max_leaf_nodes, X, y, model_type):
    model = model_type(max_leaf_nodes=max_leaf_nodes, random_state=0)
    model.fit(X, y)
    y_hat = model.predict(X)
    return MAE(y, y_hat)
#%%
rfr_utility_func_data = {'max_leaf_nodes' : [], 'MAE': []}

for max_leaf_nodes in [i**2 for i in range(2, 50)]:
    my_mae = get_MAE(max_leaf_nodes, X, y, RandomForestRegressor)
    rfr_utility_func_data['max_leaf_nodes'].append(max_leaf_nodes)
    rfr_utility_func_data['MAE'].append(my_mae)
#%%
rfr_utility_function_plot = pd.DataFrame.from_dict(rfr_utility_func_data)
rfr_minimum_mae = rfr_utility_function_plot.MAE.min()
rfr_best_max_nodes = rfr_utility_function_plot.max_leaf_nodes[rfr_utility_function_plot.MAE.idxmin]

print(f"The minimum MAE is {rfr_minimum_mae} in an RFR model with {rfr_best_max_nodes} maximum leaf nodes")

plt.plot(rfr_utility_function_plot.max_leaf_nodes, rfr_utility_function_plot.MAE)
#%%
# We will pick this model with the suggested maximum leaf nodes above, and serialise it for use in our API.

serialised_model = RandomForestRegressor(random_state=1, max_leaf_nodes=rfr_best_max_nodes)
serialised_model.fit(X, y)

#%%
# We will now dump the model to a file via joblib, which handles numpy arrays better than pickle.
dump(serialised_model, "serialised_random_forest_regressor.joblib")