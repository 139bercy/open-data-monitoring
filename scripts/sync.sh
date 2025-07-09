#!/bin/bash

# Sync local db with distant db

SERVER=$1
DATE=$(date +"%Y-%m-%d")

echo "Dump and create database backup, sync with local"
ssh "$SERVER" "sudo -u postgres pg_dump -h localhost -p 5433 -d odm -F c" > odm-"$DATE".dump
pg_dump -h localhost -U postgres -d odm -p 5432 -F c -f odm-"$DATE"-backup.dump
pg_restore -h localhost -U postgres -d odm -c odm-"$DATE".dump