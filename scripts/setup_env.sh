#!/bin/bash

PYTHON_VERSION=2.7.8
POSTGRES_VERSION=9.4.1
BASHRC="~/.bashrc"

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
    source $BASHRC
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
    curl -O https://toolbelt.heroku.com/download/osx
    open /tmp/heroku-toolbelt.pkg
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
fi

#
# Check if virtualenvwrapper is installed
#
which -s virtualenvwrapper.sh
if [[ $? != 0 ]] ; then
    echo "Installing virtualenvwrapper"
    sudo pip install virtualenvwrapper
    echo "" >> $BASHRC
    echo "### Added by Down" >> $BASHRC
    echo "export WORKON_HOME=$HOME/.virtualenvs" >> $BASHRC
    echo "source /usr/local/bin/virtualenvwrapper.sh" >> $BASHRC
    source $BASHRC
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
