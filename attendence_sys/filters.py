import django_filters

from .models import Attendence

class AttendenceFilter(django_filters.FilterSet):

    class Meta:
        model = Attendence
        fields = ["Student_ID", "date", "year", "period"]
