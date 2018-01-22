# chatlogger-for-mumo

The Chatlogger for Mumo

## !history [n = 10 [\w+]] 
Will print the last n lines that were written in your channel, if no other defined.
##### Examples
```bash
!history
``` 
<i>Prints the last 10 chat messages.</i>

```bash
!history 25
``` 
Prints the last 25 chat messages.<br>
```bash
!history 50 Lounge
```
Prints the last 50 chat messages from the channel Lounge.

## !offtopic \w+
##### Example
```bash
!offtopic Text that should not appear in the History
```
All following text will not be included in the log.
