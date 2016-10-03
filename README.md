# CittaAppDemo  
Complete Django Project for Citta Website Demo

## About the Code
The code for this project is contained the main `citta` folder, and dvided in two parts: the sub `citta` folder, and the `scheduler` folder.

### Citta
The sub `citta` folder contains code pertaining to the entire site. `settings.py` contains the settings for the site.

The settings to take special note of are `DATABASES`, which describes the backed for the project, and `SITE_ID`, which needs to be changed whether running locally or on google.

Simlarly, `GOOGLE_OAUTH2_CLIENT_ID` and `GOOGLE_OAUTH2_CLIENT_SECRET` need to be changed. Both the local an production options are present, which one version commented out.

`urls.py` describes the url patterns that are valid for this site. The first url is for the scheduler app, the second is for the admin page, and the third is for login scripts.

## Scheduler

The `scheduler` folder is for the scheduling app specfically, and contains the bulk of the relevant code.

`admin.py` contains code to change what is available on the admin page.

`models.py` has classes which describe the tables in the database. The classes describe the columns and relationships between the tables.

`forms.py` has classes which describe user input forms that appear on the site.They contain information about what model they affect, what fields they use, and any custom validation necessary.

`urls.py` describes the urls that refer to various pages in this app. Because this app has the url `scheduler\`, all of there patterns come after `scheduler`. They are all tied to a function in `views.py`, and have names so they can be easily referred to in other files.

`views.py` is the most important file in the project. It contains the code that runs when any of the urls are accessed. The methods at the bottom of the file, beginning with `progress` on line 209, are methods which return either rendered html, or redirects to other urls.

`progress`, `edittask`, `newtask`, and `setuser` are all form validation views. When accesed using `GET`, they render a form, and when accesed using `POST`, they validate and save the form, then redirect the user.

`deletetask', `logout`, and `reschedule` do not have any associated html, they are purely function and will always redirect after running their associated code.

All of the non-view methods are for the scheduling algorithm, and have been commented and documted within the code.

## Templates
All of the html for this site is located in `scheduler/templates/scheduler`.

Other files, such as javascript and css files, are in `scheduler/static`

## Setup
NOTE: To run django python commands, make sure the python virtualenv has been activated, by running `source env/bin/activate` in the main `citta` directory.

In order to run site, make sure the following are true:
* DEBUG is set to TRUE (for debugging) or FALSE (for deployment) in `scheduler/settings.py`
* In the same file, SITE\_ID  is set to the appropriate value (see file)
* Again in `settings.py`, change the two Google OAuth2 Key Values to their appropriate values.

Then, to run locally, go to the main `citta` directory and run the command `python manage.py runserver`.
