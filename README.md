# Strike
<div align="center">
  <img src="__screenshots/logo.png" alt="Logo" width="200">
</div>

# Introduction

Strike is Real Time Chat Application.

The back-end of this is made with Python and Django with the help of Django-Channels. In the front-end Bootstrap, CSS, HTMX and Vanila JS is used. Right now the front-end is not responsive(Only full screen mode).

![Default Home View](__screenshots/home.png?raw=true "Title")

### Main features

* Public,Private adn Group Chat.

* Sending Files(Multiple)

* Group Creation

* Group Admin ( Admin is the user that created the group)

* Group joining reqeust.

* Online Tracking

* Real Time sidebar update to show latest connection.

### Upcoming features
* Audio and Video Call


# Installation

Follow these steps to set up the project locally.

### Clone the Repository

If your project is already in an existing python3 virtualenv first install django by running

    $ git clone https://github.com/YeasinKabirJoy/Strike.git \
    cd Strike
    
      
### Create a Virtual Environment

    $ python -m virtualenv venv
    
### Activate the Virtual Environment
#### On Windows
    $ venv\Scripts\activate
#### on Mac/Linux
    $ source venv/bin/activate
    
### Install Dependencies
    $ pip install -r requirements.txt
    
### Running the Project

#### Apply database migrations
    $ python manage.py migrate
#### Run the development server
    $ python manage.py runserver
#### Open your browser and go to
   http://127.0.0.1:8000
    
    
