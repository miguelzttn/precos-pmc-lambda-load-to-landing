# Preços PMC - Lambda Load to Landing

AWS Lambda function to extract Clique Economia pricing data and load to S3 landing zone.

## Overview

This Lambda function retrieves CSV files from Curitiba's Clique Economia open data portal and stores them in the `precos-pmc-landing` S3 bucket with date-based partitioning.

## Features

- **Date-based processing**: Process data for specific dates or date ranges
- **Automatic fallback**: Uses previous day if no date is specified
- **Bulk reprocessing**: Reprocess all historical data (from 2022-06-22)
- **Multiple data sources**: Attempts both current and archived URLs
- **Timezone aware**: Uses Brazil/São Paulo timezone (BRT)

## Payload Structure

```json
{
  "date": "YYYY-MM-DD",              
  "dates": ["YYYY-MM-DD", "YYYY-MM-DD"],
  "reprocess_all_dates": false
}
```

**Parameters:**
- `date` (optional): Single date to process
- `dates` (optional): Array of dates to process
- `reprocess_all_dates` (optional): When `true`, reprocesses all dates since 2022-06-22

If no parameters are provided, processes yesterday's data.

## Files Retrieved

For each date, the function attempts to download:
- `{date}_Clique_Economia_-_Produto_-_Dicionario_de_Dados.csv`
- `{date}_Clique_Economia_-_Produto_-_Base_de_Dados.csv`
- `{date}_Clique_Economia_-_Dicionario_de_Dados.csv`
- `{date}_Clique_Economia_-_Cotacoes_-_Base_de_Dados.csv`
- `{date}_Clique_Economia_-_Base_de_Dados.csv`

## S3 Structure

Files are stored with the following prefix pattern:
```
s3://precos-pmc-landing/YYYY/MM/DD/{filename}
```

## Deployment

The function is automatically deployed via GitHub Actions on push to `main` branch using AWS OIDC authentication.

### Manual Deployment

```bash
cd src
zip -r ../function.zip .
aws lambda update-function-code \
  --function-name precos-pmc-lambda-load-to-landing \
  --zip-file fileb://function.zip
```

## Bulk execution of all files

As the timeout for this lambda is configured for 15 minutes while the execution 
of entire history takes longer than 4 hours as on January, 2026, the file 
`src/bulk_run.py` is provided.

One can execute it to load all files to landing zone.

## Dependencies

- `boto3`: AWS SDK for Python
- `urllib3`: HTTP client for file retrieval

## Environment

- **Runtime**: Python 3.x
- **Region**: us-east-2
- **IAM Role**: Requires S3 write permissions to `precos-pmc-landing` bucket

## Response

Returns HTTP 200 on success or 500 on error with detailed processing messages for each date.