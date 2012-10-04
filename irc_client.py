#!/usr/bin/python

#
# Network Computing
# Project Assignment:
# IRC Client Implementation
# Author: Michael Johnston, B00522814
#

import argparse
import socket
import threading
from Queue import Queue

def main():
  def send_credentials(password, nickname, username, realname):
    """ Send user credentials to the server and sets mode """
    if password:
      send_irc('PASS {0}'.format(password))
    send_irc('NICK {0}'.format(nickname))
    send_irc('USER {0} {1} {2} :{3}'.format(username, '0', '*', realname))

  def send_irc(data):
    """ Sends data to the IRC server """
    irc_socket.send(data + '\n')

  def join_irc_channel(channel, password=None):
    """ Sends command to join server channel """
    if password:
      send_irc("JOIN {0} {1}".format(channel, password))
    else:
      send_irc("JOIN {0}".format(channel))

  # command line argument parsing
  parser = argparse.ArgumentParser(description='Connect to a IRC server/channel.')
  parser.add_argument('-pass', action='store', dest='password', type=str, required=False, help='client password for registered nickname')
  parser.add_argument('-nick', action='store', dest='nickname', type=str, required=True, help='client nickname')
  parser.add_argument('-user', action='store', dest='user_name', type=str, required=True, help='client username')
  parser.add_argument('-realname', nargs='+', action='store', dest='realname', type=str, required=True, help='real name of user')
  parser.add_argument('-server', action='store', dest='server_name', type=str, required=True, help='server to connect to')
  parser.add_argument('-channel', action='store', dest='channel_name', type=str, required=False, help='channel to connect to (surround in quotes to use #; interpreted as comment otherwise)')
  parser.add_argument('-channelpass', action='store', dest='channel_password', type=str, required=False, help='password for the channel')

  args = parser.parse_args()

  # read in values from arguments
  password = None
  if args.password:
    password = args.password
  nickname = args.nickname
  username = args.user_name
  realname = ' '.join(args.realname)
  server = args.server_name

  # checks if optional arguments are passed and correct
  channel_name = None
  channel_password = None
  if args.channel_name:
    channel_name = args.channel_name
    if channel_name[0] not in ['#', '!', '&', '+'] or ' ' in channel_name or ',' in channel_name:
      parser.error("argument -channel must start with a '!', '#', '&', or '#' and not contain any spaces or commas")
    elif channel_name[0] == '&' and not args.channel_password:
      parser.error("channel name starting with '&' requires -channelpass")
    elif channel_name[0] == '&' and args.channel_password:
      channel_password = args.channel_password

  # create irc socket
  irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  # connect to irc server
  irc_socket.connect((server, 6667))

  #accept and print incoming messages
  stop_queue = Queue()
  listen_thread = IncomingMessages(irc_socket, stop_queue)
  listen_thread.start()

  #send credentials to server
  send_credentials(password, nickname, username, realname)

  #join channel
  if channel_name:
    join_irc_channel(channel_name, channel_password)

  # allow user to send input, stops on 'QUIT' input (also stops listening thread)
  while 1:
    user_input = raw_input()
    if 'QUIT' in user_input:
      stop_queue.put('END')
      send_irc(user_input)
      irc_socket.close()
      listen_thread.join()
      break
    send_irc(user_input)


class IncomingMessages(threading.Thread):
  """ Thread to listen for (and possibly respond to) incoming messages """
  def __init__(self, irc_socket, stop_queue):
    self.irc_socket = irc_socket
    self.stop_queue = stop_queue
    threading.Thread.__init__(self)

  def run(self):
    """ Receive and print incoming messages and respond to PING """
    while self.stop_queue.empty():
      incoming_message = self.irc_socket.recv(1024)
      message_contents = incoming_message.split()
      if message_contents[0] == 'PING': # if server pings;
        self.irc_socket.send('PONG {0}'.format(message_contents[1]) + '\n') # respond with pong + message
      else:
        print incoming_message,


if __name__ == '__main__':
  main()
