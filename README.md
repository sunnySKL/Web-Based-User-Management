# 4353GP
##Group Name - Toronto


# Project Overview
The first iteration of the group project aims to provide you with hands-on experience in building a web-based user management system that leverages Office365 for authentication.

# Setup and running locally
After creating your virtual envirmoment, you can install the dependicies using
```bash
pip3 install -r requirements.txt
```

To run it locally
```bash
flask --app wsgi:app run
```

# Config
Default and global config is located under `root/config.py`.

# Secrets
To add your own secrets, create your own under `app/instances/config.py`

