# Thesis
This code was created as part of the master's thesis 'A digital knowledge infrastructure to provide information on scientific videos and podcasts' and is responsible for the infrastructure's integration and import functionality.
For the other building blocks of the infrastructure see:
 -  [https://github.com/xEatos/dashboardduck](https://github.com/xEatos/dashboardduck) (Web-Page)
 -  [https://github.com/xEatos/searchsnail](https://github.com/xEatos/searchsnail) (Media Search Microservice)

For the code used to analyze the survey in this thesis, see: [https://github.com/xEatos/survey-auswertung](https://github.com/xEatos/survey-auswertung)

If you would like to cite this work:
```
@article{stehr_digitale_2025,
	title = {Eine digitale {Wissensinfrastruktur} zur {Bereitstellung} von {Informationen} über wissenschaftliche {Videos} und {Podcasts}},
	url = {https://repo.uni-hannover.de/handle/123456789/19141},
	doi = {10.15488/18996},
	language = {ger},
	urldate = {2025-04-29},
	author = {Stehr, Niklas},
	month = apr,
	year = {2025},
	note = {Publisher: Hannover : Gottfried Wilhelm Leibniz Universität},
}
```

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

 - To get the authorization to work locally, you need an account at ngrok [https://ngrok.com/](https://ngrok.com/)
 - Install and follow the setup on ngrok [https://dashboard.ngrok.com/get-started/setup/](https://dashboard.ngrok.com/get-started/setup/)
 - Then register a static domain name and use the following command:
```
# to access the integration indri flask server on port 5000 via a tunnle
<path to ngrok executable> http --url=<your-static-domain.app> http://127.0.0.1:5000
```
 - Note: You may have to update the instruction for the wiki service connectors on the integration page
 - [Wikibase Service Connector](https://github.com/xEatos/dashboardduck/blob/main/src/pages/integrationpage/integrationContent/WikibaseCard.tsx)
 - [Miraheze Service Connector](https://github.com/xEatos/dashboardduck/blob/main/src/pages/integrationpage/integrationContent/MirahezeCard.tsx)
