import socket
import time


class KISSClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        """Connect to the KISS server."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        print(f"Connected to KISS server at {self.host}:{self.port}")

    def send_command(self, command):
        """Send a command to the KISS server."""
        print(f"Sending command: {command}")
        self.sock.sendall(command)

    def read_response(self, buffer_size=1024):
        """Read a response from the KISS server."""
        response = self.sock.recv(buffer_size)
        print(f"Received response: {response}")
        return response

    def encode_callsign(self, callsign, ssid, last):
        """Encode a callsign in the AX.25 format."""
        callsign = callsign.upper().ljust(6)  # Pad to 6 characters and ensure uppercase
        encoded = bytearray()
        for char in callsign:
            encoded.append((ord(char) << 1) & 0xFE)  # Shift left by 1 bit and mask to keep only 7 bits

        ssid &= 0x0F  # Ensure SSID is within 0-15
        ssid_field = ssid << 1  # SSID left-shifted by 1
        if last:
            ssid_field |= 0x01  # Set the last address bit
        encoded.append(ssid_field)
        return bytes(encoded)  # Convert bytearray to bytes

    def create_kiss_frame(self, src_call, dst_call, data):
        """Create a KISS frame with AX.25 headers."""
        dst_parts = dst_call.split('-')
        src_parts = src_call.split('-')

        if len(dst_parts) == 1:
            dst_encoded = self.encode_callsign(dst_parts[0], 0, last=False)
        else:
            dst_encoded = self.encode_callsign(dst_parts[0], int(dst_parts[1]), last=False)

        if len(src_parts) == 1:
            src_encoded = self.encode_callsign(src_parts[0], 0, last=True)
        else:
            src_encoded = self.encode_callsign(src_parts[0], int(src_parts[1]), last=True)

        # Control and protocol identifiers for AX.25 UI frame
        control = b'\x03'  # Unnumbered Information (UI) frame
        pid = b'\xF0'  # No layer 3 protocol

        # AX.25 payload
        ax25_payload = dst_encoded + src_encoded + control + pid + data.encode('ascii')

        # KISS frame
        frame = b'\xC0' + b'\x00' + ax25_payload + b'\xC0'  # Add starting and ending FEND (frame end)
        return frame

    def close(self):
        """Close the connection to the KISS server."""
        if self.sock:
            self.sock.close()
            print("Connection closed")

    def send_message(self, src_call, dst_call, message):
        try:
            self.connect()
            message_command = self.create_kiss_frame(src_call, dst_call, message)
            self.send_command(message_command)

            # Allow time for the response
            time.sleep(1)
            response = self.read_response()
            print(f"Server response: {response}")

        except socket.gaierror as e:
            print(f"An error occurred: {e} (hostname or IP address is invalid)")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.close()


if __name__ == "__main__":
    client = KISSClient('localhost', 8100)
    client.send_message('NOCALL', 'CQ', 'Hello, I have successfully sent a packet.')
