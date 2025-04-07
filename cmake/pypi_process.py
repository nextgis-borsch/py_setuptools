# -*- coding: utf-8 -*-
import sys
import os
import json

version = '0.0.0'
download_url = ''

def get_latest_version(data):
    for version, files in reversed(data['releases'].items()):
        if files:
            file = files[-1]
            if file['url'].endswith(('tar.gz', 'zip')):
                return version, file['url'], file['upload_time'].replace('T', ' ')
    return None, None, None

with open(sys.argv[1]) as data_file:
    data = json.load(data_file)
    name = data['info']['name']
    version_max = sys.argv[3] if len(sys.argv) > 3 else None

    if version_max:
        for version, files in reversed(data['releases'].items()):
            if version <= version_max and files:
                file = files[-1]
                if file['url'].endswith(('tar.gz', 'zip')):
                    download_url = file['url']
                    date = file['upload_time'].replace('T', ' ')
                    break
    else:
        version, download_url, date = get_latest_version(data)

    version_file_name = os.path.join(os.path.dirname(sys.argv[1]), 'version.str')
    with open(version_file_name, 'w') as version_file:
        pack_name = f"{name}-{version}-{sys.argv[2]}"
        version_file.write(f"{version}\n{date}\n{pack_name}")

print(f"{download_url};{version};{pack_name}")