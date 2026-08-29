Lagniappe Sign-Up (best viewing experiene is on apps like Notepad++ or ones of a similar vein)

The app we have chosen for this project is an existing app called Lagniappe Sign-Up. It is a way for users in the Acadiana Area to create and register for events. Users can create events, which each have their own name, description, start time, and location. When a user other than the event's owner is on the page, they can register for the said event. Owners of events can edit, delete, and view registrations for them. 

The product uses Django for the UI, HTTP for the actions for the database.

Paths:

Path                           Method    Purpose

Common -

/about                         GET       About the app
/map                           GET       Map of event locations (not functional)
/signin                        POST      Signs in
/signup                        POST      Create User
/signout                       POST      Signs out
/healthcheck                   GET       Health of app
/faq                           GET       Questions about app

Event -

/event/list                    GET       List of events
/event/create                  POST      Event creation
/event/<int:pk>                GET       Detail view of event
/event/update/<int:pk>         POST      Update view of event
/event/registration/<int:pk>   GET       List of registrations for event
/event/<int:pk>/delete         POST      Delete view of event

Registration -

/registration/create/<int:pk>  POST      Creation of registration for event
/registration/delete/<int:pk>  POST      Deletion of registration

Feedback -
/feedback/create/<int:pk>      POST      Creation of feedback
/feedback/list                 GET       List of feedback

