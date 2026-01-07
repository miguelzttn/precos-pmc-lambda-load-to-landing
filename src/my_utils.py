import json
import boto3

from io import BytesIO
from zoneinfo import ZoneInfo
from typing import List, Tuple
from datetime import datetime, timedelta

def _find_dates_in_event(event) -> List[datetime]:

    dates_found = []
    
    date = event.get('date')
    if date:
        dates_found.append(date)
    
    dates = event.get('dates')
    if dates:
        dates_found.extend(dates)

    date = event.get('queryStringParameters', {}).get('date')
    if date:
        dates_found.append(date)

    dates = event.get('queryStringParameters', {}).get('dates')
    if dates:
        dates_found.extend(dates)

    date = json.loads(event.get('body', "{}")).get('date')
    if date:
        dates_found.append(date)
    
    dates = json.loads(event.get('body', "{}")).get('dates')
    if dates:
        dates_found.extend(dates)

    dates_found = [
        datetime.strptime(date.strip(), '%Y-%m-%d') 
        if isinstance(date, str) else date 
        for date in dates_found
    ]

    return dates_found

def _list_all_possible_dates() -> List[datetime]:
    
    end_date = _get_brt_yesterday()
    start_date = datetime(2022, 6, 22).replace(tzinfo=ZoneInfo("America/Sao_Paulo"))

    date_list = []

    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    return date_list

def _get_brt_yesterday():
    now_BRT = datetime.now(ZoneInfo("America/Sao_Paulo"))
    return now_BRT - timedelta(days=1)

def _send_to_s3_landing(date_reference: datetime, filename: str, content: BytesIO) -> Tuple[bool, str]:
    s3_client = boto3.client('s3')
    
    # prefix as YYYY/MM/DD/
    prefix = date_reference.strftime('%Y/%m/%d/')
    filename = prefix + filename

    try:

        s3_client.put_object(
            Bucket='precos-pmc-landing',
            Key=filename,
            Body=content
        )
        return True, 'OK'
    
    except Exception as e:
        return False, f"Error found: {e}"