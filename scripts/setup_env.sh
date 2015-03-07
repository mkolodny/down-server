#!/bin/bash

PYTHON_VERSION=2.7.8
POSTGRES_VERSION=9.4.1
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
    export PATH="/usr/local/bin:$PATH"
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
    echo "Please install Postgres v9.4.1"
    open http://postgresapp.com/
    read -p "Press return when done with Postgres installation"
    echo "" >> $BASH_PROFILE
    echo "### Add Postgres to the path (Down)" >> $BASH_PROFILE
    echo "export PATH=/Applications/Postgres.app/Contents/Versions/9.4/bin:$PATH" >> $BASH_PROFILE
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
if ! psql -lqt | cut -d \| -f 1 | grep -w down; then
    echo "Creating database"
    psql -c "CREATE USER down WITH CREATEDB PASSWORD 'down';"
    psql -c "CREATE DATABASE down OWNER down ENCODING 'UTF8';"
    psql -c "CREATE EXTENSION postgis;"
else
    echo "Error: a database and/or user named 'down' already exists."
    echo "Please remove them, then run the script again."
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
