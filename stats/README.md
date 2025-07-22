# Open Data Monitoring Stats

Extract stats from local database and export it to the dedicated datasets on ODS platform. 

## With Opendatasoft platforms

Populate `./stats/config.json` file with `stats/config.json.sample`.
Create dedicated datasets on your ODS platform. 
The `dataset_uid` field can be founded in the ODS Automation API results.

### Jobs

```
$ crontab -e
```

In the crontab file: 

```bash
30 6 * * * /bin/bash -c 'cd /<path>/<to>/open-data-monitoring && source 
/<path>/<to>/open-data-monitoring/venv/bin/activate && /<path>/<to>/open-data-monitoring/stats/run-stats.sh daily >> 
/<path>/<to>/open-data-monitoring/cron-daily.log 2>&1'
45 6 * * 1 /bin/bash -c 'cd /<path>/<to>/open-data-monitoring && source 
/<path>/<to>/open-data-monitoring/venv/bin/activate && /<path>/<to>/open-data-monitoring/stats/run-stats.sh weekly >> 
/<path>/<to>/open-data-monitoring/cron-weekly.log 2>&1'
```