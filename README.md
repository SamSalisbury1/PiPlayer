## Writing to NFC

Warning: DO NOT write the blocks of 4N+3 (3, 7, 11, ..., 63)
or else you will change the password for blocks 4N ~ 4N+2.

Note: 
1.  The first 6 bytes (KEY A) of the 4N+3 blocks are always shown as 0x00,
since 'KEY A' is unreadable. In contrast, the last 6 bytes (KEY B) of the 
4N+3 blocks are readable.
2.  Block 0 is unwritable. 


## Acknowledgments

This project uses the PN532 NFC Hat library https://github.com/soonuse/pn532-nfc-hat by https://github.com/soonuse, which is licensed under MIT License. Thank you to the soonuse for creating and maintaining this library.