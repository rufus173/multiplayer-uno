#                 ____                           
#     _______  __/ __/_  _______                 
#    / ___/ / / / /_/ / / / ___/  ______         
#   / /  / /_/ / __/ /_/ (__  )  /_____/         
#  /_/   \__,_/_/  \__,_/____/                   
#                 ______                         
#     _________  / __/ /__      ______ _________ 
#    / ___/ __ \/ /_/ __/ | /| / / __ `/ ___/ _ \
#   (__  ) /_/ / __/ /_ | |/ |/ / /_/ / /  /  __/
#  /____/\____/_/  \__/ |__/|__/\__,_/_/   \___/                 


import socket
import socket_manager
import random
import time

print("waiting to allow network to start")
time.sleep(5)#to allow the network services on a machine to start (this is intended to run at startup)

#lets build the deck
#we shall use the notation colour card, e.g r0 for red zero and gs for green skip
def build_deck():
    global deck
    deck = ["r0","g0","b0","y0"] #we can use w for wild , e.g. wn for wild card and wf for wild +4. for plus 2 we can use colour + t, e.g. gp for green +t
    #when wildcards are played a colour is selected and they will become colour + type, eg wf(wild +4) becomes gf(green +4)
    for i in range(2):
        for c in ["r","g","b","y"]:
            for n in range(9):
                deck.append(c+str(n+1))
            for s in ["s","r","t"]:#skip, reverse, plus 2
                deck.append(c+s)
    for i in range(6):
        deck.append("wn")#wild
        deck.append("wf")#wild plus 4
    random.shuffle(deck)
while True:
    try:
        build_deck()
        #get total number of players
        pcount = 1
        player_names = [] #indexes correspond with keys in dictionary

        handle = socket_manager.handler()
        handle.auto_bind(8032)
        handle.listen(1)

        print("waiting for player count")
        handle.sockets[0].sendall(b"requesting player count")
        pcount = int(handle.sockets[0].recv(1024).decode())
        print(pcount)
        handle.listen(pcount-1)
        for i in range(0,pcount):
            handle.sockets[i].sendall(b"username")#request usernames
            player_names.append(handle.sockets[i].recv(1024).decode())
        print("usernames gathered:",player_names)

        print("Starting")

        order = 1 #set to -1 to reverse turn order
        turn = 0#whos turn it is
        card_stack = 0 #for holding info about stacked handle.sockets[i].sendall(b"_")and +4s
        random.shuffle(deck)
        hands = {}

        for i in range(pcount):
            hands[i] = []
            for j in range(7):
                hands[i].append(deck.pop(0))

        print(hands)

        for i in range(pcount):
            temp = ""
            for c in hands[i]:
                temp = temp + c + ","
            temp = temp.rstrip(",")
            handle.sockets[i].sendall(temp.encode())
            handle.sockets[i].recv(1024)

        discard = "w"
        while discard[0] == "w":#stops the game starting on a wildcard
            discard = deck.pop(0)

        while True:#the mainloop

            #commands are issued telling the client what to expect, so go for their turn and discard to receive the discard pile

            #check if a player has won
            for i in hands:
                if hands[i] == []:
                    print("player",i,"won")
                    handle.sockets[i].sendall(b"notify")
                    handle.sockets[i].recv(1024)
                    handle.sockets[i].sendall(b"You win! :)")
                    handle.sockets[i].recv(1024)
                    for x in hands:
                        if x != i:
                            handle.sockets[x].sendall(b"notify")
                            handle.sockets[x].recv(1024)
                            handle.sockets[x].sendall(b"You loose :(")
                            handle.sockets[x].recv(1024)
                    raise SystemExit("game finnished")

            if turn > pcount-1:#this before check is to allow for skip turns
                turn = 0
            elif turn < 0:
                turn = pcount-1
            turn += order #gonna increment or decrement depending on direction of play
            if turn > pcount-1:
                turn = 0
            elif turn < 0:
                turn = pcount-1
            for i in range(pcount):
                handle.sockets[i].sendall(b"discard")
                handle.sockets[i].recv(1024)
                handle.sockets[i].sendall((discard+"\r").encode())
                handle.sockets[i].recv(1024)
                handle.sockets[i].sendall(b"player info")
                handle.sockets[i].recv(1024)
                temp = ""
                for x in range(pcount):
                    if i == x:
                        continue
                    temp = temp + player_names[x] + "\r" + str(len(hands[x])) + "\0"
                    temp = temp.rstrip("\0")
                    handle.sockets[i].sendall(temp.encode())

            if card_stack == 0:#if they have not been +4d or +2d
                handle.sockets[turn].sendall(b"go")#tell them its their turn
                handle.sockets[turn].recv(1024)
                temp = ""
                for c in hands[turn]:
                    temp = temp + c + ","
                temp = temp.rstrip(",")
                handle.sockets[turn].sendall(temp.encode())#resending their hand so i can easily deal with plus 2s and 4s
                response = handle.sockets[turn].recv(1024).decode()#we get their card, or a request to draw 1
                if response ==  "draw":
                    new_card = deck.pop(0)
                    hands[turn].append(new_card)
                    handle.sockets[turn].sendall(new_card.encode())
                if response == "card":
                    handle.sockets[turn].sendall(b"_")
                    incoming_card = handle.sockets[turn].recv(1024).decode()
                    discard = incoming_card
                    hands[turn].remove(incoming_card)#remnove cards from their hand that they play

                    #special cards game logic
                    if discard[0] == "w":
                        handle.sockets[turn].sendall(b"choose colour")
                        colour = handle.sockets[turn].recv(1024).decode()
                        discard = colour + discard[1]
                        handle.sockets[turn].sendall(b"_")
                    else:
                        handle.sockets[turn].sendall(b"no action needed")
                    handle.sockets[turn].recv(1024)#acknowledge

                    if incoming_card[1] == "r":#reverse
                        order * -1
                    if incoming_card[1] == "s":#skip
                        turn += order
                    if incoming_card[1] == "t":# +2
                        card_stack += 2
                    if incoming_card[1] == "f":# +4
                        card_stack += 4
                    # logic neeeded to work out plus 2s and plus 4s and logic for choosing colours
            else:
                handle.sockets[turn].sendall(b"plus")
                handle.sockets[turn].recv(1024)
                temp = ""
                for c in hands[turn]:
                    temp = temp + c + ","
                temp = temp.rstrip(",")
                handle.sockets[turn].sendall(temp.encode())#resending their had to update them
                response = handle.sockets[turn].recv(1024).decode()
                if response == "no response":
                    for i in range(card_stack):
                        hands[turn].append(deck.pop(0))
                    card_stack = 0
                else:
                    discard = response
                    hands[turn].remove(response)
                    if discard[1] == "t":# +2
                        card_stack += 2
                    if discard[1] == "f":# +4
                        card_stack += 4
                    if discard[0] == "w":
                        handle.sockets[turn].sendall(b"choose colour")
                        colour = handle.sockets[turn].recv(1024).decode()
                        discard = colour + discard[1]
                        handle.sockets[turn].sendall(b"_")
                        handle.sockets[turn].recv(1024)
                    else:
                        handle.sockets[turn].sendall(b"_")
                        handle.sockets[turn].recv(1024)
                temp = ""
                for c in hands[turn]:
                    temp = temp + c + ","
                temp = temp.rstrip(",")
                handle.sockets[turn].sendall(temp.encode())
                handle.sockets[turn].recv(1024)
    except Exception as problem:
        print("error occured, restarting")
        print(problem)