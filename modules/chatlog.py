#!/usr/bin/env python
# -*- coding: utf-8
#
# Copyright (C) 2013 Stephan Brandt <stephan@contagt.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:

# - Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# - Neither the name of the Mumble Developers nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# `AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE FOUNDATION OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#
# chatlog.py
# Stores the written public Messages of a defined Channel to a Chat Protocol
#

from mumo_module import (commaSeperatedIntegers,
                         MumoModule)
import re
import time
import os
from datetime import datetime
from dateutil import tz


class chatlog(MumoModule):
    default_config = {'chatlog': (
        ('servers', commaSeperatedIntegers, []),
        ('history_command', str, '!history'),
        ('offtopic_command', str, '!offtopic'),
        ('history_directory', str, 'logs'),
    )
    }
    utc = tz.tzutc()
    local = tz.tzlocal()


    def __init__(self, name, manager, configuration=None):
        MumoModule.__init__(self, name, manager, configuration)
        self.murmur = manager.getMurmurModule()
        self.history_command = self.cfg().chatlog.history_command
        self.offtopic_command = self.cfg().chatlog.offtopic_command
        self.history_directory = self.cfg().chatlog.history_directory
        self.logs_directory = self.history_directory + "/"
        if not os.path.exists(self.logs_directory):
            os.makedirs(self.logs_directory)

    def connected(self):
        manager = self.manager()
        log = self.log()
        log.debug("Server will now Log the Public Chat!")

        servers = self.cfg().chatlog.servers
        if not servers:
            servers = manager.SERVERS_ALL

        manager.subscribeServerCallbacks(self, servers)

    def disconnected(self):
        pass

    # --- Server callback functions
    #

    def getChannelName(self, server, message):
        originchannel = message.channels[0]
        return server.getChannelState(originchannel).name

    def userTextMessage(self, server, user, message, current=None):
        if message.text.startswith(self.history_command):
            cnt = 10;
            channelname = None
            m = re.search('\\' + self.history_command + '\s(\d+)(\s(.+))?', message.text)
            if m is not None:
                cnt = int(m.group(1))
                if m.group(3) is not None:
                    channelname = m.group(3)
            if channelname is None:
                channelname = self.getChannelName(server, message)
            with open(self.logs_directory + channelname + '.log', 'r') as logfile:
                content = logfile.readlines()[(-1) * cnt:]
                for line in content:
                    server.sendMessage(user.session, line)
                logfile.close()

        elif not message.text.startswith(self.offtopic_command):
            channelname = self.getChannelName(server, message)
            with open(self.logs_directory + channelname + '.log', 'a') as logfile:
                logfile.write('[')
                ts = time.time()
                utc_time = datetime.fromtimestamp(ts)
                logfile.write(utc_time.strftime('%Y-%m-%d %H:%M:%S'))
                logfile.write(']')
                logfile.write(user.name)
                logfile.write(' : ')
                logfile.write(message.text)
                logfile.write('\n')

    def local_to_utc(self, local_dt):
        local_obj = datetime.strptime(local_dt, '%Y-%m-%d %H:%M:%S')
        return local_obj.astimezone(self.utc)

    def userConnected(self, server, state, context=None):
        server.sendMessage(state.session,
                           "Please note that all Chats are beeing logged. Use !offtopic to prevent logging.")
        tuname = state.name
        for cuid, cuname in server.getRegisteredUsers(tuname).iteritems():
            if cuname == tuname:
                ureg = server.getRegistration(cuid)
                if ureg:
                    time_local = ureg[self.murmur.UserInfo.UserLastActive]
                    lines = []
                    channel = server.getChannelState(state.channel).name
                    for line in reversed(open(self.logs_directory + channel + ".log").readlines()):
                        m = re.search('\[(.+)\].+', line)
                        if m is not None:
                            ddate = self.local_to_utc(m.group(1))
                            udate = self.local_to_utc(time_local)
                            if ddate <= udate:
                                break
                            else:
                                lines.append(line)

                    for item in reversed(lines):
                        server.sendMessage(state.session, item)
                    server.sendMessage(state.session, "====== Now ======")

    def userDisconnected(self, server, state, context=None):
        pass

    def userStateChanged(self, server, state, context=None):
        pass

    def channelCreated(self, server, state, context=None):
        pass

    def channelRemoved(self, server, state, context=None):
        pass

    def channelStateChanged(self, server, state, context=None):
        pass

