# The Faceless Traveller 🌍

An interactive personal travel dashboard exploring destinations,
travel experiences and stories from around the world.

## Features

- Interactive world map showing visited and bucket-list destinations
- Travel statistics and destination breakdowns
- Continent distribution chart
- Top five most visited countries
- Seven Wonders of the World tracker
- Dynamic travel stories linked to WordPress articles

## Technology

- Python
- Streamlit
- Pandas
- Plotly
- PyCountry
- Pillow
- Google Sheets (published CSV data source)

## Project Structure

```text
the-faceless-traveller/
├── run_app.py
├── requirements.txt
├── README.md
└── wonders/
    └── Seven Wonders image files
```

## Run Locally

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the dashboard:

```bash
streamlit run run_app.py
```

## Data Source

Travel data is maintained in Google Sheets and retrieved
through its published CSV link. Blog titles and URLs are
managed through the same spreadsheet.

## Author

The Faceless Traveller
