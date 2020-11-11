import socket
from _thread import *
import _pickle as pickle
import time
import random
import math

S = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
S.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
S.settimeout(500)
PORT = 5000
BALL_RADIUS = 5
START_RADIUS = 7
ROUND_TIME = 60 * 5
MASS_LOSS_TIME = 7
W, H = 1600, 830
SERVER_IP = "192.168.0.169"


# Setup
try:
    S.bind((SERVER_IP,PORT))
except socket.error as e:
    print(str(e))
    print("[SERVER] Server could not start")
    quit()

##have two sockets?
# - one for lobby
# - one for game
# probelms distinguishing between lobby and start
print(f"[SERVER] UDP Server Started with local ip {SERVER_IP}")

# dynamic variables
players = {}
playerIP = []
balls = []
connections = 0
_id = 0
colors = [(255,0,0), (255, 128, 0), (255,255,0), (128,255,0),(0,255,0),(0,255,128),(0,255,255),(0, 128, 255), (0,0,255), (0,0,255), (128,0,255),(255,0,255), (255,0,128),(128,128,128), (0,0,0)]
start = False
stat_time = 0
game_time = "Starting Soon"
nxt = 1


# FUNCTIONS

def release_mass(players):
    """
    releases the mass of players
    :param players: dict
    :return: None
    """
    for player in players:
        p = players[player]
        if p["score"] > 8:
            p["score"] = math.floor(p["score"]*0.95)


def check_collision(players, balls):
    """
    checks if any of the player have collided with any of the balls
    :param players: a dictonary of players
    :param balls: a list of balls
    :return: None
    """
    to_delete = []
    for player in players:
        p = players[player]
        x = p["x"]
        y = p["y"]
        for ball in balls:
            bx = ball[0]
            by = ball[1]

            dis = math.sqrt((x - bx)**2 + (y-by)**2)
            if dis <= START_RADIUS + p["score"]:
                p["score"] = p["score"] + 0.5
                balls.remove(ball)


def player_collision(players):
    """
    checks for player collision and handles that collision
    :param players: dict
    :return: None
    """
    sort_players = sorted(players, key=lambda x: players[x]["score"])
    for x, player1 in enumerate(sort_players):
        for player2 in sort_players[x+1:]:
            p1x = players[player1]["x"]
            p1y = players[player1]["y"]

            p2x = players[player2]["x"]
            p2y = players[player2]["y"]

            dis = math.sqrt((p1x - p2x)**2 + (p1y-p2y)**2)
            if dis < players[player2]["score"] - players[player1]["score"]*0.85:
                players[player2]["score"] = math.sqrt(players[player2]["score"]**2 + players[player1]["score"]**2) # adding areas instead of radii
                players[player1]["score"] = 0
                players[player1]["x"], players[player1]["y"] = get_start_location(players)
                print(f"[GAME] " + players[player2]["name"] + " ATE " + players[player1]["name"])


def create_balls(balls, n):
    """
    creates orbs/balls on the screen
    :param balls: a list to add balls/orbs to
    :param n: the amount of balls to make
    :return: None
    """
    for i in range(n):
        while True:
            stop = True
            x = random.randrange(0,W)
            y = random.randrange(0,H)
            for player in players:
                p = players[player]
                dis = math.sqrt((x - p["x"])**2 + (y-p["y"])**2)
                if dis <= START_RADIUS + p["score"]:
                    stop = False
            if stop:
                break

        balls.append((x,y, random.choice(colors)))


def get_start_location(players):
    """
    picks a start location for a player based on other player
    locations. It wiill ensure it does not spawn inside another player
    :param players: dict
    :return: tuple (x,y)
    """
    while True:
        stop = True
        x = random.randrange(0,W)
        y = random.randrange(0,H)
        for player in players:
            p = players[player]
            dis = math.sqrt((x - p["x"])**2 + (y-p["y"])**2)
            if dis <= START_RADIUS + p["score"]:
                stop = False
                break
        if stop:
            break
    return (x,y)


def new_client(name, _id):
    """
    runs in a new thread for each player connected to the server
    :param con: ip address of connection
    :param _id: int
    :return: None
    """
    global connections, players, balls, game_time, nxt, start
    current_id = _id
    # recieve a name from the client
    print("[LOG]", name, "connected to the server.")

    # Setup properties for each new player
    color = colors[current_id]
    x, y = get_start_location(players)
    players[current_id] = {"x":x, "y":y,"color":color,"score":0,"name":name}  # x, y color, score, name
    

# MAINLOOP
# setup level with balls
create_balls(balls, random.randrange(200,250))

print("[GAME] Setting up level")
print("[SERVER] Waiting for connections")

# Keep looping to accept new connections
while not start:
    # recieve a name from the client
    data,addressS = S.recvfrom(16)
    
    if addressS not in playerIP:
        name = data.decode("utf-8")
        playerIP.append(addressS)
        print("[CONNECTION] Connected to:", addressS)
        # pickle data and send initial info to clients
        connections += 1
        new_client(name,_id)
        _id += 1
        if input("Next Player? Y/N: ") == "N":
            start = True
            start_time = time.time()
            print("[STARTED] Game Started")
        # increment connections start new thread then increment ids
        
for i in range(len(playerIP)):
    S.sendto(str.encode(str(i)),playerIP[i])
    
#game started  
while True:

        if start:
            game_time = round(time.time()-start_time)
            # if the game time passes the round time the game will stop
            if game_time >= ROUND_TIME:
                start = False
            else:
                if game_time // MASS_LOSS_TIME == nxt:
                    nxt += 1
                    release_mass(players)
                    print(f"[GAME] {name}'s Mass depleting")
        try:
            # Recieve data from client
            data, addressS = S.recvfrom(32)
            print("[DATA] Received", data, "from client address:", addressS)
            recv_id = playerIP.index(addressS)
            if not data: 
                break
            data = data.decode("utf-8")
            print("[DATA] Received", data, "from client id:", recv_id)

            # look for specific commands from recieved data
            if data.split(" ")[0] == "move":
                split_data = data.split(" ")
                x = int(split_data[1])
                y = int(split_data[2])
                players[recv_id]["x"] = x
                players[recv_id]["y"] = y
    
                # only check for collison if the game has started
                if start:
                    check_collision(players, balls)
                    player_collision(players)
    
                # if the amount of balls is less than 150 create more
                if len(balls) < 150:
                    create_balls(balls, random.randrange(100,150))
                    print("[GAME] Generating more orbs")

                send_data = pickle.dumps((balls,players, game_time))

            elif data.split(" ")[0] == "id":
                send_data = str.encode(str(recv_id))  # if user requests id then send it

            elif data.split(" ")[0] == "jump":
                send_data = pickle.dumps((balls,players, game_time))
            else:
                # any other command just send back list of players
                send_data = pickle.dumps((balls,players, game_time))

            # send data back to clients
            S.sendto(send_data,addressS)

        except Exception as e:
            print(e)
            break  # if an exception has been reached disconnect client

        time.sleep(0.001)

# when program ends
print("[SERVER] Server offline")

