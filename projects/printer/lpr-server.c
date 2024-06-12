#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>

static void die(const char *s) { perror(s); exit(1); }

int main(int argc, char **argv){
    
    if(argc != 2){
        fprintf(stderr, "usage: %s <server-port>\n", argv[0]);
        exit(1);
    }

    unsigned short port = atoi(argv[1]);

    //START BOILERPLATE
    int servsock;
    if ((servsock = socket (AF_INET, SOCK_STREAM, 0)) < 0){
        die("socket failed");
    }
    struct sockaddr_in servaddr;
    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
    servaddr.sin_port = htons(port);

    if (bind(servsock, (struct sockaddr *) &servaddr, sizeof(servaddr)) < 0)
        die("bind failed");

    if (listen(servsock, 5 /* queue size for connection requests */ ) < 0)
        die("listen failed");
    
    int clntsock;
    socklen_t clntlen;
    struct sockaddr_in clntaddr;
    while(1){
        //fprintf(stderr, "waiting for client ... ");

        clntlen = sizeof(clntaddr);

        if ((clntsock = accept(servsock,
                        (struct sockaddr *) &clntaddr, &clntlen)) < 0)
            die("accept failed");
        //fprintf(stderr, "client ip: %s\n", inet_ntoa(clntaddr.sin_addr));
        //END BOILERPLATE
        
        char buf[1000];
        int bytes=0;
        while ((bytes = recv(clntsock, buf, sizeof(buf)-1, 0)) > 0) {
            /*char *p=buf;
            while(*p++!='\n');
            *p='\0';*/
            buf[bytes]='\0';
            fputs(buf,stdout);
            fflush(stdout);
        }
        if (bytes < 0) {
            fprintf(stderr, "ERR: recv failed\n");
        }
        close(clntsock);


    }

}
