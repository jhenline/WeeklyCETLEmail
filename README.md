# CETL Weekly Email Generator

This Python script generates and sends the CETL (Center for Effective Teaching and Learning) weekly email, which is distributed every Monday morning at 6:00 AM. The script uses the Eventbrite API to retrieve the events for the upcoming week and SendGrid for email delivery.

## Authors

### Henry Acevedo
Henry Acevedo is the original author of this script. His work laid the foundation for automating the CETL weekly email process, integrating with the Eventbrite API, and ensuring that the script could reliably fetch and format event information. 


## Features

- **Eventbrite Integration**: Automatically fetches events from Eventbrite.
- **SendGrid Integration**: Sends out a customized email with event details to a specified list of recipients.
- **Dynamic Email Content**: Constructs the email body with event details, including date, time, location, and registration link.
- **Configurable**: Uses a `config.ini` file for storing API keys and other configuration details.

## Requirements

- Python 3.x
- `eventbrite` library
- `sendgrid` library
- `requests` library

## Installation

1. Clone this repository to your local machine.
2. Install the required Python packages:

   ```bash
   pip install eventbrite sendgrid requests
