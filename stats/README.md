# Open Data Monitoring Stats

Extract stats from local database and export it to the dedicated datasets on ODS platform.

## 📊 Catalogue des Indicateurs

Le catalogue des rapports est auto-généré à partir de la configuration `config.json` :

```bash
./stats/run-stats.sh --list
```

## 🚀 Utilisation

### Lancer une fréquence complète
```bash
./stats/run-stats.sh daily
./stats/run-stats.sh weekly
```

### Lancer un rapport spécifique par son nom
```bash
./stats/run-stats.sh mbi-stats
./stats/run-stats.sh monthly-performance
```

### Mode "Dry Run" (pas d'envoi ODS)
```bash
./stats/run-stats.sh mbi-stats --no-push
```

## ⚙️ Configuration ODS

1. Remplissez `./stats/config.json` à partir de `stats/config.json.sample`.
2. Créez les datasets cibles sur votre plateforme ODS.
3. Le champ `dataset_uid` se trouve dans les résultats de l'API Automation d'ODS.

### Automatisation (Crontab)

```bash
# Exemple crontab
30 6 * * * /bin/bash -c 'cd /path/to/project && source venv/bin/activate && ./stats/run-stats.sh daily >> cron-daily.log 2>&1'
```
