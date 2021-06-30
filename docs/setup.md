# django-discordbot Documentation

[<- Go back](index.md)

## Quick setup

1. Install `django-discordbot` via pip and/or add `django-discordbot` to your `requirements.txt`

2. Setup a django project if you haven't yet

3. Add `discordbot` to your `INSTALLED_APPS` setting like this:

    ```python
    INSTALLED_APPS = [
        ...
        'discordbot',
        ...
        'django.contrib.admin',
        ...
    ]
    ```

4. Include the discordbot URLconf in your project's `urls.py` like this:

    ```python
    from django.contrib import admin

    urlpatterns = [
        ...
        path('discordbot/', include('discordbot.urls')),
        ...
        path('admin/', admin.site.urls),
        ...
    ]
    ```

5. Run `python manage.py migrate` to create the database models

6. If you haven't yet, create a token for your bot in the [Discord Developer Portal](https://discord.com/developers/applications)

7. You have two options to apply the token:
   - Add it as an argument to the `run-discordbot` command (e.g. `python manage.py run-discordbot --token YOUR_TOKEN`)
   - Save it in the environment variable `DISCORDBOT_TOKEN`

## Usage

- Visit `/admin/discordbot/` while your Django server is running to manage the stored data
- Run the bot via `python manage.py run-discordbot`

The Django server and the bot are independent, i.e. they can be run without eachother.
