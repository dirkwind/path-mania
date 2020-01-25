import turtle, random, threading, time, sys


def text_scroll(z):
    for x in z:
        sys.stdout.write(x)
        sys.stdout.flush()
        if x == ',':
            time.sleep(0.15)
        elif x == '.':
            time.sleep(0.25)
        else:
            time.sleep(0.004)

text_scroll("""\n\n\n\n\n\n\n\n\n\n\n\nMove with W, A, S, and D or arrow keys.
The goal is to not be gruesomely murdered by murderers. These murderers are shapes that aren't you, a chevron.

Build a map with the paths provided (see the amount in top left). After placing all of your paths the level will begin.
After reaching set scores (found in the top right) you will progress to the next level and get more paths to place.

Godspeed.
""")
input("\nPress enter to continue: ")
username = input("\nChoose a username: ")
difficulty = input("\nChoose a difficulty (easy, normal, hard, impossible): ")

if difficulty.lower() in ['easy', 'e']:
    difficulty = 'easy'
    refresh = 400
    speed = 8
    paths = 80
    map_size = 20
    score_increment = 5
    path_handicap = round(2/3, 2)
elif difficulty.lower() in ['normal', 'n']:
    difficulty = 'normal'
    refresh = 200
    speed = 5
    paths = 60
    map_size = 18
    score_increment = 5
    path_handicap = 1
elif difficulty.lower() in ['hard', 'h']:
    difficulty = 'hard'
    refresh = 100
    speed = 3
    paths = 30
    map_size = 14
    score_increment = 5
    path_handicap = 1
elif difficulty.lower() in ['impossible', 'i']:
    difficulty = 'impossible'
    refresh = 50
    speed = 2
    paths = 25
    map_size = 12
    score_increment = 2.5
    path_handicap = 2
elif difficulty == 'CHEAT':
    difficulty = 'CHEAT'
    score_increment = 50
    refresh = 200
    speed = 0
    paths = 60
    map_size = 18
    path_handicap = 1
    print('mode: cheats')
else:
    print('')
    text_scroll("That was not a valid input, so you get random start.")
    difficulty = 'random'
    refresh = random.randint(100, 400)
    speed = random.randint(1, 10)
    paths = random.randint(25, 90)
    score_increment = 5
    map_size = random.choice([10, 12, 14, 16, 18, 20])



screen = turtle.Screen()


distance = 25
multiples_of_dis = []
moving = False
#paths=45
coords_visited = set()
coords_in_play = set()
enemy_list = []
cell_map = []
gamemode = 'build'
player_coords = (0, 0)
score = 0
border_size = 0
level = 1 
    
def make_border(factor, color):
    global border_size
    border_size = (distance*factor)
    border_turt = turtle.Turtle()
    border_turt.speed(0)
    border_turt.color(color)
    border_turt.penup()
    border_turt.goto(border_size/2, border_size/2)
    border_turt.pendown()
    border_turt.goto(border_size/2, -border_size/2)
    border_turt.goto(-border_size/2, -border_size/2)
    border_turt.goto(-border_size/2, border_size/2)
    border_turt.goto(border_size/2, border_size/2)
    border_turt.hideturtle()

score_turt = turtle.Turtle()
score_turt.hideturtle()
score_turt.speed(0)
score_turt.penup()
score_turt.goto((260, 255))

level_turt = turtle.Turtle()
level_turt.hideturtle()
level_turt.speed(0)
level_turt.penup()
level_turt.goto((-10, 255))

path_turt = turtle.Turtle()
path_turt.hideturtle()
path_turt.speed(0)
path_turt.penup()
path_turt.goto((-260, 255))

for multiplier in range(100):
    multiples_of_dis.append(distance * multiplier)
for multiplier in range(1, 100):
    multiples_of_dis.append(distance * -multiplier)
multiples_of_dis.sort()


class Enemy(object):

    def __init__(self, color, size, shape, speed):
        self.moving = False
        self.speed = speed
        self.turtle = turtle.Turtle(shape)
        self.turtle.color(color)
        self.turtle.penup()
        self.turtle.shapesize(size)
        self.turtle.speed(0)
        self.turtle.hideturtle()
        self.turtle.goto(random.choice(tuple(coords_in_play)))
        self.turtle.showturtle()
        self.turtle.speed(self.speed)
        
    def move_enemy(self, direction):
        if not self.moving:
            self.moving = True
            if direction == 'right':
                self.turtle.setheading(0)
            elif direction == 'left':
                self.turtle.setheading(180)
            elif direction == 'up':
                self.turtle.setheading(90)
            else:
                self.turtle.setheading(270)
            self.turtle.forward(distance)
            self.moving = False
    
    def choose_direction(self):
        distances = pathfinder.distances
        x, y = get_position(self.turtle)
        possible_directions = []
        distance_list = []
        if ((x, y), (x+distance, y)) in coords_visited:
            if (x+distance, y) in distances:
                possible_directions.append('right')
                distance_list.append(distances[(x+distance, y)])
        if ((x, y), (x-distance, y)) in coords_visited:
            if (x-distance, y) in distances:
                possible_directions.append('left')
                distance_list.append(distances[(x-distance, y)])
        if ((x, y), (x, y+distance)) in coords_visited:
            if (x, y+distance) in distances:
                possible_directions.append('up')
                distance_list.append(distances[(x, y+distance)])
        if ((x, y), (x, y-distance)) in coords_visited:
            if (x, y-distance) in distances:
                possible_directions.append('down')
                distance_list.append(distances[(x, y-distance)])
        best_direction = possible_directions[distance_list.index(min(distance_list))]
        self.move_enemy(best_direction)

class Pathfinder(object):


    def get_path(self, turtle):
        pos = get_position(turtle)
        distances = {pos : 0}
        self.q_list = []
        self.check_neighbors(pos, distances)
        self.distances = distances
    
    def check_neighbors(self, position, distances):
        x, y = position
        if ((x, y), (x+distance, y)) in coords_visited and (x+distance,y) not in distances:
            distances[(x+distance, y)] = distances[(x, y)] + 1
            self.q_list.append((x+distance, y))
        if ((x, y), (x-distance, y)) in coords_visited and (x-distance,y) not in distances:
            distances[(x-distance, y)] = distances[(x, y)] + 1
            self.q_list.append((x-distance, y))
        if ((x, y), (x, y+distance)) in coords_visited and (x,y + distance) not in distances:
            distances[(x, y+distance)] = distances[(x, y)] + 1
            self.q_list.append((x, y+distance))
        if ((x, y), (x, y-distance)) in coords_visited and (x,y - distance) not in distances:
            distances[(x, y-distance)] = distances[(x, y)] + 1
            self.q_list.append((x, y-distance))
        if len(self.q_list) != 0:
            new_pos = self.q_list.pop(0)
            self.check_neighbors(new_pos, distances)
        
        
def get_position(turtle):
    xcor = int(turtle.xcor())
    ycor = int(turtle.ycor())
    new_coords = []
    for cor in [xcor, ycor]:
        differences = []
        for num in multiples_of_dis:
            diff = num - cor
            differences.append(diff)
        round_index = differences.index(min(differences, key=abs))
        new_coords.append(multiples_of_dis[round_index])
    xcor, ycor = new_coords
    return (xcor, ycor)

def check_path(prev_position):
    global paths
    if (get_position(player), prev_position) not in coords_visited and (prev_position, get_position(player)) not in coords_visited:
        paths -= 1
        coords_visited.add((get_position(player), prev_position))
        coords_visited.add((prev_position, get_position(player)))
        coords_in_play.add(get_position(player))
    
def get_projected_path(direction, turtle):
    if direction == 'right':
        x = get_position(turtle)[0] + distance
        return (get_position(turtle), (x, get_position(turtle)[1]))
    elif direction == 'left':
        x = get_position(turtle)[0] - distance
        return (get_position(turtle), (x, get_position(turtle)[1]))
    elif direction == 'up':
        y = get_position(turtle)[1] + distance
        return (get_position(turtle), (get_position(turtle)[0], y))
    elif direction == 'down':
        y = get_position(turtle)[1] - distance
        return (get_position(turtle), (get_position(turtle)[0], y))
    else:
        print('Error: unknown distance input (' + str(direction) + ') detected.')
    
def check_drawing():
    global gamemode, enemy, enemy2, paths
    if paths == 0:
        path_turt.clear()
        path_turt.write('Paths: ' + str(paths), font=('Arial', 25, 'normal'))
        paths -= 1
        player.penup()
        if level == 1:
            enemy = Enemy('blue', 1, 'circle', 2)
            enemy_list.append(enemy)
        elif level == 2:
            enemy2 = Enemy('red', 1, 'triangle', 4)
            enemy_list.append(enemy2)
        gamemode = 'run'
    elif paths >= 0:
        player.pendown()
        path_turt.clear()
        path_turt.write('Paths: ' + str(paths), font=('Arial', 25, 'normal'))
    
def end_game():
    global gamemode
    screen.clear()
    gamemode = 'dead'
    add_user_leaderboard(difficulty, username, score)
    get_leaderboard(difficulty)
    score_turt.goto(-200, 0)
    score_turt.clear()
    score_turt.write("Your Score: {}".format(round(score)), font=('Arial', 50, 'normal'))
    score_turt.goto(-200, -25)
    score_turt.write("Level: " + str(level) + "\tDifficulty: " + difficulty.capitalize() + "", font=('Arial', 20, 'normal'))
    score_turt.goto(1000,1000)
    

def move_right():
    global moving
    if not moving:
        if gamemode == 'run' and get_projected_path('right', player) not in coords_visited:
            return None
        if get_projected_path('right', player)[1][0] > int(border_size/2) or get_projected_path('right', player)[1][1] > int(border_size/2):
            return None
        moving = True
        current_pos = get_position(player)
        player.speed(0)
        player.setheading(0)
        player.speed(speed)
        player.forward(distance)
        check_path(current_pos)
        pathfinder.get_path(player)
        moving = False
    check_drawing()

def move_left():
    global moving
    if not moving:
        if gamemode == 'run' and get_projected_path('left', player) not in coords_visited:
            return None
        if get_projected_path('left', player)[1][0] < -int(border_size/2) or get_projected_path('left', player)[1][1] < -int(border_size/2):
            return None
        moving = True
        current_pos = get_position(player)
        player.speed(0)
        player.setheading(180)
        player.speed(speed)
        player.forward(distance)
        check_path(current_pos)
        pathfinder.get_path(player)
        moving = False
    check_drawing()

def move_up():
    global moving
    if not moving:
        if gamemode == 'run' and get_projected_path('up', player) not in coords_visited:
            return None
        if get_projected_path('up', player)[1][0] > int(border_size/2) or get_projected_path('up', player)[1][1] > int(border_size/2):
            return None
        moving = True
        current_pos = get_position(player)
        player.speed(0)
        player.setheading(90)
        player.speed(speed)
        player.forward(distance)
        check_path(current_pos)
        pathfinder.get_path(player)
        moving = False
    check_drawing()

def move_down():
    global moving
    if not moving:
        if gamemode == 'run' and get_projected_path('down', player) not in coords_visited:
            return None
        if get_projected_path('down', player)[1][0] < -int(border_size/2) or get_projected_path('down', player)[1][1] < -int(border_size/2):
            return None
        moving = True
        current_pos = get_position(player)
        player.speed(0)
        player.setheading(270)
        player.speed(speed)
        player.forward(distance)
        check_path(current_pos)
        pathfinder.get_path(player)
        moving = False
    check_drawing()

def change_level(level_increase, paths_bonus, score_bonus):
    global gamemode, level, paths, score
    gamemode = 'build'
    score += score_bonus
    paths = 0
    paths += round(paths_bonus/path_handicap)
    level += level_increase
    level_turt.clear()
    level_turt.write("Level: "+str(level), font=('Arial', 25, 'normal'))
    path_turt.clear()
    path_turt.write('Paths: ' + str(paths), font=('Arial', 25, 'normal'))

def center_player():
    global moving
    moving = True
    player.penup()
    player.speed(0)
    player.setpos(0, 0)
    player.speed(speed)
    moving = False

def update_score():
    global score, paths, refresh
    if gamemode == 'run':
        score += score_increment
        if score == 400:
            change_level(1, 10, 50)
        elif score == 900:
            change_level(1, 20, 100)
        elif score == 1600:
            change_level(1, 30, 150)
        elif score == 2300:
            change_level(1, 40, 200)
            refresh = round(refresh/2)
        elif score == 3100:
            change_level(1, 30, 250)
            enemy3 = Enemy('yellow', 1, 'square', 5)
            enemy_list.append(enemy3)
        elif score == 4200:
            change_level(1, 20, 300)
            center_player()
            make_border(map_size - 2, 'orange')
            refresh = round(refresh/2)
        elif score == 5500:
            change_level(1, 10, 350)
        elif score == 6500:
            change_level(1, 9, 400)
            center_player()
            make_border(map_size - 4, 'yellow')
        elif score == 7600:
            change_level(1, 5, 450)
            refresh = round(refresh/2)
        elif score == 9000:
            change_level(1, 4, 500)
            enemy4 = Enemy('purple', 1, 'turtle', 6)
            enemy_list.append(enemy4)
        elif score == 11000:
            change_level(1, 3, 550)
        elif score == 13000:
            change_level(1, 2, 600)
        elif score == 16200:
            change_level(1, 1, 650)
        elif score == 18000:
            change_level(1, 1, 650)
            center_player()
            make_border(map_size - 6, 'blue')
        elif score == 21000:
            change_level(1, 0, 700)
        elif score == 24000:
            change_level(1, 0, 750)
            refresh = round(refresh/4)
        elif score == 29000:
            change_level(1, 0, 800)
        elif score == 35000:
            change_level(1, 1, 850)
            center_player()
            make_border(map_size - 8, 'purple')
        score_turt.clear()
        score_turt.write(score, font=('Arial', 25, 'normal'))
    screen.ontimer(update_score, refresh)


def update_player_pos():
    global player_coords
    if gamemode == 'run':
        for en in enemy_list:
            en.choose_direction()
        for en in enemy_list:
            if abs(en.turtle.xcor() - player.xcor()) < 10 and abs(en.turtle.ycor() - player.ycor()) < 10:
                end_game()
    screen.ontimer(update_player_pos, refresh)

def get_leaderboard(difficulty):
    infile = open("saves/turtle_leaderboard.txt", 'r')
    leaderboard = {}
    index = 0
    print('Difficulty User : Score')
    for line in infile:
        line = line.split('|')
        leaderboard[str(line[0])+str(index).zfill(8)] = round(float(line[1]))
        index += 1
    while len(leaderboard) > 0:
        highest = max(leaderboard, key=leaderboard.get)
        highest_split = highest.split('!')
        if highest_split[0] == 'n':
            d = 'Normal'
        elif highest_split[0] == 'e':
            d = 'Easy'
        elif highest_split[0] == 'h':
            d = 'Hard'
        elif highest_split[0] == 'i':
            d = 'Impossible'
        elif highest_split[0] == 'c':
            d = 'Cheat'
        elif highest_split[0] == 'r':
            d = 'Random'
        if d.lower() == difficulty.lower():
            print(d, highest_split[1][:len(highest_split[1])-8], ":", leaderboard.pop(highest))
        else:
            leaderboard.pop(highest)
    infile.close()

def add_user_leaderboard(difficulty, username, score):
    infile = open("saves/turtle_leaderboard.txt", 'a')
    infile.write(difficulty.lower()[0]+'!'+str(username)+'|'+str(score)+'\n')
    infile.close()


make_border(map_size, 'red')
player = turtle.Turtle()
player.speed(speed)
pathfinder = Pathfinder()
score_thread = threading.Thread(target=update_score)
player_pos_thread = threading.Thread(target=update_player_pos)

screen.onkeypress(move_left, 'a')
screen.onkeypress(move_right, 'd')
screen.onkeypress(move_up, 'w')
screen.onkeypress(move_down, 's')
screen.onkeypress(move_left, 'Left')
screen.onkeypress(move_right, 'Right')
screen.onkeypress(move_up, 'Up')
screen.onkeypress(move_down, 'Down')

score_thread.start()
player_pos_thread.start()
level_turt.write("Level: "+str(level), font=('Arial', 25, 'normal'))

screen.listen()
screen.mainloop()


