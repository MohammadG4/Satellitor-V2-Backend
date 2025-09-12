from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import AlertRule, Alert, NotificationLog
from .serializers import (
    AlertRuleSerializer, AlertSerializer, AlertUpdateSerializer,
    NotificationLogSerializer, AlertStatsSerializer
)
from .services import AlertManager
from farmapp.models import Land


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit their own objects"""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the owner
        return obj.user == request.user


class AlertRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing alert rules"""
    
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['land', 'alert_type', 'severity', 'is_active', 'index_name']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return alert rules for the authenticated user"""
        return AlertRule.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user to the current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test_rule(self, request, pk=None):
        """Test an alert rule against recent data"""
        rule = self.get_object()
        
        # Get the most recent vegetation index set for this land
        try:
            recent_data = VegetationIndexSet.objects.filter(
                land=rule.land
            ).order_by('-acquisition_date').first()
            
            if not recent_data:
                return Response(
                    {'error': 'No vegetation index data found for this land'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Test the rule
            alert_manager = AlertManager()
            index_value = alert_manager.processor.get_index_value(recent_data, rule.index_name)
            
            if index_value is None:
                return Response(
                    {'error': f'No {rule.index_name} data found in recent vegetation index set'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            should_trigger = alert_manager.processor.should_trigger_alert(rule, index_value)
            
            return Response({
                'rule_name': rule.name,
                'index_name': rule.index_name,
                'index_value': index_value,
                'threshold_value': rule.threshold_value,
                'comparison_operator': rule.comparison_operator,
                'should_trigger': should_trigger,
                'test_data_date': recent_data.acquisition_date.isoformat()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error testing rule: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet for managing alerts"""
    
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['land', 'status', 'severity', 'index_name', 'rule']
    search_fields = ['message', 'land__name', 'rule__name']
    ordering_fields = ['triggered_at', 'severity', 'index_value']
    ordering = ['-triggered_at']
    
    def get_queryset(self):
        """Return alerts for the authenticated user"""
        return Alert.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Use different serializer for updates"""
        if self.action in ['update', 'partial_update']:
            return AlertUpdateSerializer
        return AlertSerializer
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert"""
        alert = self.get_object()
        alert_manager = AlertManager()
        
        if alert_manager.acknowledge_alert(alert.id, request.user):
            return Response({'status': 'acknowledged'})
        return Response(
            {'error': 'Failed to acknowledge alert'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert"""
        alert = self.get_object()
        alert_manager = AlertManager()
        
        if alert_manager.resolve_alert(alert.id, request.user):
            return Response({'status': 'resolved'})
        return Response(
            {'error': 'Failed to resolve alert'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss an alert"""
        alert = self.get_object()
        alert_manager = AlertManager()
        
        if alert_manager.dismiss_alert(alert.id, request.user):
            return Response({'status': 'dismissed'})
        return Response(
            {'error': 'Failed to dismiss alert'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get alert statistics for the user"""
        user_alerts = Alert.objects.filter(user=request.user)
        
        # Basic counts
        total_alerts = user_alerts.count()
        triggered_alerts = user_alerts.filter(status='triggered').count()
        acknowledged_alerts = user_alerts.filter(status='acknowledged').count()
        resolved_alerts = user_alerts.filter(status='resolved').count()
        dismissed_alerts = user_alerts.filter(status='dismissed').count()
        
        # Alerts by severity
        alerts_by_severity = user_alerts.values('severity').annotate(
            count=Count('id')
        ).order_by('severity')
        severity_dict = {item['severity']: item['count'] for item in alerts_by_severity}
        
        # Alerts by land
        alerts_by_land = user_alerts.values('land__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        land_dict = {item['land__name']: item['count'] for item in alerts_by_land}
        
        # Recent alerts (last 10)
        recent_alerts = user_alerts.order_by('-triggered_at')[:10]
        recent_serializer = AlertSerializer(recent_alerts, many=True)
        
        stats_data = {
            'total_alerts': total_alerts,
            'triggered_alerts': triggered_alerts,
            'acknowledged_alerts': acknowledged_alerts,
            'resolved_alerts': resolved_alerts,
            'dismissed_alerts': dismissed_alerts,
            'alerts_by_severity': severity_dict,
            'alerts_by_land': land_dict,
            'recent_alerts': recent_serializer.data
        }
        
        serializer = AlertStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard data for alerts"""
        user_alerts = Alert.objects.filter(user=request.user)
        
        # Last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_alerts = user_alerts.filter(triggered_at__gte=thirty_days_ago)
        
        # Critical alerts (unresolved)
        critical_alerts = user_alerts.filter(
            severity='critical',
            status__in=['triggered', 'acknowledged']
        ).order_by('-triggered_at')[:5]
        
        # Alerts by day (last 30 days)
        daily_counts = recent_alerts.extra(
            select={'day': 'date(triggered_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        return Response({
            'critical_alerts': AlertSerializer(critical_alerts, many=True).data,
            'daily_counts': list(daily_counts),
            'total_recent': recent_alerts.count(),
            'unresolved': user_alerts.filter(
                status__in=['triggered', 'acknowledged']
            ).count()
        })


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing notification logs"""
    
    queryset = NotificationLog.objects.all()
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['alert', 'notification_type', 'status']
    search_fields = ['alert__message', 'alert__land__name']
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return notification logs for the authenticated user's alerts"""
        return NotificationLog.objects.filter(alert__user=self.request.user)
