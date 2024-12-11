# twitch-drop-notifier

Get notified when a new drop is available on Twitch

## Development

- [Python 3.13](https://www.python.org/downloads/) is required to run this project.

```bash
# Create and activate a virtual environment.
python -m venv .venv
source .venv/bin/activate

# Remember to run `source .venv/bin/activate` before running the following commands:
# You will need to run this command every time you open a new terminal.
# VSCode will automatically activate the virtual environment if you have the Python extension installed.

# Install dependencies.
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run the following to get passwords for the .env file.
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Rename .env.example to .env and fill in the required values.
# Only DJANGO_SECRET_KEY is required to run the server.
# EMAIL_HOST_USER, EMAIL_HOST_PASSWORD and DISCORD_WEBHOOK_URL can be left empty if not needed.
mv .env.example .env

# Run the migrations.
python manage.py migrate

# Create cache table.
python manage.py createcachetable

# Create a superuser.
python manage.py createsuperuser

# Run the server.
python manage.py runserver

# Run the tests.
pytest
```
