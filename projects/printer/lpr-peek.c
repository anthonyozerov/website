#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <string.h>

void feedOut(){
    //printf("SIMULATED FEED OUT\n");
    printf("\x1BJ\xD8\x1BJ\xD8\x1BJ\x6C");
    fflush(stdout);
}
void feedIn(){
    //printf("SIMULATED FEED IN\n");
    printf("\x1Bj\xD8\x1Bj\xD8\x1Bj\x6C");
    fflush(stdout);
}

int main(){

    //set font to Roman:
    printf("\ex1");
    printf("\ek0");

    printf("\n\n");
    feedIn();
    
    int linelength=80;
    char buf[linelength+2];
    int eof=0;
    while(!eof){
        pid_t pid=fork();
        if(pid==0){ //child timer process
            sleep(5);
            feedOut();
            exit(0);
        }
        else{
            eof=!fgets(buf,sizeof(buf),stdin);
            buf[strlen(buf)-1]='\n';
            if(waitpid(pid, NULL, WNOHANG)<=0){
                kill(pid, SIGKILL);
                waitpid(pid, NULL, 0);
                if(eof){
                    feedOut();
                }
            }
            else if (!eof){
                feedIn();
                fflush(stdout);
            }
            if(!eof) fputs(buf,stdout);
            fflush(stdout);
        }
    }
    
}
