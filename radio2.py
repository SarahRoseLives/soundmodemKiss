from soundmodemkiss import KISSClient

src_call = 'K8SDR-2'
dst_call = 'K8SDR-1'
client = KISSClient('localhost', 8101, src_call, dst_call)
client.send_message(src_call, dst_call, 'Hello, I have successfully sent a packet.')