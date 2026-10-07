# M4 - API Joins 

## 1. Objective

In this new milestone, the previously created API was to be changed to allow joins in order to allow joins on SQL queries. Joins help with performance. On top of this, the database is increased to help better reflect what real world data distributions would look like. The increased weight of a large database is to see how the performance of our load tests differs with our previous tests. The performance is sure to worsen with an increase of size in the database. This will stem from more columns being searched through and having more objects to be sent to the user. 

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

The size of this virtual machine was chosen because the recommended sizes for this milestone were unavailable. The size "Standard_F1als_v7" was the only size available in the United States regions that had only 1 gigabyte of ram and 2 virtual CPUs. Despite this, the Standard_F1als_v7 size had 10 data disks and a maximum input/output operations per second (IOPS) of 4,000. Compare this to the size of the Standard_B2ats_v2 size, one recommended for this milestone, of 4 data discs and an IOPS of 3,750. While this is not that of a drastic change, it should be noted that this increase in performance may have effected the performance of the load runs below. 

## 3. API View Changes

The main changes to the API that were made in order to support joins when SQL queries are given. 

For queries such that 1 or more tables are needed to be joined, the Django Rest API quereies in api_views.py were changed such that they used the select_related() method. This method joins models that have foreign-key relationships inside of the original model. For instance, in the api view that returns a list of all of the registrations for an event (api_event_registrations), the query in python looks like this, where the variable "event" is the event associated with the registration, which is a parameter of the view:

```python
registrations = Registration.objects.filter(
        EventID=event
    ).select_related(
        "EventID",
    ).order_by("RegistrationID")
```

In the api view that deletes a registration, which is more specific and also requires a specific user to be identified. That query is as such, where the variable of "user" is of the currently logged-in user and "events" is the one of the "event" is the event associated with the registration, which again is a parameter of the view:

```python
    registration = get_object_or_404(
        Registration.objects.select_related("UserID", "EventID"),
        RegistrationID=registration_id,
        EventID_id=event_id,
        UserID=request.user,
    )
```

Technically, the registration_id is not required for this query, as there is a 

## 4. Database Population and Changes

In the database, Feedback and Registration objects have foreign keys EventID and UserID. Technically, these could act as a many-to-many relationship, but not officially. This required a many-to-many relationship be explicitly applied.

There are checks in the application that check whether or not someone has already registered for an event, but that check does not happen as an object is being created. This required that constraints on the Feedback and Registrations models that made each UserID and EventID combination in the database be unique. The FeedbackID and RegistrationID fields were kept in order to better keep track of these objects. 

For this milestone, the database was populated with data in order to simulate how users would be using the site. This was done via the seed_events.py file provided with its default parameters:

- N_USERS = 20_000
- ORGANIZER_SHARE = 0.05       
- EVENTS_PER_ORGANIZER = 5     
- REGISTRATIONS_PER_USER = 8   
- FEEDBACK_SHARE = 0.3         
- ACTIVITY_SKEW = 0.8          
- POPULARITY_SKEW = 0.9

This created the following data distribution: 

- 20,000 users
- 3,850 events
- 160,000 registrations
- 26,522 feedbacks

A small amount of users, events, and registrations (less than 5 each) were created in order to test the website's functionality in a browser after the database was populated. There is noticeably more wait time now that the database is populated, but it is still manageable. 

## 5. Load Testing

Every load test done in this section has a warmup time of 10 seconds, a duration of 60 seconds, and is of the "GET" method. Both of the APIs were checked with concurrencies of 1, 2, 4, 8, 16, and 32. 

First, the endpoint of 

```text
GET /api/events/3840/registrations
```

was tested via authentication. This is the list of the for a given event. The event identification variable was chosen at random. 

| Metric | C=1 | C=2 | C=4 | C=8 | C=16 | C=32 |
|---|---:|---:|---:|---:|---:|---:|
| Successful RPS | 3.565 | 7.449 | 11.237 | 17.008 | 21.459 | 25.184 |
| p50 Latency | 272.13 | 261.34 | 296.44 | 317.64 | 455.67 | 857.49 |
| p99 Latency | 481.44 | 449.3 | 658.43 | 625.64 | 2306.07 | 2390.03 | 
| Error Rate | 0 | 0 | 0.0015 | 0.0022 | 0.0031 | 0.005 |
| Max Ram | ~900MiB | ~900MiB | ~900MiB | ~900MiB | ~900MiB | ~900MiB |

The next endpoint was 

```text
GET /api/events
```

While there are no joins on this query, it is important to test this endpoint as this was one of the endpoints that was previously tested in M3, when the database was nowhere near as populated.

| Metric | C=1 | C=2 | C=4 | C=8 | C=16 | C=32 |
|---|---:|---:|---:|---:|---:|---:|
| Successful RPS | 0.906 | 1.852 | 2.473 | 3.839 | 5.617 | 4.971 |
| p50 Latency | 1057.5 | 1038.82 | 1345.89 | 1444.57 | 2087.32 | 4458.58 | 
| p99 Latency | 2881.99 | 1885.61 | 5396.7 | 21056.21 | 15029.07 | 27628.31 | 
| Error Rate | 0 | 0 | 0 | 0.0033 | 0 | 0.003 |
| Max CPU | 8.51% | 8.36% | 16.97%  | 26.88% | 46.80% | 51.39% |
| Max Ram | ~900MiB | ~900MiB | ~900MiB | ~900MiB | ~900MiB | ~900MiB |


## 6. Registration-List Interpretations

The end point "GET /api/events/3840/registrations" remained mostly stable even at high concurrent users. The successful RPS went up exponentially with the amount of concurrent users. The error rate remained 0 or around 0 for every test with a concurrent amount of users greater than 1. Speaking of, a success rate of 0.005 at its highest, half of a percent, is a good metric, it still means that there were some errors on these tests. Compare this to M2 where the error rate was measured at 0.0. 

There were four spikes of the max CPU usage while the load tests were being done. Near the start, there were two spikes. The average CPU usage went from idling between 1-2% before suddenly spiking up to 13,67% as the load tests began. It the fell to 5.22% before spiking up again at 8.395%. There was a brief period where no tests happened, and then a slight bump up that peaked at 7.85% before heading back down to idle. Finally, there was a large spike in CPU usage whenever the final load test, which had the most concurrent users, of 14.61%. After the load tests, the percentage leveled back to the idling range of 1-2%. 

Comparing this with the results from M3 shows that the CPU usage was higher overall. Even at 250 concurrent users, the max CPU during M3 only reached 2.55%. While 14.61% is closer to 2.55% than the 100% that would overwhelm the CPU, it still shows that the CPU was being more heavily used. This may have been caused by the increase in the size of the database.The increase of size of the database would cause outputs of queries to be longer. 

Before, during, and after the load tests, max remaining memory stayed constant at about 900 MiB. This indicates that even with a high fluctuation of the CPU, the memory will still hold out. 

## 7. Event-List Interpretations

Throughput decreased drastically compared to M3. The throughput never went above 5 RPS, which is what it was for the M3 testing on the limited database. In the current version of the app, every single event is listed on this page. An increase in latency is expected for this test, as the database now consists of exponentially more objects in this milestone than it did in the previous milestone. Since there are more objects that need to be returned per-query, that means that there will be more time waiting for the full request to be fulfilled. 

This is explained by the drastic increase in both the average and 99th percentile latency. They are all over a second. As there are more and more concurrent users, there is correlated with the increase in time for requests to be fulfilled. 

Unlike the other API load test during this milestone, there actually was significant increase on the CPU allocation for these tasks. At a low number of concurrent users, the CPU utilization was just above 8%. As it reached 32 concurrent users, over half of the CPU was utilized at one time. According to the trend of these tests, if the number of concurrent users gets to around 60, then the CPU of our virtual machine could be fully utilized. 

Like the registrations list call, the max remaining memory was almost constant. It stayed around 870 MiB near the start and ended at around 835 MiB when the load tests were over. This shows that there was *some* increase in memory consumed for these load tests, but the amount used up was fairly minimal compared to the overall available while idling.

Despite the long wait times, the error rate remains surprisingly low. Four of the six load tests returned no errors. Despite the increase in query size compared to the registrations-list query, the overall error rate was lower. That shows how reliable this service is. 

Of course, this is an issue. We could solve this issue by paginating this page. This will set a maximum number of event objects that will be sent per query, reducing RPS, latency, and hopefully the max CPU.

## 8. Conclusions

These tests have shown the limitations of our application. 

The load tests on the event list API do show a degradation of performance when compared to previous test. Despite the slight increase in performance that the virtual machine size should be offering, the RPS is lower, the latency is higher, and the virtual machine's CPU is increasingly more utilized on this view. This shows that changes need to be made on this view, and other ones that return lists of objects, in order to get better performance.

Pagination seems like the best way in order to solve this issue, as it only sends a limited number of objects at a time per request. This would fix the problems with RPS, latency, and CPU utilization. 

It appears that the current bottleneck is the CPU. Our previous tests showed that it the CPU was not an issue. However, the changes done to the database and API (mostly the database) are causing issues on the CPU end. With the increase of data in the database, it appears that the CPU is being used to process more and more. 

However, for the load tests on the registration list API, there were not a lot of issues. The RPS had steady growth with the addition of current users, the average latency was less than a second, the error rate was equal to or less than half of a percent, and the maximum CPU utilization was always under 15%. 

The max remaining memory metric and error rate were low and steady were low for both of the load tests. This shows that these aspects of the application do not need that much attention right now. They are serviceable for what we need. 

This shows that some pages in the application have differing issues. One page runs fine, while the other page has significant issues. It shows that some parts of the website may take more to work on compared to others. For instance, more time should be dedicated to the events-list view than the registration-list view, as the former is having more issues than the latter. 
