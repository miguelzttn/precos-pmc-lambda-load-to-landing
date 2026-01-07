import json

from pmc_client import CliqueEconomiaClient
from my_utils import (
    _find_dates_in_event,
    _get_brt_yesterday,
    _list_all_possible_dates,
    _send_to_s3_landing
)

"""
    Lambda function to process Clique Economia files and upload them to S3 landing zone.

    payload can be:
    {

        "date": "YYYY-MM-DD",               # Optional: Specific date to process. 
                                                        If not passed, uses yesterday.

        "dates": ["YYYY-MM-DD", ...],       # Optional: List of specific dates to process.
                                                        If not passed, uses yesterday.

        "reprocess_all_dates": true|false   # Optional: Flag to reprocess all possible dates
                                                        If passed, overrides 'date' and 'dates' parameters.
                                                        If not passed or false, processes only the specified dates or yesterday.
    
    }

"""

def lambda_handler(event, context):
    
    messages = []
    success = True
    
    date_references = _find_dates_in_event(event) or [_get_brt_yesterday()]
    if event.get('reprocess_all_dates', False):
        date_references = _list_all_possible_dates()

    files_client = CliqueEconomiaClient()
    
    for date_reference in date_references:

        try:            
            files = files_client.get_files_by_date(date_reference=date_reference)
            responses = {}

            for filename, content in files.items():
                status, msg = _send_to_s3_landing(date_reference, filename, content)
                responses[filename] = msg

                if not status:
                    success = False
    
            msg = {
                'message': (
                    f'Processed files for date: {date_reference.strftime("%Y-%m-%d")}' if responses 
                    else f'No files found for date: {date_reference.strftime("%Y-%m-%d")}'
                ),
                'responses': responses
            }
            
            messages.append(json.dumps(msg))

        except Exception as e:
            success = False
            msg = {
                'message': f'Error processing files: {e}',
                'responses': []
            }
            messages.append(json.dumps(msg))

    return {
        'statusCode': 200 if success else 500,
        'body': json.dumps(messages)
    }