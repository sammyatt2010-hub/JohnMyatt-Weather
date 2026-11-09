# 🌦️ Dad's Weather

A personal weather app for two homes: **Middle Farm** (Fairoak, Eccleshall, ST21 6NT) and **Salcombe**.

- Current conditions, plain-English "what to expect" notes (rain timing, frost, gales, drying days, rough sea)
- 48-hour temperature/rain and wind charts, plus an hour-by-hour table
- 14-day outlook
- Sea tab for Salcombe (wave height, wave period, sea temperature)
- Side-by-side comparison of both homes
- Monet *Water Lilies* theme: a different Monet water-garden painting behind the weather card each day
- 🖼️ Painting Finder (link at the bottom): searches Wikipedia and Wikimedia Commons for high-resolution images of paintings

Forecast data comes from [Open-Meteo](https://open-meteo.com). Paintings come from Wikipedia/Wikimedia Commons. Both are free and need no API keys or secrets.

## Deploy
1. Create a new GitHub repo and upload `app.py`, `requirements.txt` and `.streamlit/config.toml`.
2. On share.streamlit.io choose **Create app**, pick the repo, set the main file to `app.py` and deploy.

## Personalise
At the top of `app.py`, change `DAD_NAME` to his name, or edit the `LOCATIONS` coordinates.
