#!/usr/bin/env python
import os.path
import subprocess
import datetime
import gzip

DOKKU_CMD = '/usr/local/bin/dokku'
DOKKU_ROOT = '/home/dokku'
VOLUME_STORAGE = os.environ.get('BACKUP_ROOT', '/home/dokku/.volumes')
BACKUP_ROOT = os.environ.get('BACKUP_ROOT', '/var/backups/data')
BACKUP_VOLUMES = os.path.join(BACKUP_ROOT, 'volumes/')
BACKUP_DBS = os.path.join(BACKUP_ROOT, 'dbs/')
BACKUP_DOKKU = os.path.join(BACKUP_ROOT, 'dokku/')

now = datetime.datetime.utcnow()

for directory in [BACKUP_VOLUMES, BACKUP_DBS, BACKUP_DOKKU]:
    try:
        os.makedirs(directory)
    except OSError:
        pass


# Get databases
dbs = [dbline.split(' ', 1)[0] for dbline in
       subprocess.check_output([DOKKU_CMD, 'postgres:list']).split('\n')[1:] if dbline]


for db in dbs:
    filename = 'postgresql_backup_{db}_{date}.sql.gz'.format(db=db, date=now.isoformat())
    output = subprocess.check_output([DOKKU_CMD, 'postgres:export', db])
    with gzip.open(os.path.join(BACKUP_DBS, filename), 'wb') as f:
        f.write(output)


for directory in os.listdir(VOLUME_STORAGE):
    if 'no-backup' in directory:
        continue
    filename = 'volume_backup_{volume}_{date}.tar.gz'.format(volume=directory, date=now.isoformat())
    filename = os.path.join(BACKUP_VOLUMES, filename)
    subprocess.check_output(['tar', 'zcf', filename, '-C', VOLUME_STORAGE,
                             os.path.join(VOLUME_STORAGE, directory)])

for app in subprocess.check_output([DOKKU_CMD, 'apps']).split('\n')[1:]:
    if not app:
        continue
    # Backup dokku
    filename = 'dokku_backup_{app}_{date}.tar'.format(date=now.isoformat(), app=app)
    filename = os.path.join(BACKUP_DOKKU, filename)
    subprocess.check_output(['tar', 'zcf', filename, '-C', DOKKU_ROOT, os.path.join(DOKKU_ROOT, app)])

# Chown
subprocess.check_output(['/bin/chown', '-R', 'backup:backup', BACKUP_ROOT])
