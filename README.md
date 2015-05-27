Word-Counter
============

A web app to do simple word frequency counting, bigrams and trigrams. 
Created for use in data visualization and storytelling classrooms.

Installation
------------

Make sure you havy Python 2.7 (and the pip package manager). Then install the dependencies:

```
pip install -r requirements.pip
```

Then install the NLTK libraries you need:
```
python -m nltk.downloader punkt
python -m nltk.downloader stopwords
```

Testing
-------

Run this command and then visit `localhost:5000` with a web browser

```
python server.py
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
sudo git clone https://github.com/c4fcm/Word-Counter
cd Word-Counter
virtualenv venv
source venv/bin/activate
pip install nltk
pip install flask
pip install flask-uploads
pip install unicodecsv
sudo pip install nltk
sudo python -m nltk.downloader -d /usr/share/nltk_data punkt
sudo python -m nltk.downloader -d /usr/share/nltk_data stopwords
```

To configure Apache follow the instructions on how to run a Flask app via WSGI:
  http://flask.pocoo.org/docs/deploying/mod_wsgi/

You'll do something like this in your apache config file `/etc/apache2/sites-available/word-counter.conf`:

```xml
<VirtualHost *:80>
        ServerName my-word-counter.awesome

        WSGIDaemonProcess wordcounter user=www-data group=www-data threads=5 python-path=/var/www/Word-Counter/venv:/var/www/Word-Counter/venv/lib/python2.7/site-packages/
        WSGIProcessGroup wordcounter
        WSGIScriptAlias / /var/www/Word-Counter/server.wsgi
        LogLevel info

        <Directory /var/www/Word-Counter>
                WSGIProcessGroup wordcounter
                WSGIApplicationGroup %{GLOBAL}
                Order deny,allow
                Allow from all
        </Directory>
</VirtualHost>
```
