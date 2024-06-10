import os
import requests
import json
from datetime import datetime
import azure.functions as func
import logging

# Azure Event Grid domain endpoint
eventGridDomainEndpoint = "<Event_Grid_Domain_Endpoint>"
# Event Grid topic to send the event to
eventGridTopic = "<Event_Grid_Topic>"
# Storage account from which to read the event
storageAccountEndpoint = "https://<your-storage-account-name>.queue.core.windows.net"
# Storage queue where events are stored
queue_name = "<your-queue-name>"

def getToken () -> string:
    msi_endpoint = os.environ["MSI_ENDPOINT"]
    msi_secret = os.environ["MSI_SECRET"]
    resource = "https://eventgrid.azure.net/"
    api_version = "2017-09-01"
    token_url = f"{msi_endpoint}?resource={resource}&api-version={api_version}"
    response = requests.get(token_url, headers={"Secret": msi_secret})
    return response.json().get("access_token")



app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger1(myTimer: func.TimerRequest) -> None:

    # Obtain an access token for the managed identity using the MSI_ENDPOINT and MSI_SECRET
    access_token = getToken()

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

@app.timer_trigger2(schedule="0 */5 * * * *", arg_name="myTimer2", run_on_startup=False,
              use_monitor=False) 
def timer_trigger2(myTimer: func.TimerRequest) -> None:
   # Initialize the DefaultAzureCredential
    credential = DefaultAzureCredential()
    access_token = getToken()

    # Initialize the Queue Service Client using the managed identity
    queue_service_client = QueueServiceClient(account_url=storageAccountEndpoint, credential=credential)
    queue_client = queue_service_client.get_queue_client(queue_name)

    # Receive messages from the queue
    while True:
        messages = queue_client.receive_messages(max_messages=32)
        if not messages:
            break
        for message in messages:
            decoded_message = message.content.decode("utf-8")
            print(decoded_message)
