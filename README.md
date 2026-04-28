# CECS 327 - Assignment 8
Marc Montano and Albert Tan

# Prerequisites
## Create a virtual env
```
python -m venv venv
```

## Source venv
```
source venv/bin/activate
```

## Install requirements
```
pip install -r requirements.txt
```

## Create and add db links to .env

Example:
```
MARC_DB=""
BERT_DB=""
```

# Usage

## Run server.py
```
python server.py
```

## Run client.py
```
python client.py
```

When testing locally use 127.0.0.1 as IP.
```
IP: 127.0.0.1
PORT: 1024
```
Press the number corresponding to the desired query
```
1. What is the average moisture inside our kitchen fridges in the past hours, week and month?
2. What is the average water consumption per cycle across our smart dishwashers in the past hour, week and month?
3. Which house consumed more electricity in the past 24 hours, and by how much?
> 2
```