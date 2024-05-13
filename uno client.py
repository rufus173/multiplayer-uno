print("""                 ____                           
     _______  __/ __/_  _______                 
    / ___/ / / / /_/ / / / ___/  ______         
   / /  / /_/ / __/ /_/ (__  )  /_____/         
  /_/   \__,_/_/  \__,_/____/                   
                 ______                         
     _________  / __/ /__      ______ _________ 
    / ___/ __ \/ /_/ __/ | /| / / __ `/ ___/ _ \ 
   (__  ) /_/ / __/ /_ | |/ |/ / /_/ / /  /  __/
  /____/\____/_/  \__/ |__/|__/\__,_/_/   \___/

    V2.1 | uno client for multiplayer uno      """)         


import socket
import time

#use https://harry-pc.duckdns.org to resolve ip
#if not update manualy
ip = "86.160.112.140"


def recv_data(server):#my program was struggling to get all the data through
    data = b""
    msg = b""
    while msg != b"\r":
        data += msg 
        msg = server.recv(1)
    return data
    

#card display
def display(hand):#MAKE SURE TO SEND THIS A LIST AND NOT A STRING
    hand_str = "" #we need to build it 1 line at a time,and ensure colouring and symbols are correct
    top = ""
    mid_top = ""
    mid = ""
    mid_bottom = ""
    bottom = ""
    for card in hand:
        colour = "\033[0m"
        match card[0]: #figure out ansi escape code required
            case "g":
                colour = "\033[32m"
            case "b":
                colour = "\033[34m"
            case "y":
                colour = "\033[33m"
            case "r":
                colour = "\033[31m"
        match card[1]:
            case "r":
                display_card = " ⇅ "
            case "s":
                display_card = " Ø "
            case "t":
                display_card = "+ 2"
            case "f":
                display_card = "+ 4"
            case "n":
                display_card = " w "
            case _:
                display_card = " "+card[1]+" "
        if card[0] != "w":
            top = top + colour + "╔═══════╗" + "\033[0m"
            mid_top = mid_top + colour + "║       ║" + "\033[0m"
            mid = mid + colour + "║  " + display_card + "  ║"
            mid_bottom = mid_bottom + colour + "║       ║" + "\033[0m"
            bottom = bottom + colour + "╚═══════╝" + "\033[0m"
        else:
            top = top + "\033[31m╔═\033[0m═════\033[32m═╗" + "\033[0m"
            mid_top = mid_top + colour + "\033[31m║ \033[0m     \033[32m ║" + "\033[0m"
            mid = mid + colour + "║  " + display_card + "  ║"
            mid_bottom = mid_bottom + colour + "\033[34m║ \033[0m     \033[33m ║" + "\033[0m"
            bottom = bottom + colour + "\033[34m╚═\033[0m═════\033[33m═╝" + "\033[0m"
    hand_str += top + "\n" + mid_top + "\n" + mid + "\n" +  mid_bottom + "\n" + bottom
    print(hand_str)


#just setting up variables
hand = []
discard = ""

#we will connect to the server
server = socket.socket()
server.connect((ip,8032))

#this is the manager that checks how many players are playing if you are the first to conenct

status = server.recv(1024).decode()
if status == "requesting player count":
    while True:
        try:
            pcount = int(input("how many players total >>>"))
            if pcount <= 1:
                raise ValueError
        except:
            pass
        break
    server.sendall(str(pcount).encode())
else:
    server.sendall(b"_")

hand = server.recv(4096).decode().split(",")
print("\n\n\nyour starting hand")
display(hand)
server.sendall(b"_")#acknowledgement packet

while True:#mainloop
    response = server.recv(1024).decode()
    match response:
        case "discard":
            server.sendall(b"_")
            discard = recv_data(server).decode()
            server.sendall(b"_")
        case "go":
            server.sendall(b"_")#acknowledgement

            #we recieve an updated hand
            hand = server.recv(4096).decode().split(",")
            print("\n\n\n\n\n\n\n\n------------- Your turn -------------")
            print("Your hand")
            display(hand)
            print("Discard pile")
            display([discard])#i spent so long debugging but the logic error of not having discard be a list broke the display function
            
            #logic for playable cards
            can_play = False
            playable_cards = []
            for card in hand:
                if card[0] == discard[0] or card[1] == discard[1] or card[0] == "w":
                    can_play = True
                    playable_cards.append(card)


            if can_play:#add logic for wether to draw or play
                count = 1
                option_str = ""
                print("Options for you to play are as follows:")
                for i in playable_cards:
                    single_option = "   ("+str(count)+")   "
                    option_str += single_option
                    for x in range(9-len(single_option)):
                        option_str += " "#pads out the space meaning all the numbers are aligned
                    count += 1
                print(option_str)
                display(playable_cards)#must be sent in a list
                while True:
                    try:
                        chosen_card = playable_cards[int(input("Number >>>"))-1]
                        break
                    except:
                        pass
                if chosen_card[1] == "s":
                    print("\n\n\nSkipped next players turn\n\n\n")
                    time.sleep(1)
                if chosen_card[1] == "r":
                    print("\n\n\nReversed turn order\n\n\n")
                    time.sleep(1)
                server.sendall(b"card")#tell the server we are playing a card
                server.recv(1024)
                server.sendall(chosen_card.encode())
                response = server.recv(1024).decode()
                if response == "choose colour":
                    print("Choose a colour for your wildcard.\n(1) red  (2) green  (3) blue  (4) yellow")
                    while True:
                        try:
                            colour = ["r","g","b","y"][int(input("number >>>"))-1]
                            break
                        except:
                            pass
                    server.sendall(colour.encode())
                    server.recv(1024)
                    server.sendall(b"_")
                else:
                    server.sendall(b"_")
            else:
                print("\n\n\nThere were no cards for you to play,\n meaning you drew one.\n\n\n")
                server.sendall(b"draw")
                hand.append(server.recv(1024).decode())
                print("your new hand:")
                display(hand)
                time.sleep(1)
        case "plus":
            server.sendall(b"_")
            hand = server.recv(4096).decode().split(",")
            print("\n\n\n\n\n\n\n\n------------- Your turn -------------")
            print("Your hand")
            display(hand)
            print("Discard pile")
            display([discard])

            playable_cards = []
            for card in hand:
                if card[1] == discard[1]:
                    can_play = True
                    playable_cards.append(card)
            if playable_cards != []:
                print("\n\n\nYou must respond to the plus card. What will you do it with?")
                count = 1
                option_str = ""
                print("Options for you to respond are as follows:")
                for i in playable_cards:
                    single_option = "   ("+str(count)+")   "
                    option_str += single_option
                    for x in range(9-len(single_option)):
                        option_str += " "#pads out the space meaning all the numbers are aligned
                    count += 1
                print(option_str)
                display(playable_cards)#must be sent in a list
                while True:
                    try:
                        chosen_card = playable_cards[int(input("Number >>>"))-1]
                        break
                    except:
                        pass
                server.sendall(chosen_card.encode())
                choose = server.recv(1024).decode()
                if choose == "choose colour":
                    print("Choose a colour for your wildcard.\n(1) red  (2) green  (3) blue  (4) yellow")
                    while True:
                        try:
                            colour = ["r","g","b","y"][int(input("number >>>"))-1]
                            break
                        except:
                            pass
                    server.sendall(colour.encode())
                    server.recv(1024)
                    server.sendall(b"_")
                else:
                    server.sendall(b"_")
            else:
                print("\n\nYou cant respond to the plus cards. Now drawing...\n\n")
                server.sendall(b"no response")
                time.sleep(1)
            hand = server.recv(4096).decode().split(",")
            server.sendall(b"_")
            print("Your new hand:")
            display(hand)