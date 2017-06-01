# minIRC_Server
#### Mike Lane
#### CS594 - Internetworking Protocols

---

### Introduction

This is a server that implements a custom IRC-like protocol called minIRC.

### Installation

You must have Python 3.6.0 or above to run the minIRC_Server. The minIRC_Server does not require any libraries outside 
of the standard Python 3.6.0 libraries. It is recommended to use `pyenv` and `pyenv-virtualenv` to install and run the
appropriate version of Python. You will need to create a file called `setings.ini`. Follow the formatting of 
`example_settings.ini`.

### Execution

Once the host and port are set properly in the `settings.ini` file, the minIRC_Server test can be started from the 
command line by using a simple command:

    $ python3 server_test.py
    
This will make the server start listening for connections.

The server will log debug output to the screen as well as to the file at `logs/server.log`. 