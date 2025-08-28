from rest_framework.throttling import AnonRateThrottle


class PasswordResetThrottle(AnonRateThrottle):
    rate = '5/hour'  # 5 attempts per hour
