CC = gcc
CFLAGS = -g -Wall

default: lpr-peek lpr-server

lpr-server:

lpr-peek:

.PHONY: clean
clean:
	rm -f lpr-peek lpr-server *.o

.PHONY: test
test: lpr-peek
	nc -l 4377 | ./lpr-peek
