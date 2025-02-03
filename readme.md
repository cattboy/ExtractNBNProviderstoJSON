# NBNProviderScraper
Scrapes NBN website for Retail Service Providers (RSPs), outputs to JSON https://www.nbnco.com.au/residential/service-providers

-- Logs
Only 5 logs are kept, the oldest is deleted when a new log is created.

-- OUTPUT
If filesize and length of files are different move the current file in OUTPUT into a folder called OUTPUT_History, only keeping 5 latest files. 