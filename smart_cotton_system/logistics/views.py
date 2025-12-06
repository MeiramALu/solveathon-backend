from rest_framework import viewsets
from .models import Vehicle, GPSLog, Route
from .serializers import VehicleSerializer, GPSLogSerializer, RouteSerializer

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

class GPSLogViewSet(viewsets.ModelViewSet):
    queryset = GPSLog.objects.all().order_by('-timestamp')
    serializer_class = GPSLogSerializer

class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all().order_by('-created_at')
    serializer_class = RouteSerializer