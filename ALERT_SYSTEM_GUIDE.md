# 🚨 Alert System - Complete Guide

## Quick Answer: What You Need to Run Manually

**ONLY 2 THINGS:**
1. **Set up cron job** (one-time setup)
2. **Add crop instances** when you plant crops

**EVERYTHING ELSE IS AUTOMATIC!**

---

## 🔄 Automatic vs Manual

### ✅ AUTOMATIC (No work needed):
- Scenario creation when land is created
- Data fetching every 5 days
- Alert evaluation and creation
- Database updates

### 🔧 MANUAL (One-time setup):
- Cron job configuration
- Crop planting records

---

## 📊 How Each Alert Works

### 1. Rapid NDVI Drop
**Triggers when:** NDVI drops >15% vs previous observation
**Example:** 0.65 → 0.45 = -30% drop = ALERT
**Causes:** Water stress, disease, damage

### 2. Spatial Anomaly
**Triggers when:** >20% of field area shows >15% NDVI drop
**Example:** 15 out of 100 grid cells affected = ALERT
**Causes:** Localized disease, irrigation issues

### 3. Growth Stagnation
**Triggers when:** NDVI slope <0.01 for >10 days
**Example:** NDVI stays flat for 20 days = ALERT
**Causes:** Nutrient deficiency, poor soil

### 4. Below Historical Percentile
**Triggers when:** Current NDVI below 10th percentile vs historical
**Example:** Current 0.35, historical 10th percentile 0.38 = ALERT
**Causes:** Drought, climate stress

### 5. Phenology Delay
**Triggers when:** Start of season delayed >14 days after planting
**Example:** Planted Jan 15, should emerge Jan 25, actually Feb 10 = ALERT
**Causes:** Poor seed, cold weather, soil issues

### 6. Poor Emergence
**Triggers when:** >70% of observations below 0.2 NDVI after planting
**Example:** 5 out of 7 observations low = ALERT
**Causes:** Bad seed, planting too deep, soil crusting

### 7. Long-term Trend Decline
**Triggers when:** 2+ year declining NDVI trend
**Example:** 0.6 → 0.55 → 0.5 → 0.45 = ALERT
**Causes:** Soil degradation, climate change

---

## 🔧 Setup Instructions

### 1. Cron Job (One-time)
```bash
# Add to crontab
0 6 */5 * * docker compose exec web python Satellitor/manage.py fetch_satellite_data
```

### 2. Crop Planting (When you plant)
```json
POST /api/farm/crop-instances/
{
  "land": 1,
  "crop": 1,
  "planting_date": "2024-01-15",
  "season": "Winter"
}
```

---

## 🎯 Automatic Workflow

**Every 5 days at 6 AM:**
1. Fetch satellite data
2. Process GeoTIFF files
3. Extract statistics
4. Evaluate all 7 scenarios
5. Create alerts if triggered
6. Send notifications

**When you create a land:**
1. All 7 scenarios created automatically
2. Ready to monitor immediately

---

## 📱 API Endpoints

```bash
# Get all alerts
GET /api/alerts/alerts/

# Get alerts for land
GET /api/alerts/alerts/?land=1

# Get statistics
GET /api/alerts/alerts/stats/

# Acknowledge alert
POST /api/alerts/alerts/{id}/acknowledge/

# Resolve alert
POST /api/alerts/alerts/{id}/resolve/
```

---

## 🎉 Summary

**The system is 100% functional!**

- Set up cron job once
- Add crop instances when planting
- Everything else is automatic
- 7 scientific scenarios working
- Real-time monitoring every 5 days
- Complete API for frontend

**Just run the cron job and start planting - everything else happens automatically!** 🌱📡🚨
