import socket
import threading
import time


class KISSClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.receive_thread = None

    def connect(self):
        """Connect to the KISS server."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        print(f"Connected to KISS server at {self.host}:{self.port}")

    def send_command(self, command):
        """Send a command to the KISS server."""
        self.sock.sendall(command)
        self.decode_ax25_packet(command, "Sent")

    def read_response(self, buffer_size=1024):
        """Read a response from the KISS server."""
        while self.running:
            try:
                response = self.sock.recv(buffer_size)
                if response:
                    self.decode_ax25_packet(response, "Received")
                else:
                    print("Connection closed by server.")
                    break
            except Exception as e:
                print(f"An error occurred while receiving: {e}")
                break

    def start_receiving(self):
        """Start the thread to continuously read responses."""
        self.running = True
        self.receive_thread = threading.Thread(target=self.read_response)
        self.receive_thread.start()

    def stop_receiving(self):
        """Stop the thread that reads responses."""
        self.running = False
        if self.receive_thread:
            self.receive_thread.join()

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

    def decode_ax25_packet(self, packet, packet_type):
        """Decode the AX.25 packet."""
        # Remove KISS framing bytes (start and end with 0xC0)
        if packet.startswith(b'\xC0') and packet.endswith(b'\xC0'):
            packet = packet[1:-1]

        # KISS command byte (skip it)
        packet = packet[1:]

        def decode_callsign(encoded):
            callsign = ''.join(chr(b >> 1) for b in encoded[:6]).strip()
            ssid = (encoded[6] >> 1) & 0x0F
            return f"{callsign}-{ssid}" if ssid else callsign

        dst_call = decode_callsign(packet[:7])
        src_call = decode_callsign(packet[7:14])
        control = packet[14]
        pid = packet[15]
        message = packet[16:].decode('ascii')

        print(f"{packet_type}: From: {src_call} To: {dst_call} Message: {message}")

    def close(self):
        """Close the connection to the KISS server."""
        self.stop_receiving()
        if self.sock:
            self.sock.close()
            print("Connection closed")

    def send_message(self, src_call, dst_call, message):
        try:
            self.connect()
            self.start_receiving()
            message_command = self.create_kiss_frame(src_call, dst_call, message)
            self.send_command(message_command)

            # Keep the connection open to receive messages
            while True:
                try:
                    time.sleep(1)  # Keep the main thread alive
                except KeyboardInterrupt:
                    print("Interrupted by user.")
                    break

        except socket.gaierror as e:
            print(f"An error occurred: {e} (hostname or IP address is invalid)")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.close()


if __name__ == "__main__":
    client = KISSClient('localhost', 8100)
    client.send_message('NOCALL-0', 'CQ-0', 'Hello, I have successfully sent a packet.')
