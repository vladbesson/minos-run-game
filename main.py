import math
import random

import pyray as pr


def main():
    pr.init_window(800, 600, "Minos Run")
    pr.set_target_fps(60)
    pr.rl_set_line_width(3)
    camera = pr.Camera3D((0,0.5,0), (1,0.5,1), (0,1,0), 60, pr.CAMERA_PERSPECTIVE)

    player = Player()
    maze = Maze()
    agent = MazeAgent(maze)
    game_state = "pause"
    level = 0
    msg = "Click to start"

    while not pr.window_should_close():
        if game_state == "play":
            player.controls(maze)
            agent.update(maze)
            if maze.exit == (int(player.pos.x), int(player.pos.z)):
                level += 1
                game_state = "pause"
                msg = "You won! Click to start"
                player = Player()
                maze = Maze(level*2+15)
                agent = MazeAgent(maze, 1+level/5)
            elif agent.done:
                game_state = "pause"
                msg = "You lost! Click to retry"
                player = Player()
                maze = Maze(level*2+15)
                agent = MazeAgent(maze, 1+level/5)
                
        camera.position = player.pos
        camera.target = pr.vector3_add(player.pos, player.direction)
        pr.begin_drawing()
        pr.clear_background(pr.SKYBLUE)
        pr.begin_mode_3d(camera)
        pr.draw_sphere((player.pos.x-150, 500, player.pos.z), 25, pr.YELLOW)
        pr.draw_grid(maze.size*10, 0.2)
        pr.draw_plane((0, -0.01, 0), (maze.size*2, maze.size*2), pr.WHITE)

        for i in range(maze.size):
            for j in range(maze.size):
                if maze.maze[i][j] != 0:
                    height = maze.heights[i][j]
                    pr.draw_cube((i+0.5, 0.5*height, j+0.5), 1, height, 1, maze.colors[i][j])
                    draw_cube_wires_thick((i+0.5, 0.5*height, j+0.5), 1, height, 1, 0.01, pr.BLACK)
                    pr.draw_cube((i+0.502, 0.5*height-0.002, j+0.502), 1, height, 1, (0,0,0,100))
                    pr.draw_cube((i+0.503, 0.5*height-0.003, j+0.498), 1, height, 1, (0,0,0,50))
                    pr.draw_plane((i+1, 0.01, j+0.5), (0.7*height, 1), (0,0,0,100))
        pr.draw_capsule_wires((maze.exit[0]+0.5, 0.35, maze.exit[1]+0.5), (maze.exit[0]+0.5, 0.7, maze.exit[1]+0.5), 0.35, 10, 4, pr.YELLOW)
        pr.draw_capsule(agent.pos, (agent.pos.x, 0.5, agent.pos.z), 0.25, 10, 4, (50, 100, 200, 100))
        pr.end_mode_3d()
        if game_state != "play":
            pr.draw_text(f"Current level: {level+1}", 50, 100, 40, pr.WHITE)
            pr.draw_text(msg, 50, 50, 40, pr.WHITE)
            if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
                game_state = "play"
        pr.end_drawing()


class Player:
    def __init__(self):
        self.pos = pr.Vector3(1.5, 0.5, 1.5)
        self.yaw = 0
        self.pitch = 0
        self.sensitivity = 0.003
        self.direction = pr.Vector3(1,0,1)
        self.speed = 2
        pr.disable_cursor()

    def controls(self, maze):
        speed = pr.get_frame_time()*self.speed
        mouse_delta = pr.get_mouse_delta()
        self.yaw -= mouse_delta.x * self.sensitivity
        self.pitch = max(-1.57, min(1.57, self.pitch - mouse_delta.y*self.sensitivity))
        sin_yaw, cos_yaw = math.sin(self.yaw), math.cos(self.yaw)

        # adjust camera direction
        self.direction.x = math.cos(self.pitch) * sin_yaw
        self.direction.y = math.sin(self.pitch)
        self.direction.z = math.cos(self.pitch) * cos_yaw

        forward = pr.is_key_down(pr.KEY_W) - pr.is_key_down(pr.KEY_S)
        sideward = pr.is_key_down(pr.KEY_D) - pr.is_key_down(pr.KEY_A)

        if forward != 0 and sideward != 0:
            speed *= 0.707

        nx, nz = self.pos.x, self.pos.z

        nx += speed * (sin_yaw*forward - cos_yaw*sideward)
        nz += speed * (cos_yaw*forward + sin_yaw*sideward)

        if maze.no_collision(nx, nz):
            self.pos.x, self.pos.z = nx, nz
        elif maze.no_collision(nx, self.pos.z):
            self.pos.x = nx
        if maze.no_collision(self.pos.x, nz):
            self.pos.z = nz


class Maze:
    def __init__(self, size=15):
        self.size = size
        self.maze = [[1] * self.size for _ in range(self.size)]
        self.colors = [[[random.randint(0,255) for _ in range(3)] + [255] for _ in range(self.size)] for _ in range(self.size)]
        self.heights = [[round(random.uniform(0.2, 2), 1) for _ in range(self.size)] for _ in range(self.size)]

        def carve(x, y):
            self.maze[x][y] = 0
            dirs = [(2, 0), (-2, 0), (0, 2), (0, -2)]
            random.shuffle(dirs)

            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 1 <= nx < self.size - 1 and 1 <= ny < self.size - 1 and self.maze[nx][ny] == 1:
                    self.maze[x+dx//2][y+dy//2] = 0
                    carve(nx, ny)

        carve(1, 1)
        for _ in range(self.size*2):
            self.maze[random.randint(1, self.size-2)][random.randint(1, self.size-2)] = 0

        self.exit = random.choice(list(self._reachable_cells((1, 1)) - {(1, 1)}))

    def _reachable_cells(self, start):
        """All open cells that can be walked to from start."""
        seen = {start}
        stack = [start]
        while stack:
            x, z = stack.pop()
            for dx, dz in [(-1,0), (1,0), (0,-1), (0,1)]:
                cell = (x+dx, z+dz)
                if self.maze[cell[0]][cell[1]] == 0 and cell not in seen:
                    seen.add(cell)
                    stack.append(cell)
        return seen

    def no_collision(self, nx, nz):
        if (self.maze[int(nx+0.1)][int(nz+0.1)] != 0 or self.maze[int(nx+0.1)][int(nz)] != 0 or
            self.maze[int(nx)][int(nz+0.1)] != 0 or self.maze[int(nx-0.1)][int(nz)] != 0 or
            self.maze[int(nx)][int(nz-0.1)] != 0 or self.maze[int(nx-0.1)][int(nz-0.1)] != 0):
            return 0
        return 1


class MazeAgent:
    def __init__(self, maze, speed=1):
        self.pos = pr.Vector3(1.1, 0, 1.1)
        self.speed = speed
        self.done = False
        self.heatmap = [[0]*maze.size for _ in range(maze.size)]
        self.target_cell = (1,1)

    def _choose_next_cell(self, maze):
        min_heat, x, z = 99999, int(self.pos.x), int(self.pos.z)
        for dx, dz in random.sample([(-1,0), (1,0), (0,-1), (0,1)], 4):
            nx, nz = x+dx, z+dz
            if maze.maze[nx][nz] == 0:
                if self.heatmap[nx][nz] < min_heat:
                    min_heat = self.heatmap[nx][nz]
                    position = (nx, nz)
                if maze.exit == (nx, nz):
                    return (nx, nz)
        return position

    def update(self, maze):
        if self.done: return

        dx, dz = self.target_cell[0] + 0.5 - self.pos.x, self.target_cell[1] + 0.5 - self.pos.z
        dist2 = dx*dx + dz*dz

        if dist2 < 0.0005:
            self.heatmap[self.target_cell[0]][self.target_cell[1]] +=1
            if self.target_cell == maze.exit:
                self.done = True
            else:
                self.target_cell = self._choose_next_cell(maze)

        dist = math.sqrt(dist2+1e-16)
        step = min(pr.get_frame_time() * self.speed, dist)  # never overshoot the cell center
        nx, nz = self.pos.x + dx*step/dist, self.pos.z + dz*step/dist
        if maze.no_collision(nx, self.pos.z):
            self.pos.x = nx
        if maze.no_collision(self.pos.x, nz):
            self.pos.z = nz


def draw_cube_wires_thick(center, w, h, d, t, color):
    """Cube wireframe made of 12 thin bars, each t units thick."""
    cx, cy, cz = center
    hw, hh, hd = w/2, h/2, d/2
    for sx in (-hw, hw):          # 4 vertical edges
        for sz in (-hd, hd):
            pr.draw_cube((cx+sx, cy, cz+sz), t, h, t, color)
    for sy in (-hh, hh):          # 4 edges along X, top and bottom
        for sz in (-hd, hd):
            pr.draw_cube((cx, cy+sy, cz+sz), w, t, t, color)
    for sx in (-hw, hw):          # 4 edges along Z, top and bottom
        for sy in (-hh, hh):
            pr.draw_cube((cx+sx, cy+sy, cz), t, t, d, color)

main()
