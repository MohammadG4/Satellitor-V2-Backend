from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models as gis_models
from farmapp.models import Land, VegetationIndexSet
import json

User = get_user_model()


class AlertRule(models.Model):
    """Alert rules for vegetation indices"""
    
    ALERT_TYPES = [
        ('threshold', 'Threshold Alert'),
        ('anomaly', 'Anomaly Detection'),
        ('trend', 'Trend Analysis'),
        ('custom', 'Custom Script'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Rule Name")
    description = models.TextField(blank=True, verbose_name="Description")
    land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name="alert_rules", verbose_name="Land")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alert_rules", verbose_name="User")
    
    # Alert configuration
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, verbose_name="Alert Type")
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium', verbose_name="Severity")
    
    # Vegetation index configuration
    index_name = models.CharField(max_length=20, verbose_name="Index Name")  # NDVI, NDRE, etc.
    threshold_value = models.FloatField(null=True, blank=True, verbose_name="Threshold Value")
    comparison_operator = models.CharField(
        max_length=10,
        choices=[
            ('gt', 'Greater Than'),
            ('lt', 'Less Than'),
            ('gte', 'Greater Than or Equal'),
            ('lte', 'Less Than or Equal'),
            ('eq', 'Equal'),
            ('ne', 'Not Equal'),
        ],
        default='lt',
        verbose_name="Comparison Operator"
    )
    
    # Notification settings
    is_active = models.BooleanField(default=True, verbose_name="Active")
    notification_methods = models.JSONField(
        default=list,
        verbose_name="Notification Methods",
        help_text="List of notification methods: ['email', 'sms', 'webhook']"
    )
    
    # Advanced settings
    custom_script = models.TextField(blank=True, verbose_name="Custom Script")
    cooldown_hours = models.IntegerField(default=24, verbose_name="Cooldown Hours")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Alert Rule"
        verbose_name_plural = "Alert Rules"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['land', 'name'],
                name='uniq_land_alert_rule_name'
            )
        ]
    
    def __str__(self):
        return f"{self.land.name} - {self.name}"


class Alert(models.Model):
    """Individual alert instances"""
    
    STATUS_CHOICES = [
        ('triggered', 'Triggered'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name="alerts", verbose_name="Alert Rule")
    land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name="alerts", verbose_name="Land")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alerts", verbose_name="User")
    
    # Alert data
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='triggered', verbose_name="Status")
    severity = models.CharField(max_length=20, verbose_name="Severity")
    
    # Vegetation index data that triggered the alert
    index_name = models.CharField(max_length=20, verbose_name="Index Name")
    index_value = models.FloatField(verbose_name="Index Value")
    threshold_value = models.FloatField(verbose_name="Threshold Value")
    comparison_operator = models.CharField(max_length=10, verbose_name="Comparison Operator")
    
    # Additional context
    vegetation_index_set = models.ForeignKey(
        VegetationIndexSet,
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name="Vegetation Index Set"
    )
    message = models.TextField(verbose_name="Alert Message")
    context_data = models.JSONField(default=dict, verbose_name="Context Data")
    
    # Timestamps
    triggered_at = models.DateTimeField(auto_now_add=True, verbose_name="Triggered At")
    acknowledged_at = models.DateTimeField(null=True, blank=True, verbose_name="Acknowledged At")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Resolved At")
    
    class Meta:
        verbose_name = "Alert"
        verbose_name_plural = "Alerts"
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"{self.land.name} - {self.index_name} Alert ({self.severity})"


class NotificationLog(models.Model):
    """Log of notification attempts"""
    
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('webhook', 'Webhook'),
        ('push', 'Push Notification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    ]
    
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="notifications", verbose_name="Alert")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name="Type")
    recipient = models.CharField(max_length=200, verbose_name="Recipient")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    
    # Delivery details
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Sent At")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Delivered At")
    error_message = models.TextField(blank=True, verbose_name="Error Message")
    response_data = models.JSONField(default=dict, verbose_name="Response Data")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    class Meta:
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert} - {self.notification_type} ({self.status})"


class AlertScenario(models.Model):
    """Advanced alert scenarios for agricultural monitoring"""
    
    SCENARIO_TYPES = [
        ('rapid_ndvi_drop', 'Rapid NDVI Drop (Acute Stress)'),
        ('spatial_anomaly', 'Spatial/Patchy Anomaly (Localized Problem)'),
        ('growth_stagnation', 'Stagnation During Growth (Expected Rise Not Happening)'),
        ('below_historical', 'Below Historical Percentile (Seasonal Anomaly/Drought)'),
        ('phenology_delay', 'Delay in Phenology (SOS/EOS Deviation)'),
        ('poor_emergence', 'Persistent Low NDVI After Sowing (Poor Emergence)'),
        ('trend_decline', 'Long-term Trend Decline (Chronic Degradation)'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Scenario Name")
    description = models.TextField(verbose_name="Description")
    scenario_type = models.CharField(max_length=50, choices=SCENARIO_TYPES, verbose_name="Scenario Type")
    land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name="alert_scenarios", verbose_name="Land")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alert_scenarios", verbose_name="User")
    
    # Scenario-specific parameters
    parameters = models.JSONField(default=dict, verbose_name="Scenario Parameters")
    
    # Alert configuration
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium',
        verbose_name="Severity"
    )
    
    # Status and timing
    is_active = models.BooleanField(default=True, verbose_name="Active")
    cooldown_hours = models.IntegerField(default=24, verbose_name="Cooldown Hours")
    notification_methods = models.JSONField(default=list, verbose_name="Notification Methods")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Alert Scenario"
        verbose_name_plural = "Alert Scenarios"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['land', 'name'],
                name='uniq_land_scenario_name'
            )
        ]
    
    def __str__(self):
        return f"{self.land.name} - {self.name}"


class ScenarioExecution(models.Model):
    """Track execution of alert scenarios"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    scenario = models.ForeignKey(AlertScenario, on_delete=models.CASCADE, related_name="executions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result_data = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.scenario.name} - {self.status}"
