# Alert System Cron Setup Script for Windows
Write-Host "🚨 Setting up Alert System Cron Job..." -ForegroundColor Green

# Instructions for Windows Task Scheduler
Write-Host ""
Write-Host "📋 WINDOWS SETUP INSTRUCTIONS:" -ForegroundColor Yellow
Write-Host "1. Open Task Scheduler (taskschd.msc)" -ForegroundColor White
Write-Host "2. Create Basic Task" -ForegroundColor White
Write-Host "3. Name: 'Satellite Data Fetch'" -ForegroundColor White
Write-Host "4. Trigger: Daily, every 5 days" -ForegroundColor White
Write-Host "5. Action: Start a program" -ForegroundColor White
Write-Host "6. Program: docker" -ForegroundColor White
Write-Host "7. Arguments: compose exec web python Satellitor/manage.py fetch_satellite_data" -ForegroundColor White
Write-Host "8. Start in: C:\Django\Satellitor-V2" -ForegroundColor White
Write-Host ""
Write-Host "✅ After setup, the system will run automatically!" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Manual steps remaining:" -ForegroundColor Yellow
Write-Host "1. Add crop instances when you plant crops" -ForegroundColor White
Write-Host "2. Monitor alerts via API endpoints" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Alert system is ready to go!" -ForegroundColor Green
