Lagniappe Sign-Up (best viewing experiene is on apps like Notepad++ or ones of a similar vein)

The app we have chosen for this project is an existing app called Lagniappe Sign-Up. It is a way for users in the Acadiana Area to create and register for events. Users can create events, which each have their own name, description, start time, and location. When a user other than the event's owner is on the page, they can register for the said event. Owners of events can edit, delete, and view registrations for them. 

This is a CSCE 553 baseline, not a production service. The data represented in this application does not reflect real life people or events and has no personal bearing. 

The product uses Django for the UI, HTTP for the API, and SQLite for the database.

Users:

Beth - username: "beth," password: "beth," owns event "beth's event"

Jacob - username: "jacob," password: "jacob," owns event "jacob's event"

Tom - username: "tom," password: "tom," owns event "tom's event"


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


Curls : 
Health check:
curl.exe -i https://csce-553-team.onrender.com/health/
<img width="766" height="431" alt="image" src="https://github.com/user-attachments/assets/a77c1392-1eae-404f-b901-efd3d574a4de" />

curl.exe -I https://csce-553-team.onrender.com/event/create            
HTTP/1.1 302 Found                   
Date: Tue, 01 Sep 2026 20:21:43 GMT   
Content-Type: text/html; charset=utf-8   
Connection: keep-alive   
cross-origin-opener-policy: same-origin                                  
location: /signin/?next=/event/create     
referrer-policy: same-origin             
rndr-id: 575d85a5-324c-4324    
Server: cloudflare            
vary: Cookie         
vary: Accept-Encoding   
x-content-type-options: nosniff   
x-frame-options: DENY   
x-render-origin-server: WSGIServer/0.2 CPython/3.14.3   
cf-cache-status: DYNAMIC   
CF-RAY: a346fba2cf80485e-DFW   
alt-svc: h3=":443"; ma=86400   

curl.exe -I https://csce-553-team.onrender.com/event/list
HTTP/1.1 500 Internal Server Error
Date: Tue, 01 Sep 2026 20:22:24 GMT
Content-Type: text/html; charset=utf-8
Connection: keep-alive
cross-origin-opener-policy: same-origin
referrer-policy: same-origin
rndr-id: 173211b7-95f1-4c11
Server: cloudflare
vary: Cookie
vary: Accept-Encoding
x-content-type-options: nosniff
x-frame-options: DENY
x-render-origin-server: WSGIServer/0.2 CPython/3.14.3
cf-cache-status: DYNAMIC
CF-RAY: a346fca0fe76f0a4-DFW
alt-svc: h3=":443"; ma=86400
