# 🚨 Alert System Documentation

## **Overview**

The Alert System is a comprehensive monitoring and notification system that automatically triggers alerts based on vegetation index thresholds. It integrates seamlessly with the satellite data pipeline and provides real-time monitoring of farm conditions.

## **🏗️ Architecture**

### **Components**
- **Alert Rules**: Define conditions for triggering alerts
- **Alerts**: Individual alert instances when conditions are met
- **Notifications**: Delivery mechanisms (email, SMS, webhook)
- **Alert Processor**: Service layer for processing alerts
- **Management Commands**: Automated alert processing

### **Data Flow**
1. **Satellite Data Pipeline** fetches vegetation indices
2. **Alert Processor** evaluates all active rules
3. **Alerts** are created when conditions are met
4. **Notifications** are sent via configured methods
5. **Users** can acknowledge/resolve/dismiss alerts

## **📊 Models**

### **AlertRule**
Defines alert conditions and notification settings.

**Fields:**
- `name`: Rule name
- `description`: Rule description
- `land`: Associated land
- `user`: Rule owner
- `alert_type`: Type of alert (threshold, anomaly, trend, custom)
- `severity`: Alert severity (low, medium, high, critical)
- `index_name`: Vegetation index to monitor (NDVI, NDRE, EVI, SAVI, GCI)
- `threshold_value`: Threshold value for comparison
- `comparison_operator`: Comparison operator (gt, lt, gte, lte, eq, ne)
- `is_active`: Whether rule is active
- `notification_methods`: List of notification methods
- `cooldown_hours`: Hours to wait before triggering again
- `custom_script`: Custom evaluation script (for advanced rules)

### **Alert**
Individual alert instances when rules are triggered.

**Fields:**
- `rule`: Associated alert rule
- `land`: Associated land
- `user`: Alert owner
- `status`: Alert status (triggered, acknowledged, resolved, dismissed)
- `severity`: Alert severity
- `index_name`: Vegetation index that triggered alert
- `index_value`: Actual index value
- `threshold_value`: Threshold that was exceeded
- `comparison_operator`: Comparison operator used
- `vegetation_index_set`: Associated vegetation data
- `message`: Human-readable alert message
- `context_data`: Additional context data
- `triggered_at`: When alert was triggered
- `acknowledged_at`: When alert was acknowledged
- `resolved_at`: When alert was resolved

### **NotificationLog**
Logs of notification delivery attempts.

**Fields:**
- `alert`: Associated alert
- `notification_type`: Type of notification (email, sms, webhook, push)
- `recipient`: Notification recipient
- `status`: Delivery status (pending, sent, failed, delivered)
- `sent_at`: When notification was sent
- `delivered_at`: When notification was delivered
- `error_message`: Error message if delivery failed
- `response_data`: Provider response data

## **🔌 API Endpoints**

### **Alert Rules**

#### **List Alert Rules**
```
GET /api/alerts/alert-rules/
```

**Query Parameters:**
- `land`: Filter by land ID
- `alert_type`: Filter by alert type
- `severity`: Filter by severity
- `is_active`: Filter by active status
- `index_name`: Filter by index name
- `search`: Search in name and description
- `ordering`: Order by field (created_at, updated_at, name)

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Low NDVI Alert",
      "description": "Alert when NDVI drops below 0.3",
      "land": 1,
      "land_name": "Field A",
      "user": 1,
      "user_email": "farmer@example.com",
      "alert_type": "threshold",
      "severity": "medium",
      "index_name": "NDVI",
      "threshold_value": 0.3,
      "comparison_operator": "lt",
      "is_active": true,
      "notification_methods": ["email", "sms"],
      "custom_script": "",
      "cooldown_hours": 24,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### **Create Alert Rule**
```
POST /api/alerts/alert-rules/
```

**Request Body:**
```json
{
  "name": "Low NDVI Alert",
  "description": "Alert when NDVI drops below 0.3",
  "land": 1,
  "alert_type": "threshold",
  "severity": "medium",
  "index_name": "NDVI",
  "threshold_value": 0.3,
  "comparison_operator": "lt",
  "is_active": true,
  "notification_methods": ["email", "sms"],
  "cooldown_hours": 24
}
```

#### **Test Alert Rule**
```
POST /api/alerts/alert-rules/{id}/test_rule/
```

**Response:**
```json
{
  "rule_name": "Low NDVI Alert",
  "index_name": "NDVI",
  "index_value": 0.25,
  "threshold_value": 0.3,
  "comparison_operator": "lt",
  "should_trigger": true,
  "test_data_date": "2024-01-15"
}
```

### **Alerts**

#### **List Alerts**
```
GET /api/alerts/alerts/
```

**Query Parameters:**
- `land`: Filter by land ID
- `status`: Filter by status
- `severity`: Filter by severity
- `index_name`: Filter by index name
- `rule`: Filter by rule ID
- `search`: Search in message, land name, rule name
- `ordering`: Order by field (triggered_at, severity, index_value)

**Response:**
```json
{
  "count": 25,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "rule": 1,
      "rule_name": "Low NDVI Alert",
      "land": 1,
      "land_name": "Field A",
      "user": 1,
      "user_email": "farmer@example.com",
      "status": "triggered",
      "severity": "medium",
      "index_name": "NDVI",
      "index_value": 0.25,
      "threshold_value": 0.3,
      "comparison_operator": "lt",
      "vegetation_index_set": 1,
      "acquisition_date": "2024-01-15",
      "message": "Alert: NDVI value (0.250) is less than threshold (0.300) for land Field A",
      "context_data": {
        "acquisition_date": "2024-01-15",
        "index_stats": {
          "min": 0.1,
          "max": 0.4,
          "mean": 0.25,
          "std": 0.05,
          "count": 1000
        }
      },
      "triggered_at": "2024-01-15T10:30:00Z",
      "acknowledged_at": null,
      "resolved_at": null
    }
  ]
}
```

#### **Acknowledge Alert**
```
POST /api/alerts/alerts/{id}/acknowledge/
```

**Response:**
```json
{
  "status": "acknowledged"
}
```

#### **Resolve Alert**
```
POST /api/alerts/alerts/{id}/resolve/
```

**Response:**
```json
{
  "status": "resolved"
}
```

#### **Dismiss Alert**
```
POST /api/alerts/alerts/{id}/dismiss/
```

**Response:**
```json
{
  "status": "dismissed"
}
```

#### **Alert Statistics**
```
GET /api/alerts/alerts/stats/
```

**Response:**
```json
{
  "total_alerts": 150,
  "triggered_alerts": 25,
  "acknowledged_alerts": 20,
  "resolved_alerts": 100,
  "dismissed_alerts": 5,
  "alerts_by_severity": {
    "low": 10,
    "medium": 80,
    "high": 50,
    "critical": 10
  },
  "alerts_by_land": {
    "Field A": 60,
    "Field B": 40,
    "Field C": 30,
    "Field D": 20
  },
  "recent_alerts": [...]
}
```

#### **Alert Dashboard**
```
GET /api/alerts/alerts/dashboard/
```

**Response:**
```json
{
  "critical_alerts": [...],
  "daily_counts": [
    {"day": "2024-01-15", "count": 5},
    {"day": "2024-01-16", "count": 3},
    {"day": "2024-01-17", "count": 8}
  ],
  "total_recent": 16,
  "unresolved": 12
}
```

### **Notification Logs**

#### **List Notification Logs**
```
GET /api/alerts/notification-logs/
```

**Query Parameters:**
- `alert`: Filter by alert ID
- `notification_type`: Filter by notification type
- `status`: Filter by delivery status
- `search`: Search in alert message, land name
- `ordering`: Order by field (created_at, sent_at)

## **⚙️ Configuration**

### **Environment Variables**

Add these to your `.env` file:

```env
# Email Settings
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Frontend URL (for alert links)
FRONTEND_URL=https://yourdomain.com

# Webhook URL (optional)
ALERT_WEBHOOK_URL=https://your-webhook-endpoint.com/alerts
```

### **Docker Compose Updates**

Add email service to your `docker-compose.yml`:

```yaml
services:
  # ... existing services ...
  
  mail:
    image: mailhog/mailhog:latest
    container_name: satellitor_mail
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI
```

## **🚀 Usage Examples**

### **1. Create a Basic NDVI Alert**

```bash
curl -X POST "http://localhost:8000/api/alerts/alert-rules/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Low NDVI Alert",
    "description": "Alert when NDVI drops below 0.3",
    "land": 1,
    "alert_type": "threshold",
    "severity": "medium",
    "index_name": "NDVI",
    "threshold_value": 0.3,
    "comparison_operator": "lt",
    "is_active": true,
    "notification_methods": ["email"],
    "cooldown_hours": 24
  }'
```

### **2. Test an Alert Rule**

```bash
curl -X POST "http://localhost:8000/api/alerts/alert-rules/1/test_rule/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### **3. Acknowledge an Alert**

```bash
curl -X POST "http://localhost:8000/api/alerts/alerts/1/acknowledge/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### **4. Get Alert Dashboard**

```bash
curl -X GET "http://localhost:8000/api/alerts/alerts/dashboard/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## **🔧 Management Commands**

### **Process Alerts**
```bash
# Process alerts for recent data (last 24 hours)
python manage.py process_alerts

# Process alerts for specific land
python manage.py process_alerts --land-id 1

# Process alerts for last 48 hours
python manage.py process_alerts --hours-back 48

# Dry run (test without creating alerts)
python manage.py process_alerts --dry-run
```

### **Docker Commands**
```bash
# Process alerts in Docker
docker compose exec web python manage.py process_alerts

# Process alerts for specific land
docker compose exec web python manage.py process_alerts --land-id 1
```

## **📈 Monitoring and Maintenance**

### **Alert Processing Flow**
1. **Satellite data** is fetched every 5 days
2. **Vegetation indices** are calculated and stored
3. **Alert processor** evaluates all active rules
4. **Alerts** are created for triggered conditions
5. **Notifications** are sent via configured methods

### **Best Practices**
- **Set appropriate thresholds** based on historical data
- **Use cooldown periods** to prevent alert spam
- **Monitor notification delivery** via logs
- **Regularly review and update** alert rules
- **Test rules** before activating them

### **Troubleshooting**
- Check **notification logs** for delivery failures
- Verify **email settings** in environment variables
- Monitor **alert processor** logs for errors
- Test **alert rules** using the test endpoint

## **🔒 Security Considerations**

- **User isolation**: Users can only see their own alerts and rules
- **Permission-based access**: Alert management requires authentication
- **Secure notifications**: Email credentials should be properly secured
- **Webhook security**: Implement proper authentication for webhook endpoints

## **📊 Performance Considerations**

- **Database indexing**: Ensure proper indexes on frequently queried fields
- **Alert cooldowns**: Prevent excessive alert generation
- **Notification batching**: Consider batching notifications for high-volume scenarios
- **Background processing**: Use Celery for heavy alert processing if needed

---

**🎉 Your alert system is now fully integrated with the satellite data pipeline and ready for production use!**
