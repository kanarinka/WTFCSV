WTFcsv
======

A web app to do provide a simple way to summarize what is in a CSV.
Created for use in data visualization and storytelling classrooms.

Installation
------------

Make sure you havy Python 2.7 (and the pip package manager). Then install the dependencies:

```
pip install -r requirements.pip
```

Testing
-------

Run this command and then visit `localhost:5000` with a web browser

```
python server.py
```

Translating
-----------

To create a translation for a new language, run this command with the right 2-letter 
language code (this example uses spanish - `es`):
```shell
pybabel init -i messages.pot -d translations -l es
```

This creates a new directory structe for the language under `translations/`.
Go into there ad edit the messages.po file to localize all the strings.

Then run this to compile them into a file:
```shell
pybabel compile -d translations
```

When you add or modify strings in the source code, run this to add it to the various `.po` files:
```shell
pybabel extract -F babel.cfg -o messages.pot 
pybabel update -i messages.pot -d translations
```

Deploying
---------

We tend to deploy on Ubuntu machines with Apache and WSGI.

First, prep your machine (if you haven't already):
```
sudo aptitude install python
sudo aptitude install libapache2-mod-wsgi
sudo easy_install pip
```

Then checkout the repo, set up a virtual environment, and get the NLTK libraries you need:
```
cd /var/www/
sudo git clone https://github.com/c4fcm/WTFCSV
cd WTFCSV
virtualenv venv
source venv/bin/activate
pip install -r requirements.pip
```

To configure Apache follow the instructions on how to run a Flask app via WSGI:
  http://flask.pocoo.org/docs/deploying/mod_wsgi/

You'll do something like this in your apache config file `/etc/apache2/sites-available/wtf-csv.conf`:

```xml
<VirtualHost *:80>
        ServerName wtfcsv.awesome

        WSGIDaemonProcess wtfcsv user=www-data group=www-data threads=5 python-path=/var/www/WTFCSV/venv:/var/www/WTFCSV/venv/lib/python2.7/site-packages/
        WSGIProcessGroup wtfcsv
        WSGIScriptAlias / /var/www/WTFCSV/server.wsgi
        LogLevel info

        <Directory /var/www/WTFCSV>
                WSGIProcessGroup wtfcsv
                WSGIApplicationGroup %{GLOBAL}
                Order deny,allow
                Allow from all
        </Directory>
</VirtualHost>
```
