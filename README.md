# Item-Catalog

## Introduction

> This project is a part of the Udacity's Full Stack Web Developer Nanodegree.
It involved building an interactive catalogue web application with items in various categories as well as provide a user registration (via Google+ oAuth2) and authentication system. Registered users have the ability to post, edit and delete their own items.

This program uses third-party auth with Google or Facebook. Some of the technologies used to build this application include Flask, Bootsrap, Jinja2, and SQLite.
## Running

#### ***Project Setup:***
1.	Install Vagrant: https://www.vagrantup.com/downloads.html 
2.	Install Virtual Machine: https://www.virtualbox.org/wiki/Downloads
3.	Download a FSND virtual machine: https://github.com/udacity/fullstack-nanodegree-vm 

#### ***Starting the Virtual Machine:***
> Once you get the above software installed, follow the following instructions: 
```bash
cd vagrant
vagrant up
vagrant ssh
cd /vagrant
```

#### ***Setting up the database***:
> Run the following command to set up the database
```bash
python3 database_setup.py
```
> Once you have Initialize the database, Populate the database with some initial data
```bash
python3 item_catlog_init.py
```

#### ***Running the project:***
```bash
python3 project.py
```
> Open the browser and go to http://localhost:5000
