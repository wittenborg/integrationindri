# integrationindri
 integration mirco service

## Setup

Install the dependencies in a virtual env:

```
python -m venv .venv

.venv/Scripts/activate

pip install -r /path/to/requirements.txt

```

## Get Started

Start server:
```
flask --app server run
```


## NGROK

 - To get the authorization to work locally, you need a account at ngrok [https://ngrok.com/](https://ngrok.com/)
 - Install and follow the setup on ngrok [https://dashboard.ngrok.com/get-started/setup/](https://dashboard.ngrok.com/get-started/setup/)
 - Then register a static domain name and use the following command:
```
# to access the integration indri flask server on port 5000 via a tunnle
<path to ngrok executable> http --url=<your-static-domain.app> http://127.0.0.1:5000
```
 - Note: You may have to update the instruction for the wiki service connectors on the integration page
 - [Wikibase Service Connector](https://github.com/xEatos/dashboardduck/blob/main/src/pages/integrationpage/integrationContent/WikibaseCard.tsx)
 - [Miraheze Service Connector](https://github.com/xEatos/dashboardduck/blob/main/src/pages/integrationpage/integrationContent/MirahezeCard.tsx)
