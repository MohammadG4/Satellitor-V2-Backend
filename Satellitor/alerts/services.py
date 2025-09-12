import logging
from datetime import datetime, timedelta
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from farmapp.models import VegetationIndexSet
from .models import AlertRule, Alert, NotificationLog
import json

logger = logging.getLogger(__name__)


class AlertProcessor:
    """Service class for processing alerts"""
    
    def __init__(self):
        self.logger = logger
    
    def process_land_alerts(self, land, vegetation_index_set):
        """Process all alert rules for a specific land and vegetation index set"""
        try:
            # Get active alert rules for this land
            alert_rules = AlertRule.objects.filter(
                land=land,
                is_active=True
            )
            
            self.logger.info(f"Processing {alert_rules.count()} alert rules for land {land.name}")
            
            for rule in alert_rules:
                self.process_alert_rule(rule, vegetation_index_set)
                
        except Exception as e:
            self.logger.error(f"Error processing alerts for land {land.name}: {str(e)}")
    
    def process_alert_rule(self, rule, vegetation_index_set):
        """Process a single alert rule"""
        try:
            # Check if alert was triggered recently (cooldown)
            if self.is_in_cooldown(rule):
                self.logger.debug(f"Rule {rule.name} is in cooldown, skipping")
                return
            
            # Get the index value from the vegetation index set
            index_value = self.get_index_value(vegetation_index_set, rule.index_name)
            if index_value is None:
                self.logger.warning(f"No {rule.index_name} data found for land {rule.land.name}")
                return
            
            # Check if alert condition is met
            if self.should_trigger_alert(rule, index_value):
                self.create_alert(rule, vegetation_index_set, index_value)
            else:
                self.logger.debug(f"Rule {rule.name} condition not met for value {index_value}")
                
        except Exception as e:
            self.logger.error(f"Error processing rule {rule.name}: {str(e)}")
    
    def is_in_cooldown(self, rule):
        """Check if rule is in cooldown period"""
        if rule.cooldown_hours <= 0:
            return False
        
        last_alert = Alert.objects.filter(
            rule=rule,
            triggered_at__gte=timezone.now() - timedelta(hours=rule.cooldown_hours)
        ).first()
        
        return last_alert is not None
    
    def get_index_value(self, vegetation_index_set, index_name):
        """Get the mean value of a specific vegetation index"""
        try:
            stats = vegetation_index_set.stats
            if index_name in stats and 'mean' in stats[index_name]:
                return stats[index_name]['mean']
            return None
        except Exception as e:
            self.logger.error(f"Error getting index value for {index_name}: {str(e)}")
            return None
    
    def should_trigger_alert(self, rule, index_value):
        """Check if alert condition is met"""
        if rule.threshold_value is None:
            return False
        
        operator = rule.comparison_operator
        
        if operator == 'gt':
            return index_value > rule.threshold_value
        elif operator == 'lt':
            return index_value < rule.threshold_value
        elif operator == 'gte':
            return index_value >= rule.threshold_value
        elif operator == 'lte':
            return index_value <= rule.threshold_value
        elif operator == 'eq':
            return abs(index_value - rule.threshold_value) < 0.001  # Float comparison
        elif operator == 'ne':
            return abs(index_value - rule.threshold_value) >= 0.001
        
        return False
    
    def create_alert(self, rule, vegetation_index_set, index_value):
        """Create a new alert"""
        try:
            with transaction.atomic():
                alert = Alert.objects.create(
                    rule=rule,
                    land=rule.land,
                    user=rule.user,
                    severity=rule.severity,
                    index_name=rule.index_name,
                    index_value=index_value,
                    threshold_value=rule.threshold_value,
                    comparison_operator=rule.comparison_operator,
                    vegetation_index_set=vegetation_index_set,
                    message=self.generate_alert_message(rule, index_value),
                    context_data=self.generate_context_data(vegetation_index_set, rule.index_name)
                )
                
                # Send notifications
                self.send_notifications(alert)
                
                self.logger.info(f"Created alert {alert.id} for rule {rule.name}")
                
        except Exception as e:
            self.logger.error(f"Error creating alert for rule {rule.name}: {str(e)}")
    
    def generate_alert_message(self, rule, index_value):
        """Generate human-readable alert message"""
        operator_text = {
            'gt': 'greater than',
            'lt': 'less than',
            'gte': 'greater than or equal to',
            'lte': 'less than or equal to',
            'eq': 'equal to',
            'ne': 'not equal to',
        }.get(rule.comparison_operator, rule.comparison_operator)
        
        return (
            f"Alert: {rule.index_name} value ({index_value:.3f}) is "
            f"{operator_text} threshold ({rule.threshold_value:.3f}) "
            f"for land {rule.land.name}"
        )
    
    def generate_context_data(self, vegetation_index_set, index_name):
        """Generate additional context data for the alert"""
        try:
            stats = vegetation_index_set.stats.get(index_name, {})
            return {
                'acquisition_date': vegetation_index_set.acquisition_date.isoformat(),
                'index_stats': stats,
                'all_indices_stats': vegetation_index_set.stats
            }
        except Exception as e:
            self.logger.error(f"Error generating context data: {str(e)}")
            return {}
    
    def send_notifications(self, alert):
        """Send notifications for an alert"""
        try:
            for method in alert.rule.notification_methods:
                if method == 'email':
                    self.send_email_notification(alert)
                elif method == 'sms':
                    self.send_sms_notification(alert)
                elif method == 'webhook':
                    self.send_webhook_notification(alert)
                    
        except Exception as e:
            self.logger.error(f"Error sending notifications for alert {alert.id}: {str(e)}")
    
    def send_email_notification(self, alert):
        """Send email notification"""
        try:
            subject = f"[{alert.severity.upper()}] {alert.rule.name} - {alert.land.name}"
            message = f"""
Alert Details:
- Land: {alert.land.name}
- Index: {alert.index_name}
- Value: {alert.index_value:.3f}
- Threshold: {alert.threshold_value:.3f}
- Message: {alert.message}
- Triggered: {alert.triggered_at}

View details: {settings.FRONTEND_URL}/alerts/{alert.id}
            """.strip()
            
            # Create notification log
            notification = NotificationLog.objects.create(
                alert=alert,
                notification_type='email',
                recipient=alert.user.email,
                status='pending'
            )
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[alert.user.email],
                fail_silently=False
            )
            
            # Update notification log
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
            self.logger.info(f"Email notification sent for alert {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {str(e)}")
            # Update notification log with error
            try:
                notification = NotificationLog.objects.filter(
                    alert=alert,
                    notification_type='email'
                ).last()
                if notification:
                    notification.status = 'failed'
                    notification.error_message = str(e)
                    notification.save()
            except:
                pass
    
    def send_sms_notification(self, alert):
        """Send SMS notification (placeholder - implement with your SMS provider)"""
        try:
            # Create notification log
            notification = NotificationLog.objects.create(
                alert=alert,
                notification_type='sms',
                recipient=getattr(alert.user, 'phone_number', 'N/A'),
                status='pending'
            )
            
            # TODO: Implement SMS sending with your provider (Twilio, AWS SNS, etc.)
            # For now, just log
            self.logger.info(f"SMS notification would be sent for alert {alert.id}")
            
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
        except Exception as e:
            self.logger.error(f"Error sending SMS notification: {str(e)}")
    
    def send_webhook_notification(self, alert):
        """Send webhook notification"""
        try:
            # Create notification log
            notification = NotificationLog.objects.create(
                alert=alert,
                notification_type='webhook',
                recipient=getattr(settings, 'ALERT_WEBHOOK_URL', 'N/A'),
                status='pending'
            )
            
            # TODO: Implement webhook sending
            # For now, just log
            self.logger.info(f"Webhook notification would be sent for alert {alert.id}")
            
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
        except Exception as e:
            self.logger.error(f"Error sending webhook notification: {str(e)}")


class AlertManager:
    """Manager class for alert operations"""
    
    def __init__(self):
        self.processor = AlertProcessor()
    
    def process_new_vegetation_data(self, land, vegetation_index_set):
        """Process alerts for new vegetation index data"""
        self.processor.process_land_alerts(land, vegetation_index_set)
    
    def acknowledge_alert(self, alert_id, user):
        """Acknowledge an alert"""
        try:
            alert = Alert.objects.get(id=alert_id, user=user)
            alert.status = 'acknowledged'
            alert.acknowledged_at = timezone.now()
            alert.save()
            return True
        except Alert.DoesNotExist:
            return False
    
    def resolve_alert(self, alert_id, user):
        """Resolve an alert"""
        try:
            alert = Alert.objects.get(id=alert_id, user=user)
            alert.status = 'resolved'
            alert.resolved_at = timezone.now()
            alert.save()
            return True
        except Alert.DoesNotExist:
            return False
    
    def dismiss_alert(self, alert_id, user):
        """Dismiss an alert"""
        try:
            alert = Alert.objects.get(id=alert_id, user=user)
            alert.status = 'dismissed'
            alert.save()
            return True
        except Alert.DoesNotExist:
            return False
