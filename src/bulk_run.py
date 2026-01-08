import logging
from dotenv import load_dotenv

from lambda_function import lambda_handler

"""

    This code runs a bulk execution of the lambda_handler function,
    for all possible dates.

    Expect either for AWS credentials on .env or AWS login already configured.

"""

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

def test_lambda_handler():
    event = {
        "dates": ["2024-06-05"]
    }
    context = {}
    response = lambda_handler(event, context)
    print(response)

    #assert response["statusCode"] == 200, response.get("body", "")

if __name__ == "__main__":
    
    # Grant everything is working as expected
    test_lambda_handler()

    payload = {
        "reprocess_all_dates": True
    }

    lambda_handler(
        event=payload,
        context={}
    )
