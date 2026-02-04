# Astrology Backend for COGNICOO Child Compass

Python + Flask backend that calculates Western (Tropical) and Vedic (Sidereal) astrology charts using Swiss Ephemeris.

## Features

- **Western Astrology** - Tropical zodiac, Placidus houses, major aspects
- **Vedic Astrology** - Sidereal zodiac (Lahiri ayanamsa), Nakshatras, Rashi chart
- **Swiss Ephemeris** - Accurate planetary calculations
- **Fast** - Typical response time <100ms

## API Endpoints

### Health Check
```bash
GET /health
```

### Calculate Western Chart
```bash
POST /calculate/western
Content-Type: application/json

{
  "date": "1990-05-15",
  "time": "14:30",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  }
}
```

**Response:**
```json
{
  "type": "western",
  "planets": {
    "Sun": {
      "sign": "Taurus",
      "degree": 24.123,
      "formatted": "Taurus 24°07'"
    },
    "Moon": { ... },
    ...
  },
  "houses": {
    "system": "Placidus",
    "ascendant": { "sign": "Leo", "degree": 15.5 },
    "midheaven": { "sign": "Taurus", "degree": 10.2 }
  },
  "aspects": [
    {
      "planet1": "Sun",
      "planet2": "Moon",
      "aspect": "Trine",
      "angle": 120,
      "orb": 3.5
    }
  ],
  "sunSign": "Taurus",
  "moonSign": "Capricorn",
  "risingSign": "Leo"
}
```

### Calculate Vedic Chart
```bash
POST /calculate/vedic
```

**Response:**
```json
{
  "type": "vedic",
  "planets": {
    "Sun": {
      "sign": "Mesha",
      "degree": 1.234
    },
    ...
  },
  "lagna": {
    "sign": "Karka",
    "degree": 22.5
  },
  "nakshatra": {
    "name": "Rohini",
    "pada": 2,
    "formatted": "Rohini Pada 2"
  },
  "moonSign": "Makara",
  "sunSign": "Mesha"
}
```

### Calculate Both
```bash
POST /calculate/both
```

Returns both Western and Vedic charts in one response.

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
# Server runs on http://localhost:3001

# Test
curl -X POST http://localhost:3001/calculate/western \
  -H "Content-Type: application/json" \
  -d '{
    "date": "1990-05-15",
    "time": "14:30",
    "location": {"latitude": 40.7128, "longitude": -74.0060}
  }'
```

## Deploy to Railway

1. **Via GitHub:**
   ```bash
   cd astrology-backend
   git init
   git add .
   git commit -m "Initial astrology backend"
   gh repo create astrology-backend --public --source=. --push
   ```

2. **In Railway Dashboard:**
   - New Project → Deploy from GitHub
   - Select `astrology-backend` repo
   - Railway auto-detects Python and deploys
   - Environment variables: None needed!

3. **Get URL:**
   - Railway provides: `https://astrology-backend-production.up.railway.app`
   - Health check: `curl https://astrology-backend-production.up.railway.app/health`

## Cost

- **Development:** FREE (Python + Swiss Ephemeris are open source)
- **Railway Hosting:** FREE tier (500 hours/month + $5 credit)
- **Per-request:** $0 (unlike paid APIs that charge per chart)

## Integration with iOS App

Update `WesternAstrologyService.swift` and `VedicAstrologyService.swift`:

```swift
private let apiEndpoint = "https://astrology-backend-production.up.railway.app"

func calculate(for person: PersonData) async throws -> WesternChart {
    let url = URL(string: "\(apiEndpoint)/calculate/western")!
    // ... make POST request
}
```

## Accuracy

Swiss Ephemeris is used by professional astrologers worldwide. Accuracy:
- Planetary positions: ±1 arc second
- House cusps: ±1 arc minute
- Time range: 13,000 BCE to 17,000 CE

## License

MIT - Swiss Ephemeris is dual-licensed (GPL/Commercial). This project uses it under GPL.
