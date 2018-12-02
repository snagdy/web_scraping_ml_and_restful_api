### How to Launch the Flask Application
1. We are using a Conda environment for this application.
Preferably Conda's provided base environment as it saves us
from doing too much work in getting packages.
This is highly recommended to do in a CMD shell if using Windows.
```
cd <conda_directory>\Scripts\
activate base                               # On Windows
source activate base                        # On Linux
```
2. Next we actually get the packages we need.
```
conda install --name base joblib
conda install --name base -c conda-forge flask-restful
```
3. Depending on your OS (Linux or Windows): 
```
export FLASK_APP=test_rest_api.py       # Linux
$env:FLASK_APP='.\test_rest_api.py'     # Windows (PowerShell)
set FLASK_APP=test_rest_api.py          # Windows (cmd)
```
4. Run the application using:
```
flask run
```
 
---
### RESTful API Syntax
The API syntax is as follows, arguments in any order separated by the ampersand (&):
```
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
```
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
The above response was produced by this query string:
http://\<host:port\>/api?address=50%20St%20Katharine%27s%20Way,%20London%20E1W%201LA&new_build=false&flat_type=Flat&lease_type=Leasehold

This was close to Zoopla's prediction for the area of £786,709 estimated value.

https://www.zoopla.co.uk/for-sale/details/48943432?search_identifier=b5e388742344ddcf8b52da15c2991219

;-)