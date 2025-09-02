# Euraxess Scraper

This project is a web scraper for extracting job listings from the Euraxess website using Scrapy. It processes and saves job data to CSV files for further analysis.

## Features

- Scrapes job postings from Euraxess
- Outputs results to CSV files in the `output/` directory

## Project Structure

```
├── app.py                 # Main application entry point
├── scrapy.cfg             # Scrapy configuration file
├── euraxess/              # Scrapy project directory
│   ├── items.py           # Item definitions
│   ├── middlewares.py     # Custom middlewares
│   ├── pipelines.py       # Data pipelines
│   ├── settings.py        # Scrapy settings
│   └── spiders/           # Spider definitions
│       └── euraxess.py    # Main spider for Euraxess
├── output/                # Output CSV files
└── README.md              # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.12+
- Scrapy
- Streamlit

### Running the Scraper

To run the spider and save results to CSV:

```powershell
scrapy crawl euraxess_scraper
```

Launch the Streamlit app for interactive filtering:

```powershell
streamlit run app.py
```
