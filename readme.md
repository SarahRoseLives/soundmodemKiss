# SoundmodemKiss

## Introduction
This application connects via KISS TCP connection to UZ7HO's soundmodem software to faciliate the sending and reciving of messages.

## Features
- **Connectivity:** Connect to a KISS server over a specified host and port.
- **Message Sending:** Send AX.25 formatted messages to other stations.
- **Message Receiving:** Receive AX.25 formatted messages from other stations.
- **Callback Support:** Register callback functions to handle received messages.
- **Error Handling:** Handle various errors gracefully, such as socket errors or invalid hostnames/IP addresses.

## Usage
1. Instantiate the `KISSClient` class with the required parameters: host, port, source call, and destination call.
2. Optionally, set a message callback function using `set_message_callback(callback)`.
3. Send a message using `send_message(src_call, dst_call, message)`.
4. Optionally, handle received messages in the callback function provided.

Example Usage:
```python
from soundmodemkiss import KISSClient

src_call = 'K8SDR-1'
dst_call = 'K8SDR-2'
client = KISSClient('localhost', 8100, src_call, dst_call)

def message_callback(message):
    print(f"Received message: {message}")

client.set_message_callback(message_callback)
client.send_message(src_call, dst_call, 'Hello, I have successfully sent a packet.')
