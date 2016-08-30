# ITA Trade Events Lambda

This project provides an AWS Lambda that creates a single JSON document from the XML endpoint 
at [http://emenuapps.ita.doc.gov/ePublic/GetEventXML?StartDT={0}&EndDT={1}](http://emenuapps.ita.doc.gov/ePublic/GetEventXML?StartDT={0}&EndDT={1}) .
It uploads that JSON file to a S3 bucket.

## Prerequisites

Follow instructions from [python-lambda](https://github.com/nficano/python-lambda) to ensure your basic development environment is ready,
including:

* Python
* Pip
* Virtualenv
* Virtualenvwrapper
* AWS credentials

## Getting Started

	git clone git@github.com:GovWizely/lambda-ita-trade-events.git
	cd lambda-ita-trade-events
	mkvirtualenv -r requirements.txt lambda-ita-trade-events

## Configuration

* Define AWS credentials in either `config.yaml` or in the [default] section of ~/.aws/credentials.
* Edit `config.yaml` if you want to specify a different AWS region, role, and so on.
* Make sure you do not commit the AWS credentials to version control

## Invocation

	lambda invoke -v
 
## Deploy

	lambda deploy
