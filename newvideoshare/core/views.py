from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User,Video
from rest_framework import viewsets
from .models import Video, Subscription, History, Like
from .serializers import VideoSerializer, SubscriptionSerializer, HistorySerializer
from .serializers import UserSerializer, RegisterSerializer, VideoSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .permissions import HasActiveSubscription
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone

class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticated, HasActiveSubscription]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1

        instance.save()

        History.objects.create(
            user=request.user,
            video=instance,
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save()

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_video(request, video_id):
    user = request.user
    video = Video.objects.get(id=video_id)
    if not Like.objects.filter(user=user, video=video).exists():
        Like.objects.create(user=user, video=video)
        video.likes += 1
        video.save()
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'video_{video_id}',
            {
                'type': 'video_like_update',
                'likes': video.likes,
            }
        )
    serializer = VideoSerializer(video)
    return Response(serializer.data)
    
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

class UserView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

class HistoryViewSet(viewsets.ModelViewSet):
    queryset = History.objects.all()
    serializer_class = HistorySerializer
    permission_classes = [IsAuthenticated]
    
class SubscriptionCreateView(generics.CreateAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_subscription(request):
    user = request.user
    subscription_start = timezone.now()
    subscription_end = subscription_start + timezone.timedelta(days=30)  
    subscription = Subscription.objects.create(
        user=user,
        subscription_start=subscription_start,
        subscription_end=subscription_end,
        is_active=True
    )
    serializer = SubscriptionSerializer(subscription)
    return Response(serializer.data)