import socket
import time
import json
import gc
import ubinascii
import uos


class HTTPD:
    def __init__(self, port=80):
        gc.enable()
        # enable debug print statements
        self.debug = True
        self.debug_level = 'relaxed'  # verbose and relaxed

        # initiate listening socket server
        addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
        self.s = socket.socket()
        self.s.bind(addr)
        self.s.listen(5)
        self.s.settimeout(None)
        if(self.debug and (self.debug_level == 'relaxed' or self.debug_level == 'verbose')):
            print('listening on', addr)

    def changeHTML(self, new_html):
        f = open(new_html, "r")
        self.html = str(f.read())
        f.close()

    def socketListener(self):
        gc.collect()
        cl, addr = self.s.accept()
        if(self.debug and (self.debug_level == 'relaxed' or self.debug_level == 'verbose')):
            print('client connected from', addr)
        cl_file = cl.makefile('rwb', 1)
        client_ask = open('client_response.txt', 'w')
        while True:
            line = cl_file.readline()
            client_ask.write(line)
            if not line or line == b'\r\n':
                break
        client_ask.close()
        client_dict = self.getClientAsk()
        self.getRoute(cl, client_dict)
        cl.close()
        if(self.debug and self.debug_level == 'verbose'):
            print("JSON Dict: %s" % client_dict)

    def getRoute(self, client, client_dict):
        gc.collect()
        url = str(client_dict["Method"])
        method_type = url.split('/')[0][:-1]
        uri_nolower = self.special_char_digest(
            url.split('/')[1].replace(' HTTP', ''))
        uri = uri_nolower.lower()
        if(self.debug and self.debug_level == 'relaxed'):
            print("URI: %s" % uri)
        elif(self.debug and self.debug_level == 'verbose'):
            print("URL: %s" % url)
            print("URI: %s" % uri)
            print("JSON Dict: %s" % client_dict)

        # Set captive portal condition
        captive_portal = False

        Maximum_segment_size = 536
        try:
            if(not captive_portal or '.' in uri):
                # set uri handling
                if(uri == 'favicon.ico'):
                    f = open('www/favicon.ico', 'rb')
                elif(uri == ''):
                    f = open('www/index.html', 'rb')
                else:
                    f = open('www/error.html', 'rb')
            else:
                # Captive Portal Handling
                f = open('www/index.html', 'rb')

            if(method_type == 'GET'):
                response = f.read(Maximum_segment_size)
                if('%s' in response):
                    response = response % ('Test')
                while (len(response) > 0):
                    client.send(response)
                    response = f.read(Maximum_segment_size)
                f.close()
            elif(method_type == 'POST'):
                receive = client.read(Maximum_segment_size)
                while (len(receive) > 0):
                    f.write(receive)
                    receive = client.read(Maximum_segment_size)
                f.close()
                client.sendall(
                    "<!DOCTYPE html><html><body><h1>Received Message</h1><p>Message Received</p></body></html>")
        except Exception as e:
            print(e)
            client.sendall(
                "<!DOCTYPE html><html><body><h1>Server Error</h1><p>Server Error.</p></body></html>")

    def getClientAsk(self):
        f = open('client_response.txt', 'r', encoding='utf-16')
        temp = f.read()
        f.close()
        if(self.debug and self.debug_level == 'verbose'):
            print("Client Ask: %s" % temp)
        try:
            temp = temp.replace('\r\n\r\n', '').replace(
                '\r\n', '\", \"').replace(': ', '\": \"')
            client_dict = json.loads("{ \"Method\": \"" + temp + "\" }")
            return client_dict
        except Exception as e:
            print(e)

    def special_char_digest(self, string):
        # test if string has special char
        special_char_start = string.find('%')

        # replace all special chars with their corresponding char
        while(special_char_start != -1):
            special_char = string[special_char_start:special_char_start + 3]
            string = string.replace(special_char, ubinascii.unhexlify(
                special_char.replace('%', '')).decode())
            special_char_start = string.find('%')

        return string
