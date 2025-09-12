#!/bin/bash

# Alert System Cron Setup Script
echo "🚨 Setting up Alert System Cron Job..."

# Add cron job for satellite data fetching every 5 days at 6 AM
(crontab -l 2>/dev/null; echo "0 6 */5 * * cd /path/to/Satellitor-V2 && docker compose exec web python Satellitor/manage.py fetch_satellite_data") | crontab -

echo "✅ Cron job added successfully!"
echo "📅 Satellite data will be fetched every 5 days at 6:00 AM"
echo ""
echo "🔧 Manual steps remaining:"
echo "1. Update the path in the cron job to match your actual project path"
echo "2. Add crop instances when you plant crops"
echo "3. Monitor alerts via API endpoints"
echo ""
echo "🎉 Alert system is ready to go!"
