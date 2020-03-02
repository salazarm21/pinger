#imports for code
import os 
import argparse 
import socket
import struct
import select
import time

#use terminal to run code!!! use sudo!!!

"""sets echo request to 8"""
#echo requests = 8 to identify if the packet is echo 8 or echo reply 0
ICMP_ECHO_REQUEST = 8 #Fill in the type of ECHO request here # (Platform specific)
#how long to wait till timeout
DEFAULT_TIMEOUT = 2
#counter
DEFAULT_COUNT = 4 


class Pinger(object):
    """ pings to host """
    #sets targethost, count, and timeout to their given values
    def __init__(self, target_host, count=DEFAULT_COUNT, timeout=DEFAULT_TIMEOUT):
        self.target_host = target_host
        self.count = count
        self.timeout = timeout


    def do_checksum(self, source_string):
        """  Verify the packet integritity by calculating the checksum just like we did in class """
        #sets sum to 0
        sum = 0

        #modulo math: why we divide by 2 then multiply by 2
        max_count = (len(source_string)/2)*2
        #set count to 0
        count = 0
        while count < max_count:

            # To make this program run with Python 2.7.x:            
            # val = ord(source_string[count + 1])*256 + ord(source_string[count])             
            # ### uncomment the above line, and comment out the below line.
            #changes the value of val 
            val = source_string[count + 1]*256 + source_string[count]            
            # In Python 3, indexing a bytes object returns an integer.
            # Hence, ord() is redundant.            

            #adding the sum and val together
            sum = sum + val
            sum = sum & 0xffffffff
            #adding two to count
            count = count + 2
     #loop to determine if the max count is less than the length of the source string and if it is then
    #change the value of sum to be sum plus the source string lenght -1 and then returns an answer
        if max_count<len(source_string):
            sum = sum + ord(source_string[len(source_string) - 1])
            sum = sum & 0xffffffff 
     #adds back carry outs from top 16 bits to lower 16 bits
        sum = (sum >> 16)  +  (sum & 0xffff)
        sum = sum + (sum >> 16)
        #one's compliment
        answer = ~sum
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer
 
    def receive_pong(self, sock, ID, timeout):
        """
        We have to create a socket on our side so we can receive the replies from the destination host.
        We also have to make sure not to wait too long “TIMEOUT”.

        recieves ping from socket
        """

        #sets time remaining to timeout
        time_remaining = timeout

        #sets start_time, readable, and time_spent
        while True:
            start_time = time.time()
            readable = select.select([sock], [], [], time_remaining)
            time_spent = (time.time() - start_time)
            #sets readable to empty
            if readable[0] == []: #Fill in [#Fill in] == []: #Timeout occurs if readable is 0, hopefully remember what time out is now 
                return
     
            time_received = time.time()
            recv_packet, addr = sock.recvfrom(1024)
            icmp_header = recv_packet[20:28]
            #header layout, dummy data
            #interprets string as binary data
            type, code, checksum, packet_ID, sequence = struct.unpack(
                "bbHHh", icmp_header
            )
            if packet_ID == ID:
                bytes_In_double = struct.calcsize("d")
                #binary data 
                time_sent = struct.unpack("d", recv_packet[28:28 + bytes_In_double])[0]
                return time_received - time_sent
     
            time_remaining = time_remaining - time_spent
            if time_remaining <= 0:
                return
     
     
    def send_ping(self, sock,  ID):
        """
        We have to create a packet and send it to the destination host,
        we are creating a dummy ICMP packet and attaching it to the IP header. 
        
        sends ping to target host
        """
        target_addr  =  socket.gethostbyname(self.target_host)
         #once checksum has been computed, set it to 0
        my_checksum = 0 #Fill in
     
        # Create a dummy header with a 0 checksum.
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
        bytes_In_double = struct.calcsize("d")
        data = (192 - bytes_In_double) * "Q"
        data = struct.pack("d", time.time()) + bytes(data.encode('utf-8'))
     
        # Get the checksum on the data and the dummy header.
        my_checksum = self.do_checksum(header + data)
        #makes new header 
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1)
        
        #add the data from above to the header to create a complete packet
        packet = header + data #Fill in
        #send the packet to the target address
        sock.sendto(packet, (target_addr, 1))
     
     
    def ping_once(self):
        """
        Returns the delay (in seconds) or none on timeout.
        """
        icmp = socket.getprotobyname("icmp")
        try:
        #add the ipv4 socket (same as we did in our first project, SOCK_RAW(to bypass some of the TCP/IP handling by your OS) and the ICMP packet
            #raw socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        except socket.error as e:
            if e.errno == 1:
                # print a messege if not run by superuser/admin, so operation is not permitted
                e.msg +=  "messages can only be sent from root user" #Fill in before
                raise socket.error(e.msg)
        except Exception as e:
            #print the errror messege    
            print ("Exception: %s" %(e))
            
        my_ID = os.getpid() & 0xFFFF
        
        #Call the definition from send.ping above and send to the socket you created above
        self.send_ping(sock , my_ID)
        #sets delay
        delay = self.receive_pong(sock, my_ID, self.timeout)
        #closes the socket
        sock.close()
        return delay
     
     
    def ping(self):
        """
        Run the ping process
        """

        #tries to ping to the target host
        #if it can ping it pings and outputs its ping delay 
        #if it can not ping then it will output ping failed and/or with its timeout
        for i in range(self.count):
            print ("Ping to %s..." % self.target_host,)
            try:
                delay  =  self.ping_once()
            except socket.gaierror as e:
                #if ping failed with a socket error
                print ("Ping failed. (socket error: '%s')" % e[1])
                break
     
            if delay  ==  None:
                #if ping failed because of timeout
                print ("Ping failed. (timeout within %ssec.)" % self.timeout)
            else:
                delay  =  delay * 1000
                #got ping with the delay time
                print ("Get pong in %0.4fms" % delay)

 
#sets the name and targethost for ping
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Python ping')
    parser.add_argument('--target-host', action="store", dest="target_host", required=True)
    given_args = parser.parse_args()  
    target_host = given_args.target_host
    #sets pinger for target host 
    pinger = Pinger(target_host=target_host)
    pinger.ping()
