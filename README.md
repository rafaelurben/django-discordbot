# Discordbot

A Discordbot to run in a django-environment.

## Requirements

Django Admin is installed and activated.

## Quick start

1.  Add "discordbot" to your INSTALLED_APPS setting like this::

    ```python
    INSTALLED_APPS = [
        ...
        'discordbot',
    ]
    ```

2.  Include the discordbot URLconf in your project urls.py like this::

    ```python
    path('discordbot/', include('discordbot.urls')),
    ```

3.  Run `python manage.py migrate` to create the models.

4.  Visit <http://127.0.0.1:8000/admin/discordbot/>

5.  Run the bot via `python manage.py run-discordbot`
