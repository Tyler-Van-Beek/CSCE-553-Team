from rest_framework import serializers
from events.models import Users, Event, Category, Feedback, Registration

class EventSerializer(serializers.Serializer):
    EventID = serializers.IntegerField(read_only="True")
    OrganizerID = serializers.PrimaryKeyRelatedField(queryset=Users.objects.all())
    CategoryID = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    Title = serializers.CharField(("title"), max_length=100)
    Description = serializers.CharField(("description"), max_length=500)
    Location = serializers.CharField(("location"), max_length=100)
    DateTime = serializers.DateTimeField(("datetime"), null=True)
    EventStatus = serializers.BooleanField(("eventstatus"), default=True)