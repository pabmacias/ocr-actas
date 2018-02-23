# Python Flask with Gitlab CI and Deployment to Bluemix

This app demonstrastes a web scraper which uses Gitlab-CI to be tested and 
deployed to Bluemix.

## Requirements
* Python 3.5.3
* Pip 9.0.1

## Run the app locally

1. Instructions:
+ cd into this project's root directory
+ Run `pip install -r requirements.txt` to install the app's dependencies
+ Run `python app.py`
+ Access the running app in a browser at <http://localhost:5000>

## Bluemix

2. Deploy:
+ Change application name in manifest.yml
+ Select the Bluemix Python version to use in runtime.txt
+ cf push <name-of-the-app> 


[Install Python]: https://www.python.org/downloads/
