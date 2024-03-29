#!/bin/bash

PYTHON_VERSION=2.7.8
POSTGRES_VERSION=9.3.5
BASH_PROFILE="$HOME/.bash_profile"

#
# Check if Homebrew is installed
#
which -s brew
if [[ $? != 0 ]] ; then
    # Install Homebrew
    # https://github.com/mxcl/homebrew/wiki/installation
    echo "Installing Homebrew"
    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    echo "export PATH=/usr/local/bin:\$PATH" >> $BASH_PROFILE
    source $BASH_PROFILE
else
    echo "Updating Homebrew packages"
    brew update
fi

#
# Check if Python is installed
#
if ! brew list -1 | grep "^python$"; then
    echo "Installing Homebrew Python 2.7"
    brew install python
fi

#
# Check if Heroku toolbelt is installed
#
which -s heroku
if [[ $? != 0 ]] ; then
    # Install Heroku toolbelt
    echo "Downloading Heroku toolbelt"
    open https://signup.heroku.com/dc
    open https://toolbelt.heroku.com/
    read -p "Press return when done with Heroku installation"
else
    echo "Updating Heroku"
    heroku update
fi
 
#
# Heroku setup
#
heroku login

#
# Check if Postgres is installed
#
psql --version | grep ${POSTGRES_VERSION}
if [[ $? != 0 ]] ; then
    echo "Please install Postgres v9.3.5"
    echo "Make sure to remove any previous versions of Postgres you have"
    open https://github.com/PostgresApp/PostgresApp/releases/download/9.3.5.0/Postgres-9.3.5.0.zip
    read -p "Press return when done with Postgres installation"
    echo "" >> $BASH_PROFILE
    echo "### Add Postgres to the path (Down)" >> $BASH_PROFILE
    echo "export PATH=/Applications/Postgres.app/Contents/Versions/9.3/bin:\$PATH" >> $BASH_PROFILE
    source $BASH_PROFILE
fi

#
# Install GeoDjango requirements.
#
brew install geos
brew install gdal
brew install proj

#
# Setup the database
#
# TODO: Go into the postgres database before creating the postgis extension
if ! psql -lqt | cut -d \| -f 1 | grep -w down; then
    echo "Creating database"
    psql -c "CREATE USER down WITH CREATEDB PASSWORD 'down';"
    psql -c "CREATE DATABASE down OWNER down ENCODING 'UTF8';"
    psql -c "CREATE EXTENSION postgis;"
else
    echo "ERROR: A database with the name 'down' already exists"
    echo "Please remove that database, then run this script again"
    exit 0
fi

#
# Check if virtualenvwrapper is installed
#
which -s virtualenvwrapper.sh
if [[ $? != 0 ]] ; then
    echo "Installing virtualenvwrapper"
    sudo pip install virtualenvwrapper
    echo "" >> $BASH_PROFILE
    echo "### Virtualenvwrapper for Python virtual environments (Down)" >> $BASH_PROFILE
    echo "export WORKON_HOME=$HOME/.virtualenvs" >> $BASH_PROFILE
    echo "source /usr/local/bin/virtualenvwrapper.sh" >> $BASH_PROFILE
    source $BASH_PROFILE
else
    source `which virtualenvwrapper.sh`
fi

#
# Create virtual environment
#
echo "Creating a virtual environment"
mkvirtualenv down

#
# Install Python requirements
#
echo "Installing requirements"
pip install -r requirements.txt
