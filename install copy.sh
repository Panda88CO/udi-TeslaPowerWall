#!/usr/bin/env bash


mkdir -p profile 
mkdir -p profile/nodedef
mkdir -p profile/nls
mkdir -p profile/editor



pip install --upgrade pip
pip install git+https://github.com/jrester/tesla_powerwall#egg=tesla_powerwall
pip install -r requirements.txt --user