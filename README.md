[![CircleCI](https://circleci.com/gh/GovWizely/lambda-ita-trade-events/tree/master.svg?style=svg)](https://circleci.com/gh/GovWizely/lambda-ita-trade-events/tree/master)
[![Maintainability](https://api.codeclimate.com/v1/badges/57a7c7efe105b2036acf/maintainability)](https://codeclimate.com/github/GovWizely/lambda-ita-trade-events/maintainability)
[![Dependabot Status](https://api.dependabot.com/badges/status?host=github&repo=GovWizely/lambda-ita-trade-events)](https://dependabot.com)

# ITA Trade Events Lambda

This project provides an AWS Lambda that creates a single JSON document from two sources:
* the XML endpoint at [http://emenuapps.ita.doc.gov/ePublic/GetEventXML?StartDT={0}&EndDT={1}](http://emenuapps.ita.doc.gov/ePublic/GetEventXML?StartDT={0}&EndDT={1})  
* an Excel spreadsheet of Trade Events Partnership Program (TEPP) events in the S3 bucket  

It uploads that JSON file to a S3 bucket.

## Prerequisites

- This project is tested against Python 3.7+ in [CircleCI](https://app.circleci.com/github/GovWizely/lambda-ita-trade-events/pipelines).

## Getting Started

	git clone git@github.com:GovWizely/lambda-ita-trade-events.git
	cd lambda-ita-trade-events
	mkvirtualenv -p /usr/local/bin/python3.8 -r requirements-test.txt errors

If you are using PyCharm, make sure you enable code compatibility inspections for Python 3.7/3.8.

### Tests

```bash
python -m pytest
```

## Configuration

* Define AWS credentials in either `config.yaml` or in the [default] section of `~/.aws/credentials`. To use another profile, you can do something like `export AWS_DEFAULT_PROFILE=govwizely`.
* Edit `config.yaml` if you want to specify a different AWS region, role, and so on.
* Make sure you do not commit the AWS credentials to version control.

## Invocation

	lambda invoke -v
 
## Deploy
    
To deploy:

	lambda deploy --requirements requirements.txt
