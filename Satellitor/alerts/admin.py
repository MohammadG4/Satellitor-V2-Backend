from django.contrib import admin
from django.utils import timezone
from .models import AlertRule, Alert, NotificationLog, AlertScenario, ScenarioExecution


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'land', 'user', 'alert_type', 'severity', 'index_name',
        'threshold_value', 'comparison_operator', 'is_active', 'created_at'
    ]
    list_filter = [
        'alert_type', 'severity', 'is_active', 'index_name', 'created_at'
    ]
    search_fields = ['name', 'description', 'land__name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'land', 'user')
        }),
        ('Alert Configuration', {
            'fields': ('alert_type', 'severity', 'index_name', 'threshold_value', 'comparison_operator')
        }),
        ('Notification Settings', {
            'fields': ('is_active', 'notification_methods', 'cooldown_hours')
        }),
        ('Advanced', {
            'fields': ('custom_script',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'land', 'rule', 'severity', 'index_name', 'index_value',
        'threshold_value', 'status', 'triggered_at'
    ]
    list_filter = [
        'status', 'severity', 'index_name', 'triggered_at', 'acknowledged_at', 'resolved_at'
    ]
    search_fields = ['message', 'land__name', 'rule__name', 'user__email']
    readonly_fields = [
        'triggered_at', 'acknowledged_at', 'resolved_at', 'context_data'
    ]
    ordering = ['-triggered_at']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('rule', 'land', 'user', 'status', 'severity')
        }),
        ('Index Data', {
            'fields': ('index_name', 'index_value', 'threshold_value', 'comparison_operator')
        }),
        ('Context', {
            'fields': ('vegetation_index_set', 'message', 'context_data')
        }),
        ('Timestamps', {
            'fields': ('triggered_at', 'acknowledged_at', 'resolved_at')
        })
    )
    
    actions = ['acknowledge_alerts', 'resolve_alerts', 'dismiss_alerts']
    
    def acknowledge_alerts(self, request, queryset):
        """Acknowledge selected alerts"""
        updated = queryset.filter(status='triggered').update(
            status='acknowledged',
            acknowledged_at=timezone.now()
        )
        self.message_user(request, f'{updated} alerts acknowledged.')
    acknowledge_alerts.short_description = "Acknowledge selected alerts"
    
    def resolve_alerts(self, request, queryset):
        """Resolve selected alerts"""
        updated = queryset.filter(status__in=['triggered', 'acknowledged']).update(
            status='resolved',
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{updated} alerts resolved.')
    resolve_alerts.short_description = "Resolve selected alerts"
    
    def dismiss_alerts(self, request, queryset):
        """Dismiss selected alerts"""
        updated = queryset.filter(status__in=['triggered', 'acknowledged']).update(
            status='dismissed'
        )
        self.message_user(request, f'{updated} alerts dismissed.')
    dismiss_alerts.short_description = "Dismiss selected alerts"


@admin.register(AlertScenario)
class AlertScenarioAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'land', 'user', 'scenario_type', 'severity', 'is_active', 'created_at'
    ]
    list_filter = [
        'scenario_type', 'severity', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description', 'land__name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'land', 'user')
        }),
        ('Scenario Configuration', {
            'fields': ('scenario_type', 'parameters', 'severity')
        }),
        ('Alert Settings', {
            'fields': ('is_active', 'cooldown_hours', 'notification_methods')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ScenarioExecution)
class ScenarioExecutionAdmin(admin.ModelAdmin):
    list_display = [
        'scenario', 'status', 'started_at', 'completed_at'
    ]
    list_filter = [
        'status', 'started_at', 'completed_at'
    ]
    search_fields = ['scenario__name', 'scenario__land__name']
    readonly_fields = ['started_at', 'completed_at']
    ordering = ['-started_at']
    
    fieldsets = (
        ('Execution Information', {
            'fields': ('scenario', 'status', 'started_at', 'completed_at')
        }),
        ('Results', {
            'fields': ('result_data', 'error_message')
        })
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'alert', 'notification_type', 'recipient', 'status',
        'sent_at', 'created_at'
    ]
    list_filter = [
        'notification_type', 'status', 'sent_at', 'created_at'
    ]
    search_fields = [
        'alert__message', 'alert__land__name', 'recipient', 'error_message'
    ]
    readonly_fields = ['created_at', 'sent_at', 'delivered_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('alert', 'notification_type', 'recipient', 'status')
        }),
        ('Delivery Details', {
            'fields': ('sent_at', 'delivered_at', 'error_message', 'response_data')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
