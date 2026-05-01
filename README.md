# CECS 327 - Assignment 8
Marc Montano and Albert Tan

# Connection and Data Retrieval
The system establishes connections to two distinct PostgreSQL databases—Marc’s and Albert’s—using the psycopg2 library. These connections are managed through a db_connect context manager, which ensures that both BERT_DB and MARC_DB are accessed and closed safely. Data is retrieved by executing dynamic SQL queries that parse JSONB payloads using the ->> operator to extract specific sensor measurements and timestamps.

# Distributed Query Processing
Distributed query processing is implemented at the application level within the server.py script. When a user requests a metric like "Moisture Level" or "Electricity Usage," the server executes queries across multiple database instances and then aggregates the results in Python. For instance, the query_electricity function fetches data from both Marc’s and Albert’s databases, processes the raw values into a unified format, and performs a comparative analysis before sending the final result to the client.

# Query Completeness Determination
Query completeness is determined by combining local and shared data sources to cover a full requested time interval. The system uses a DATA_SHARE_TIME threshold to decide where data resides:

- For periods before the sharing threshold, the system queries the owner's original database.

- For periods after the threshold, it queries the shared database where the data was replicated.

The server then merges these datasets to ensure no gaps exist in the 24-hour, weekly, or monthly reports.

# DataNiz Metadata and Data Sharing
DataNiz metadata and sharing are utilized to facilitate data exchange between the two house environments:

- Metadata: Specific keys within the IoT payload, such as board_name, are used as metadata filters to identify which physical device generated a reading within a shared table.

- Data Sharing: The system utilizes a forward-only replication model where Albert's sensor data is shared with Marc's database (neondata_virtual) after a specific epoch. The server logic is programmed to recognize this sharing state, checking both the shared and original sources to provide a complete picture of the smart house metrics.

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
