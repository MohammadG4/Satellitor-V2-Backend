# Satellitor Farm API Documentation

## Base URL

```
http://localhost:8000/api/farm/
```

## Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

To get a token, use the login endpoint:

```bash
POST /api/login/
{
  "email": "admin@outlook.com",
  "password": "admin112"
}
```

## Permissions

- **Lands, Land Sizes, Crop Instances**: Users can only see/modify their own data
- **Vegetation Index Sets**: Read-only for all authenticated users (own data only), only staff/admin can create/update/delete
- **Crops**: Read-only for all authenticated users, only staff/admin can create/update/delete
- **All endpoints**: Require authentication

---

## 1. Lands

### List Lands

**GET** `/lands/`

**Response:**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Field A",
      "created_date": "2025-01-08T00:00:00Z",
      "last_updated": "2025-01-08T00:00:00Z",
      "user": 1,
      "location": "Test farm",
      "soil_type": "Sandy",
      "irrigation_type": "Drip",
      "status": true,
      "notes": "North plot",
      "image_url": null,
      "boundary": {
        "type": "Polygon",
        "coordinates": [
          [
            [31.0, 30.0],
            [31.01, 30.0],
            [31.01, 30.01],
            [31.0, 30.01],
            [31.0, 30.0]
          ]
        ]
      }
    }
  ]
}
```

### Create Land

**POST** `/lands/`

**Request:**

```json
{
  "name": "Field A",
  "location": "Test farm",
  "soil_type": "Sandy",
  "irrigation_type": "Drip",
  "status": true,
  "notes": "North plot",
  "image_url": "https://example.com/farm.jpg",
  "boundary": {
    "type": "Polygon",
    "coordinates": [
      [
        [30.069427803367414, 31.311796903610233],
        [30.068495408742663, 31.312247514724735],
        [30.068722709734566, 31.312944889068607],
        [30.06967829594864, 31.312483549118046],
        [30.069933426629607, 31.311941742897037],
        [30.069427803367414, 31.311796903610233]
      ]
    ]
  }
}
```

**Response:**

```json
{
  "id": 1,
  "name": "Field A",
  "created_date": "2025-01-08T00:00:00Z",
  "last_updated": "2025-01-08T00:00:00Z",
  "user": 1,
  "location": "Test farm",
  "soil_type": "Sandy",
  "irrigation_type": "Drip",
  "status": true,
  "notes": "North plot",
  "image_url": "https://example.com/farm.jpg",
  "boundary": {
    "type": "Polygon",
    "coordinates": [
      [
        [31.0, 30.0],
        [31.01, 30.0],
        [31.01, 30.01],
        [31.0, 30.01],
        [31.0, 30.0]
      ]
    ]
  }
}
```

Note: Upon land creation, the API automatically computes and stores land sizes in `LandSize` for these units: `square_meter`, `hectare`, `acre`, `feddan`.

### Get Land by ID

**GET** `/lands/{id}/`

**Response:** Same as create response

### Update Land

**PUT/PATCH** `/lands/{id}/`

**Request:** Same as create request (partial updates allowed with PATCH)

**Response:** Same as create response

### Delete Land

**DELETE** `/lands/{id}/`

**Response:** `204 No Content`

---

## 2. Land Sizes

### List Land Sizes

**GET** `/land-sizes/`

**Response:**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "land": 1,
      "value": "5.50",
      "unit": "hectare"
    }
  ]
}
```

### Get Land Sizes (by size id, returns all 4 units)

**GET** `/land-sizes/{id}/`

Given a specific LandSize id (any unit) that belongs to the authenticated user, the endpoint returns all four sizes for that land: `square_meter`, `hectare`, `acre`, `feddan`.

Example: `GET /api/farm/land-sizes/12/`

**Response:**

```json
[
  { "id": 10, "land": 1, "value": "55000.0000", "unit": "square_meter" },
  { "id": 11, "land": 1, "value": "5.5000", "unit": "hectare" },
  { "id": 12, "land": 1, "value": "13.5903", "unit": "acre" },
  { "id": 13, "land": 1, "value": "13.0952", "unit": "feddan" }
]
```

### Create Land Size

**POST** `/land-sizes/`

**Request:**

```json
{
  "land": 1,
  "value": "5.50",
  "unit": "hectare"
}
```

**Response:**

```json
{
  "id": 1,
  "land": 1,
  "value": "5.50",
  "unit": "hectare"
}
```

Note: Creating a land size manually will normalize and upsert all four units for the land based on the submitted value and unit.

### Update Land Size (synchronizes all units)

**PATCH** `/land-sizes/{id}/`

Updating any one size will recalculate and update the other three units for the same land to keep values consistent.

**Request:**

```json
{ "value": 12.5, "unit": "acre" }
```

**Response:** Returns all four sizes for that land (array), not just the patched item.

```json
[
  { "id": 10, "land": 1, "value": "50600.0000", "unit": "square_meter" },
  { "id": 11, "land": 1, "value": "5.06", "unit": "hectare" },
  { "id": 12, "land": 1, "value": "12.5", "unit": "acre" },
  { "id": 13, "land": 1, "value": "12.0476", "unit": "feddan" }
]
```

 

**Unit Choices:**

- `feddan`
- `acre`
- `hectare`
- `square_meter`

---

## 3. Crops

### List Crops

**GET** `/crops/`

**Permissions:** Read-only for all authenticated users

**Response:**

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "crop_name": "Wheat",
      "description": "Cereal crop"
    },
    {
      "id": 2,
      "crop_name": "Tomato",
      "description": "Vegetable crop"
    }
  ]
}
```

### Create Crop

**POST** `/crops/`

**Permissions:** Staff/Admin only

**Request:**

```json
{
  "crop_name": "Wheat",
  "description": "Cereal crop"
}
```

**Response:**

```json
{
  "id": 1,
  "crop_name": "Wheat",
  "description": "Cereal crop"
}
```

### Update Crop

**PUT/PATCH** `/crops/{id}/`

**Permissions:** Staff/Admin only

**Request:** Same as create request (partial updates allowed with PATCH)

**Response:** Same as create response

### Delete Crop

**DELETE** `/crops/{id}/`

**Permissions:** Staff/Admin only

**Response:** `204 No Content`

---

## 4. Crop Instances

### List Crop Instances

**GET** `/crop-instances/`

**Response:**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "land": 1,
      "crop": 1,
      "planting_date": "2025-01-15",
      "harvest_date": null,
      "season": "Winter"
    }
  ]
}
```

### Create Crop Instance

**POST** `/crop-instances/`

**Request:**

```json
{
  "land": 1,
  "crop": 1,
  "planting_date": "2025-01-15",
  "harvest_date": "2025-06-15",
  "season": "Winter"
}
```

**Response:**

```json
{
  "id": 1,
  "land": 1,
  "crop": 1,
  "planting_date": "2025-01-15",
  "harvest_date": "2025-06-15",
  "season": "Winter"
}
```

**Season Choices:**

- `Winter` (شتوي)
- `Summer` (صيفي)
- `Nile` (نيل)
- `Spring` (ربيعي)
- `Autumn` (خريفي)

---

## 5. Vegetation Index Sets

### List Vegetation Index Sets

**GET** `/vegetation-index-sets/`

**Permissions:** Users can only see vegetation index sets for their own lands

**Query Parameters:**

- `land` - Filter by specific land ID (e.g., `?land=1`)
- `acquisition_date` - Filter by specific acquisition date (e.g., `?acquisition_date=2025-01-20`)
- `search` - Search by land name (e.g., `?search=Field A`)
- `ordering` - Order by field (e.g., `?ordering=acquisition_date` or `?ordering=-created_at`)
- `page` - Page number for pagination (e.g., `?page=1`)
- `page_size` - Number of results per page (e.g., `?page_size=20`)

**Examples:**

- Get all vegetation index sets for user's lands: `GET /vegetation-index-sets/`
- Get vegetation index sets for specific land: `GET /vegetation-index-sets/?land=1`
- Get vegetation index sets for specific date: `GET /vegetation-index-sets/?acquisition_date=2025-01-20`
- Get vegetation index sets for specific land and date: `GET /vegetation-index-sets/?land=1&acquisition_date=2025-01-20`
- Search by land name: `GET /vegetation-index-sets/?search=Field A`
- Order by acquisition date (newest first): `GET /vegetation-index-sets/?ordering=-acquisition_date`

**Response:**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "land": 1,
      "acquisition_date": "2025-01-20",
      "file_path": "/data/indices_2025-01-20.tif",
      "stats": {
        "NDVI": {
          "min": -0.2,
          "max": 0.9,
          "mean": 0.55
        },
        "NDRE": {
          "min": -0.1,
          "max": 0.8,
          "mean": 0.45
        },
        "NDMI": {
          "min": -0.3,
          "max": 0.7,
          "mean": 0.3
        }
      },
      "created_at": "2025-01-08T00:00:00Z"
    }
  ]
}
```

### Create Vegetation Index Set

**POST** `/vegetation-index-sets/`

**Permissions:** Staff/Admin only

**Request:**

```json
{
  "land": 1,
  "acquisition_date": "2025-01-20",
  "file_path": "/data/indices_2025-01-20.tif",
  "stats": {
    "NDVI": {
      "min": -0.2,
      "max": 0.9,
      "mean": 0.55
    },
    "NDRE": {
      "min": -0.1,
      "max": 0.8,
      "mean": 0.45
    },
    "NDMI": {
      "min": -0.3,
      "max": 0.7,
      "mean": 0.3
    }
  }
}
```

**Response:**

```json
{
  "id": 1,
  "land": 1,
  "acquisition_date": "2025-01-20",
  "file_path": "/data/indices_2025-01-20.tif",
  "stats": {
    "NDVI": {
      "min": -0.2,
      "max": 0.9,
      "mean": 0.55
    },
    "NDRE": {
      "min": -0.1,
      "max": 0.8,
      "mean": 0.45
    },
    "NDMI": {
      "min": -0.3,
      "max": 0.7,
      "mean": 0.3
    }
  },
  "created_at": "2025-01-08T00:00:00Z"
}
```

### Update Vegetation Index Set

**PUT/PATCH** `/vegetation-index-sets/{id}/`

**Permissions:** Staff/Admin only

**Request:** Same as create request (partial updates allowed with PATCH)

**Response:** Same as create response

### Delete Vegetation Index Set

**DELETE** `/vegetation-index-sets/{id}/`

**Permissions:** Staff/Admin only

**Response:** `204 No Content`

---

## Error Responses

### 400 Bad Request

```json
{
  "field_name": ["This field is required."]
}
```

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Common 403 scenarios:**

- Regular users trying to create/update/delete crops (staff/admin only)
- Regular users trying to create/update/delete vegetation index sets (staff/admin only)
- Users trying to access other users' lands, crop instances, or vegetation data

### 404 Not Found

```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error

```json
{
  "detail": "A server error occurred."
}
```

---

## Frontend Integration Examples

### JavaScript/Fetch

```javascript
// Get JWT token
const loginResponse = await fetch("http://localhost:8000/api/login/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    email: "admin@outlook.com",
    password: "admin112",
  }),
});

const { access } = await loginResponse.json();

// Create a land
const landResponse = await fetch("http://localhost:8000/api/farm/lands/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${access}`,
  },
  body: JSON.stringify({
    name: "My Farm",
    location: "Cairo, Egypt",
    soil_type: "Clay",
    irrigation_type: "Sprinkler",
    status: true,
    notes: "Main field",
    boundary: {
      type: "Polygon",
      coordinates: [
        [
          [31.0, 30.0],
          [31.01, 30.0],
          [31.01, 30.01],
          [31.0, 30.01],
          [31.0, 30.0],
        ],
      ],
    },
  }),
});

const land = await landResponse.json();
console.log("Created land:", land);
```

### Python/Requests

```python
import requests

# Get JWT token
login_response = requests.post('http://localhost:8000/api/login/', json={
    'email': 'admin@outlook.com',
    'password': 'admin112'
})
access_token = login_response.json()['access']

# Create a land
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

land_data = {
    'name': 'My Farm',
    'location': 'Cairo, Egypt',
    'soil_type': 'Clay',
    'irrigation_type': 'Sprinkler',
    'status': True,
    'notes': 'Main field',
    'boundary': {
        'type': 'Polygon',
        'coordinates': [[
            [31.0, 30.0],
            [31.01, 30.0],
            [31.01, 30.01],
            [31.0, 30.01],
            [31.0, 30.0]
        ]]
    }
}

response = requests.post('http://localhost:8000/api/farm/lands/',
                        json=land_data, headers=headers)
land = response.json()
print('Created land:', land)
```

### cURL Examples

```bash
# Login
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@outlook.com","password":"admin112"}'

# Create land (replace TOKEN with actual token)
curl -X POST http://localhost:8000/api/farm/lands/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Farm",
    "location": "Cairo, Egypt",
    "soil_type": "Clay",
    "irrigation_type": "Sprinkler",
    "status": true,
    "notes": "Main field",
    "boundary": {
      "type": "Polygon",
      "coordinates": [[[31.0,30.0],[31.01,30.0],[31.01,30.01],[31.0,30.01],[31.0,30.0]]]
    }
  }'
```

---

## Notes

1. **GeoJSON Format**: All polygon boundaries use GeoJSON format with WGS84 coordinates (longitude, latitude)
2. **User Filtering**: Users can only see their own lands, land sizes, crop instances, and vegetation index sets
3. **Crop Permissions**: Crops are read-only for regular users, only staff/admin can create/update/delete
4. **Vegetation Index Sets Permissions**: Read-only for regular users (own data only), only staff/admin can create/update/delete
5. **Date Format**: All dates use ISO 8601 format (YYYY-MM-DD)
6. **Pagination**: List endpoints support pagination with `?page=1&page_size=20`
7. **Filtering**: Use query parameters like `?land=1` to filter by related objects
8. **Bounding Box**: Lands endpoint supports `?in_bbox=min_lon,min_lat,max_lon,max_lat` for spatial filtering
9. **Staff Access**: To create/update/delete crops and vegetation index sets, user must have `is_staff=True` (admin users)
10. **Vegetation Index Sets Filtering**:

- Filter by specific land: `?land=1`
- Filter by acquisition date: `?acquisition_date=2025-01-20`
- Combine filters: `?land=1&acquisition_date=2025-01-20`
- Search by land name: `?search=Field A`
- Order results: `?ordering=-acquisition_date` (newest first)
