# Stratégies de Rollback

En cas d'échec du déploiement ou de bug critique en production, voici les options pour revenir en arrière.

## 1. Rollback du Code et du Front (Stratégie Atomique)

La meilleure solution est d'utiliser des **symlinks** pour pointer vers des versions horodatées.

### Architecture suggérée :
- `/var/www/odm/releases/20260305_120000`
- `/var/www/odm/releases/20260305_134000`
- `/var/www/odm/current` -> (symlink vers la dernière release)

### Procédure de rollback :
Il suffit de faire pointer le symlink `current` vers la version précédente et de redémarrer le service.
```bash
ln -sfn /var/www/odm/releases/VERSION_PRECEDENTE /var/www/odm/current
sudo systemctl restart odm-api
```

## 2. Rollback de la Base de Données

Les migrations SQL sont souvent difficiles à inverser automatiquement.

### Solutions :
- **Backups réguliers** : Automatiser un `pg_dump` avant chaque déploiement.
- **Transactions** : Toujours essayer d'encapsuler les patches SQL dans des `BEGIN;` ... `COMMIT;`.
- **Scripts de "Down"** : Pour chaque `patch.sql`, créer un `patch.down.sql` qui annule les changements (ex: suppression de colonne, suppression de table).

## 3. Rollback via Git

Si vous n'utilisez pas de symlinks, vous pouvez forcer un retour arrière sur le serveur :
```bash
git reset --hard HEAD@{1}
# Ou vers un tag connu
git checkout v1.2.3
sudo systemctl restart odm-api
```
