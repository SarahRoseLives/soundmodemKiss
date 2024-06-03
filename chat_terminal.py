from soundmodemkiss import KISSClient
import threading
import time
import tkinter as tk
from tkinter import scrolledtext


class ChatApp:
    def __init__(self, master):
        self.master = master
        self.master.title("KISS Chat")

        # Configuration frame
        self.config_frame = tk.Frame(self.master)
        self.config_frame.pack(padx=10, pady=10, fill=tk.X)

        tk.Label(self.config_frame, text="Your Callsign:").grid(row=0, column=0, sticky=tk.E)
        tk.Label(self.config_frame, text="To Callsign:").grid(row=1, column=0, sticky=tk.E)
        tk.Label(self.config_frame, text="Modem IP:").grid(row=2, column=0, sticky=tk.E)
        tk.Label(self.config_frame, text="Port:").grid(row=3, column=0, sticky=tk.E)

        self.src_call_entry = tk.Entry(self.config_frame)
        self.dst_call_entry = tk.Entry(self.config_frame)
        self.ip_entry = tk.Entry(self.config_frame)
        self.port_entry = tk.Entry(self.config_frame)

        self.src_call_entry.grid(row=0, column=1)
        self.dst_call_entry.grid(row=1, column=1)
        self.ip_entry.grid(row=2, column=1)
        self.port_entry.grid(row=3, column=1)

        self.src_call_entry.insert(0, 'NOCALL')
        self.dst_call_entry.insert(0, 'CQ')
        self.ip_entry.insert(0, 'localhost')
        self.port_entry.insert(0, '8100')

        self.connect_button = tk.Button(self.config_frame, text="Connect", command=self.connect)
        self.connect_button.grid(row=4, columnspan=2, pady=10)

        # Chat frame
        self.chat_frame = tk.Frame(self.master)
        self.chat_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, state='disabled', wrap='word')
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.message_entry = tk.Entry(self.chat_frame)
        self.message_entry.pack(padx=10, pady=10, fill=tk.X, expand=False)
        self.message_entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self.chat_frame, text="Send", command=self.send_message)
        self.send_button.pack(padx=10, pady=10)

        self.client = None

    def connect(self):
        src_call = self.src_call_entry.get()
        dst_call = self.dst_call_entry.get()
        modem_ip = self.ip_entry.get()
        port = int(self.port_entry.get())

        self.client = KISSClient(modem_ip, port, src_call, dst_call)
        self.client.set_message_callback(self.message_callback)
        try:
            self.client.connect()
            self.client.start_receiving()
            self.chat_display.configure(state='normal')
            self.chat_display.insert(tk.END, f"Connected to {modem_ip}:{port} as {src_call}\n")
            self.chat_display.configure(state='disabled')
        except Exception as e:
            self.chat_display.configure(state='normal')
            self.chat_display.insert(tk.END, f"Failed to connect: {e}\n")
            self.chat_display.configure(state='disabled')

    def message_callback(self, message):
        if "ACK" not in message:
            ack_command = self.client.create_kiss_frame(self.client.src_call, self.client.dst_call, 'ACK')
            self.client.send_command(ack_command)
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, f"Received: {message}\n")
        self.chat_display.configure(state='disabled')

    def send_message(self, event=None):
        if self.client:
            message = self.message_entry.get()
            if message:
                self.send_message_with_retries(self.client, self.client.src_call, self.client.dst_call, message)
                self.message_entry.delete(0, tk.END)

    def send_message_with_retries(self, client, src_call, dst_call, message, max_attempts=3):
        attempts = 0
        while attempts < max_attempts:
            client.ack_received.clear()
            message_command = client.create_kiss_frame(src_call, dst_call, message)
            client.send_command(message_command)
            self.chat_display.configure(state='normal')
            self.chat_display.insert(tk.END, f'Sent: {message}\n')
            self.chat_display.configure(state='disabled')

            if client.ack_received.wait(timeout=5):  # Wait for ACK with a timeout of 5 seconds
                self.chat_display.configure(state='normal')
                self.chat_display.insert(tk.END, "ACK received, message sent successfully.\n")
                self.chat_display.configure(state='disabled')
                break  # Exit loop if ACK is received
            else:
                attempts += 1
                self.chat_display.configure(state='normal')
                self.chat_display.insert(tk.END, f"No ACK received, retrying ({attempts}/{max_attempts})\n")
                self.chat_display.configure(state='disabled')

        if attempts == max_attempts:
            self.chat_display.configure(state='normal')
            self.chat_display.insert(tk.END, "Failed to send message after 3 attempts.\n")
            self.chat_display.configure(state='disabled')

    def close(self):
        if self.client:
            self.client.close()
        if hasattr(self, 'receive_thread') and self.receive_thread:
            self.receive_thread.join()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)

    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()
