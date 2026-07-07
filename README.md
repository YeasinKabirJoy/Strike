# Strike
<div align="center">
  <img src="__screenshots/logo.png" alt="Logo" width="200">
</div>

# Introduction

Strike is Real Time Chat Application.

The back-end of this is built with Python, Django, and Django Channels. The front-end uses Bootstrap, CSS, HTMX, and Vanilla JS.

![Default Home View](__screenshots/home_page.png?raw=true "Title")

### Main Features

* Public, private, and group chat

* Real-time messaging with Django Channels and WebSockets

* Image sharing with multiple uploads, 5MB max size per image

* Message editing and deletion for sent text messages

* Typing indicators per chat room

* Search inside individual chats

* Lazy-loaded message pagination for chat history

* Online/offline presence tracking

* Multi-tab aware online status

* Last seen for private chats

* Private-chat read receipts

* Real-time sidebar updates for latest conversations and presence

* Group creation and group admin controls

* Group join requests

* User profiles with avatars and profile details

* User search and private chat creation

### Upcoming features
* 1:1 audio calling

* 1:1 video calling


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

### Environment Variables

Create a local `.env` file in the project root. Example:

    DJANGO_ENV=development
    DEBUG=True
    SECRET_KEY=your-local-secret-key
    ALLOWED_HOSTS=127.0.0.1,localhost
    CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
    CORS_ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000

For production, set these values in your hosting provider or deployment environment:

    DJANGO_ENV=production
    DEBUG=False
    SECRET_KEY=<generate-a-strong-secret>
    ALLOWED_HOSTS=your-domain.com,www.your-domain.com
    CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
    CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
    
### Running the Project

#### Apply database migrations
    $ python manage.py migrate
#### Run the development server
    $ python manage.py runserver
#### Open your browser and go to
   http://127.0.0.1:8000
    
    
