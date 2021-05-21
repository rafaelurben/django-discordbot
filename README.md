# Discordbot

![PyPI](https://img.shields.io/pypi/v/django-discordbot)
![PyPI - Django Version](https://img.shields.io/pypi/djversions/django-discordbot)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-discordbot)
![PyPI - License](https://img.shields.io/pypi/l/django-discordbot)

![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/rafaelurben/django-discordbot)
![GitHub lines of code](https://img.shields.io/tokei/lines/github.com/rafaelurben/django-discordbot)
![GitHub issues](https://img.shields.io/github/issues/rafaelurben/django-discordbot)
![GitHub pull requests](https://img.shields.io/github/issues-pr/rafaelurben/django-discordbot)

A Discordbot to run in a django environment.

Planned features can be found in the [project board](https://github.com/rafaelurben/django-discordbot/projects/1?fullscreen=true).

Feel free to open an issue or start a pull request. ;)

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

4.  Visit <http://127.0.0.1:8000/admin/discordbot/> to manage the stored data

5.  Run the bot via `python manage.py run-discordbot`
