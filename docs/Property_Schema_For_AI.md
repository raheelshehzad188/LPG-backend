# Property Table Schema — AI / Gemini Reference

`api_new_ai` property data ke liye `properties` table use karta hai. Yeh schema Gemini cache aur SQL filter ke liye reference hai.

## Table: `properties`

| Column         | Type           | Description                          | Example / Notes                    |
|----------------|----------------|--------------------------------------|------------------------------------|
| id             | INTEGER (PK)   | Auto-increment property ID           | 1, 2, 34                           |
| title          | VARCHAR(255)   | Property title                       | "5 Marla Spanish House DHA Phase 6"|
| location_name  | VARCHAR(100)   | Area/Location                        | DHA Defence, Bahria Nasheman       |
| price          | DECIMAL(15,2)  | Price in rupees (₹)                  | 18400000 = 1.84 crore               |
| area_size      | VARCHAR(50)    | Plot/house size                      | 5 Marla, 1 Kanal, 2000 sqft         |
| type           | VARCHAR(50)    | Property type                        | plot, Houses Property, flat        |
| description    | TEXT           | Full description                     | Long text                          |
| cover_photo    | VARCHAR(255)   | Image URL                            | https://... or empty               |
| bedrooms       | INTEGER        | Number of bedrooms                   | 3, 4                               |
| baths          | INTEGER        | Number of bathrooms                  | 2, 3                               |
| created_at     | DATETIME       | When added                           | For ordering                       |

## Filter Criteria (AI Engine)

Gemini `FILTER_CRITERIA` JSON mein yeh keys use karta hai:

| Key            | Type  | Meaning                    | SQL / Usage                              |
|----------------|-------|----------------------------|------------------------------------------|
| area           | string| Location (DHA, Bahria)    | `location_name ILIKE '%DHA%'`             |
| type           | string| plot, house, flat         | `type ILIKE '%plot%'`                     |
| budget_max_lac | number| Max budget in lakh         | `price <= budget_max_lac * 100000`        |

**Examples:**
- 5 crore → `budget_max_lac: 500`
- 50 lac → `budget_max_lac: 50`
- DHA plots 2 crore → `area: "DHA", type: "plot", budget_max_lac: 200`

## Scraping / Insert

Properties scraping se ya admin panel se add hoti hain. Insert ke waqt columns match karein:

```sql
INSERT INTO properties (title, location_name, price, area_size, type, description, cover_photo, bedrooms, baths)
VALUES ('Title', 'DHA Phase 6', 25000000, '5 Marla', 'plot', '...', 'https://...', NULL, NULL);
```

- `type` agar plots ke liye hai to "plot" ya "Plot" use karein (AI "plot" filter karta hai).
- `price` hamesha rupees mein (lac/crore nahi).
