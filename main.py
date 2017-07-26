# USB-Port
# ID Number: 
# July 8th 2017
# CSE 4340 Lab 1 Bluetooth Summer 2017



import bluetooth
from time import sleep
import random
import sys
import struct
import threading

# A list of global variables used
connectedServer = False
connectedClient = False
sock = None
client = None
nearby_devices = None
address = None
hostMacAddress = None

# If an exception is thrown that says, Port is already in use, then this number should be changed
# It can be changed from 1 to 12 or so. To prevent this problems, Disconnecting then quitting is recommended
port = 11


# This function comes from https://github.com/karulis/pybluez/commit/38634a16f8ecb2dbcac3e6cc4a12ec713d5f7b8b
def read_local_bdaddr():
  get_byte = str
  import bluetooth._bluetooth as _bt
  hci_sock = _bt.hci_open_dev(0)
  old_filter = hci_sock.getsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, 14)
  flt = _bt.hci_filter_new()
  opcode = _bt.cmd_opcode_pack(_bt.OGF_INFO_PARAM,
            _bt.OCF_READ_BD_ADDR)
  _bt.hci_filter_set_ptype(flt, _bt.HCI_EVENT_PKT)
  _bt.hci_filter_set_event(flt, _bt.EVT_CMD_COMPLETE);
  _bt.hci_filter_set_opcode(flt, opcode)
  hci_sock.setsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, flt )

  _bt.hci_send_cmd(hci_sock, _bt.OGF_INFO_PARAM, _bt.OCF_READ_BD_ADDR )

  pkt = hci_sock.recv(255)

  status,raw_bdaddr = struct.unpack("xxxxxxB6s", pkt)
  assert status == 0

  t = [ "%X" % ord(get_byte(b)) for b in raw_bdaddr ]
  t.reverse()
  bdaddr = ":".join(t)

  # restore old filter
  hci_sock.setsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, old_filter )
  return bdaddr

# This method will start a server and run it for 5 seconds
# If no clients connect to it, it will say exit
# if a client connects, then it will set a bool as true and acts as the server
def serverSide():
   global connectedServer
   global client
   global port

   if(connectedServer == False):
     backlog = 1
     s = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
     s.bind((read_local_bdaddr(), port))

     try:
       s.settimeout(5.0)
       s.listen(backlog)
       client, clientInfo = s.accept()
       connectedServer = True
       t = threading.Thread(target=getMessage)
       t.start()
       print("\nConnected as a Server\n")

     except bluetooth.BluetoothError as e:
       print("\nCount not find any client")
       s.close()

# This function will attempt to connect to the address that was set at the address
# If the device can not connect to it, it will exit.
def clientSide():
   global connectedClient
   global sock
   global address
   global port

   if(connectedClient == False):
    try:
      sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
      sock.connect((address, port))
      connectedClient = True
      t = threading.Thread(target=getMessage)
      t.start()
      print("\nConnected as a Client\n")
    except bluetooth.BluetoothError as e:
      sleep(1)
      print("Server may not be online. Try again")
      sock.close()

# This message runs as a seperate thread only
# this is used to monitor the incomming message while the main
# program takes care of sending message. This is used to make the program function
# as a live chat program. The way I wanted it to. This took a long time to get right.
def getMessage():
  global client
  global sock
  global connectedClient
  global connectedServer

  while (connectedClient == True or connectedServer == True):

    # If you're an client, then you recieve messages using Sock
    if(connectedClient == True):
      try:
        data = sock.recv(1024)
        if data:
          print(data)
      except:
        # If you attempt to send a message after the other device disconnected
        print("The connection on the other device was reset.")
        connectedClient = False
        break


    # If you're an Server, then you recieve messages using client
    elif(connectedServer == True):
      try:
        data = client.recv(1024)
        if data:
          print(data)
      except:
        # If you attempt to send a message after the other device disconnected
        print("The connection on the other device was reset.")
        connectedServer = False
        break

# This function is used to send messages to either the server on the client.
def sendMessage(text):
  global client
  global sock
  global connectedClient
  global connectedServer

  # If you're an client, then you send messages using Sock
  if(connectedClient == True):
    if(text != ""):
      sock.send(text)

  # If you're an Server, then you send messages using client
  if(connectedServer == True):
    if(text != ""):
      client.send(text)



# This message is used to scan for Bluetooth devices.
# This Scan will not display BLE devices, Only regular bluetooth.
def scanForDevices():
  global nearby_devices
  nearby_devices = bluetooth.discover_devices()

  count = 0
  for bdaddr in nearby_devices:
    # An crash can occur if a device is found without a name, this if-else fixes it
    if(bluetooth.lookup_name(bdaddr) is not None):
      print(str(count) + " <--- Device name: " + bluetooth.lookup_name(bdaddr) + "Address: " + bdaddr)
    else:
      print(str(count) + " <--- No Name listed: Address: " + bdaddr)

    count = count + 1


def main():
  global connectedServer
  global connectedClient
  global nearby_devices
  global address
  global client
  global sock

  print("Welcome to USB-Port's Bluetooth P2P chat program!\n")
  print("Type \"help\" to see a list of option.")
  print("type \"how\" to see how to connect and send a message\n")

  while True:
    cmd = raw_input()
    cmdList = cmd.split(" ")

    #This is the quit command, makes it safe to quit without breaking things
    if(cmd == "q"):
      if(connectedClient):
        sock.close()
      if(connectedServer):
        client.close()

      connectedClient = False
      connectedServer = False
      print("Bye!")
      break

    #This is the scan command, scans and and assigns the nearby devices list
    if(cmd == "scan"):
      print("Scanning... takes about 10 seconds")
      scanForDevices()

      if(nearby_devices):
        print("Type \"connect\" and the number next to the device to connect to it. I.E connect 0")
      else:
        print("No devices found, please check the visibility of the device")

    #This is the connect command, Devices must be found so that you can connect to them
    if(nearby_devices is not None):
      #You can only connect if you are not already connected, and the second arg for "connect" is a number listed in the scan display
      if(cmdList[0] == "connect" and connectedClient == False and connectedServer == False and (int(cmdList[1]) <= len(nearby_devices))):
        #checks to see if the arg for the device you want to connect to is in the list of nearby devices
        if(nearby_devices[int(cmdList[1])] in nearby_devices):
          #assign that MAC to the address
          address = nearby_devices[int(cmdList[1])]
          print("Will attempt to connect 10 times, perfrom the conection command on other device.")
          print("If both devices do not sync, try again")


          for count in range(0,10):

            if(connectedClient == False and connectedServer == False):
              randNum = random.randint(0,100)

              if(randNum <50):
                print("\nStarting Client...")
                clientSide()
              elif(randNum >= 50):
                print("\nStarting Server...")
                serverSide()
            else:
              print("\nYou may now type and send a message, from both devices.")
              break
        else:
          print("The device you requested connection is not found in the list of discovered devices. :(")

    if(connectedServer == True or connectedClient == True):

      sendMessage(cmd)


    if(cmd == "disconnect"):
      connectedClient = False
      connectedServer = False
      if(connectedClient):
        sock.close()
      if(connectedServer):
        client.close()
      print("Disconnected")

    # This displays the commands that can be typed
    if(cmd == "help"):
      print("The list of commands are as followed: ")
      print("\"scan\" <--- Performs a bluetooth scans for discoverable devices, takes 10 seconds to complete.")
      print("\"connect [int]\" <--- Connects to a device shown in the scan. Must perform scan first to see availble devices. I.E connect 0")
      print("\"disconect\" <--- Disconnects from the current connected device.")
      print("\"how\" <--- Display a quick start step guide.")
      print("\"q\" <--- Quits the application.")

    #This is a quick start guide
    if(cmd == "how"):
      print("1) Start by typing \"scan\" to discover a list of nerby BT devices.")
      print("2) A list of populated BT devices will be displayed. On the left you will see a number next to each one.")
      print("3) Type \"connect\" followed by the number of which device you wish to connect to. I.E \"connect 0\"")
      print("4) The other user should also do steps 1-3 and attempt to connect to this device.")
      print("5) A random sync will take part. If the deivces happen not to sync, repeat step 3")
      print("6) A confirmation message will appear if successful, then you will be free to send BT message to each device")


connectedClient = False
connectedServer = False
if __name__ == "__main__":
  main()



