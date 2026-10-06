# M4 - API Joins 

## 1. Objective

In this new milestone, the previously created API was to be changed to allow joins in order to allow joins on SQL queries. 

## 2. Virtual Machine Configuration

Like M3, this application was deployed via an Azure virtual machine. The configuration of the virtual machine for this milestone is slightly different:

- Resource Group: `InternetScale-Lab3`
- VM Name: `django-web-server-2`
- Region: Central US (Zone 1)
- VM Size: `Standard_F1als_v7`
- vCPU: 2
- RAM: 1 GiB
- Operating System: Ubuntu Server 24.04 LTS
- Architecture: x64
- OS Disk: Premium SSD Default Size, 30 GiB
- Allowed inbound ports:
  - SSH 22
  - HTTP 80

The name of this service having a 2 denotes how the first deployment of the application was unsuccessful. After creating a new virtual machine, the application finally worked. 

The size of this virtual machine was chosen because the recommended sizes for this milestone were unavailable. The size "Standard_F1als_v7" was the only size available in the United States regions that had only 1 gigabyte of ram and 2 virtual CPUs. Despite this, the Standard_F1als_v7 size had 10 data disks and a maximum input/output operations per second (IOPS) of 4,000. Compare this to the size of the Standard_B2ats_v2 size, one recommended for this milestone, of 4 data discs and an IOPS of 3,750. While this is not that of a drastic change, it should be noted that this increase in performance will have effected how the load tests run. 

## 3. API and View Changes

The main changes to the API that were made in order to support joins when SQL queries are given. 

For queries such that 1 or more tables are needed to be joined, the Django Rest API quereies in api_views.py were changed such that they used the select_related() method. This method joins models that have foreign-key relationships inside of the original model. For instance, in the api view that returns all of the registrations for an event (api_event_registrations), the query in python looks like this, where the variable "event" is the event associated with the registration, which is a parameter of the view:

```python
registrations = Registration.objects.filter(
        EventID=event
    ).select_related(
        "EventID",
    ).order_by("RegistrationID")
```

This is for a list of registrations. In the api view that deletes a registration, which is more specific and also requires a specific user to be identified. That query is as such, where the variable of "user" is of the currently logged-in user and "events" is the one of the "event" is the event associated with the registration, which again is a parameter of the view:

```python
    user = request.user
    events = get_object_or_404(Event, EventID=event_id)
    registration = get_object_or_404(
        Registration.objects.select_related("UserID", "EventID"),
        EventID=events,
        UserID=user
    )
```

## Database Population

For this milestone, the database was populated with data in order to simulate how users would be using the site. This was done via the seed_events.py file provided with its default parameters:

- N_USERS = 20_000
- ORGANIZER_SHARE = 0.05       
- EVENTS_PER_ORGANIZER = 5     
- REGISTRATIONS_PER_USER = 8   
- FEEDBACK_SHARE = 0.3         
- ACTIVITY_SKEW = 0.8          
- POPULARITY_SKEW = 0.9

This created the following data distribution: 

