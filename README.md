# Web Scraping ML and RESTful API
### Purpose

This is a showcase of a pickled ML model hosted within a Flask RESTful application, 
where the endpoint exposes inputs for inference from the trained model.

The model predicts house prices in London based on its parameters.

### NOTICE:

- The below is all in need of an update, since this project was originally written in Python 2.x, in 2019!
- Modernisation to Python 3.x and modern standards is a work in-progress.
- Retraining the model (Random Forest Regressor, K-Means Clustering feature engineering, etc) on new web-scraped data is on the TODO list.

---

### How to Launch the Flask Application
1. We are using a Conda environment for this application.

```bash
conda env create -f environment.yml
```


2. Depending on your OS (Linux or Windows): 

Linux
```bash
export FLASK_APP=flask_prediction_api.py       # Linux
```

Windows
```
$env:FLASK_APP='.\flask_prediction_api.py'     # Windows (PowerShell)
set FLASK_APP=flask_prediction_api.py          # Windows (cmd)
```
3. Run the application using:

```bash
flask run
```
 
---
### RESTful API Syntax
The API syntax is as follows, arguments in any order separated by the ampersand (&):
```http request
http://<host:port>/api?address=<address>&new_build=<new_build>&flat_type=<flat_type>&lease_type=<lease_type>
```
Where the required arguments specified are as explained below:

| Syntax Element | Meaning |
| --- | --- |
| \<host:port\> | The host's IP or domain name and Flask's listening port. |
| \<address\> | The address you want to query, spaces are fine.|
| \<new_build\> | lowercase "true" or "false", no quotes necessary. |
| \<flat_type\> | Provide a flat type as "Detached", "Flat", "Semi Detached", "Terraced"; spaces are expected, no quotes.|
| \<lease_type\> | Provide a lease type as "Freehold" or "Leasehold".||
 
---
### Expected RESTful API Output
You can expect the output to be a dictionary as below:
```json
{
  "Model Inputs": {
    "address": "50 St Katharine's Way, London E1W 1LA", 
    "flat_type": "Flat", 
    "lease_type": "Leasehold", 
    "new_build": "false"
  }, 
  "Predicted House Price": 767905.0, 
  "cod": 200
}
```
#### Trivia:

NOTE: this is outdated! Last checked in 2019.

The above response was produced by this query string:
http://\<host:port\>/api?address=50%20St%20Katharine%27s%20Way,%20London%20E1W%201LA&new_build=false&flat_type=Flat&lease_type=Leasehold

This was close to Zoopla's prediction for the area of £786,709 estimated value.

https://www.zoopla.co.uk/for-sale/details/48943432?search_identifier=b5e388742344ddcf8b52da15c2991219

;-)