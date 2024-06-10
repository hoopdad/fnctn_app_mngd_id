import os
import requests
import json
from datetime import datetime
import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger1(myTimer: func.TimerRequest) -> None:
    # Azure Event Grid domain endpoint
    eventGridDomainEndpoint = "<Event_Grid_Domain_Endpoint>"

    # Event Grid topic to send the event to
    eventGridTopic = "<Event_Grid_Topic>"

    # Obtain an access token for the managed identity using the MSI_ENDPOINT and MSI_SECRET
    msi_endpoint = os.environ["MSI_ENDPOINT"]
    msi_secret = os.environ["MSI_SECRET"]
    resource = "https://eventgrid.azure.net/"
    api_version = "2017-09-01"
    token_url = f"{msi_endpoint}?resource={resource}&api-version={api_version}"
    response = requests.get(token_url, headers={"Secret": msi_secret})
    access_token = response.json().get("access_token")

    # Event data
    event_data = [{
        "id": "event-id",
        "eventType": "recordInserted",
        "subject": "myapp/vehicles/motorcycles",
        "eventTime": datetime.utcnow().isoformat(),
        "data": {
            "make": "Ducati",
            "model": "Panigale V4"
        },
        "dataVersion": "1.0"
    }]

    # Send the event to the Event Grid domain
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    event_url = f"{eventGridDomainEndpoint}/api/events?topic={eventGridTopic}"
    requests.post(event_url, json=event_data, headers=headers)

    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function executed.')

