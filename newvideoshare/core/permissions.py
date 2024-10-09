from rest_framework.permissions import BasePermission
from django.utils import timezone

class HasActiveSubscription(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        subscription = user.subscription_set.filter(is_active=True).first()
        if subscription and subscription.subscription_end > timezone.now():
            return True
        return False