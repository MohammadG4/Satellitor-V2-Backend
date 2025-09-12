from rest_framework import serializers
from .models import AlertRule, Alert, NotificationLog
from farmapp.models import Land


class AlertRuleSerializer(serializers.ModelSerializer):
    land_name = serializers.CharField(source='land.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = AlertRule
        fields = [
            'id', 'name', 'description', 'land', 'land_name', 'user', 'user_email',
            'alert_type', 'severity', 'index_name', 'threshold_value', 'comparison_operator',
            'is_active', 'notification_methods', 'custom_script', 'cooldown_hours',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_notification_methods(self, value):
        """Validate notification methods"""
        valid_methods = ['email', 'sms', 'webhook', 'push']
        for method in value:
            if method not in valid_methods:
                raise serializers.ValidationError(f"Invalid notification method: {method}")
        return value
    
    def validate_threshold_value(self, value):
        """Validate threshold value"""
        if value is not None and (value < -1 or value > 1):
            raise serializers.ValidationError("Threshold value should be between -1 and 1")
        return value


class AlertSerializer(serializers.ModelSerializer):
    land_name = serializers.CharField(source='land.name', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    acquisition_date = serializers.DateField(source='vegetation_index_set.acquisition_date', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'rule', 'rule_name', 'land', 'land_name', 'user', 'user_email',
            'status', 'severity', 'index_name', 'index_value', 'threshold_value',
            'comparison_operator', 'vegetation_index_set', 'acquisition_date',
            'message', 'context_data', 'triggered_at', 'acknowledged_at', 'resolved_at'
        ]
        read_only_fields = [
            'id', 'triggered_at', 'acknowledged_at', 'resolved_at'
        ]


class AlertUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating alert status"""
    
    class Meta:
        model = Alert
        fields = ['status']
    
    def validate_status(self, value):
        """Validate status transition"""
        valid_transitions = {
            'triggered': ['acknowledged', 'dismissed'],
            'acknowledged': ['resolved', 'dismissed'],
            'resolved': [],  # Cannot change from resolved
            'dismissed': []  # Cannot change from dismissed
        }
        
        if self.instance:
            current_status = self.instance.status
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot change status from {current_status} to {value}"
                )
        
        return value


class NotificationLogSerializer(serializers.ModelSerializer):
    alert_message = serializers.CharField(source='alert.message', read_only=True)
    land_name = serializers.CharField(source='alert.land.name', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'alert', 'alert_message', 'land_name', 'notification_type',
            'recipient', 'status', 'sent_at', 'delivered_at', 'error_message',
            'response_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AlertStatsSerializer(serializers.Serializer):
    """Serializer for alert statistics"""
    total_alerts = serializers.IntegerField()
    triggered_alerts = serializers.IntegerField()
    acknowledged_alerts = serializers.IntegerField()
    resolved_alerts = serializers.IntegerField()
    dismissed_alerts = serializers.IntegerField()
    alerts_by_severity = serializers.DictField()
    alerts_by_land = serializers.DictField()
    recent_alerts = AlertSerializer(many=True)
