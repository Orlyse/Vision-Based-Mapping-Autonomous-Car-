def draw_maze(commands):
    """
    Draw a 2D ASCII maze from a list of commands in {-1, 0, 1}.

      1  -> move forward
      0  -> turn left, then move forward
     -1  -> turn right, then move forward

    Start at (0,0) facing RIGHT.
    - Horizontal segments: '_'
    - Vertical segments:   '|'
    - If both meet in one cell: '+'
    - Start and end: 'S' and 'E'
    """

    # directions: 0=up, 1=right, 2=down, 3=left
    dirs = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    heading = 1          # 🔹 start facing RIGHT

    x = y = 0
    start_pos = (x, y)
    end_pos = start_pos

    vertical = set()
    horizontal = set()

    min_x = max_x = x
    min_y = max_y = y

    for cmd in commands:
        # update heading
        if cmd == 0:        # turn left
            heading = (heading - 1) % 4
        elif cmd == -1:     # turn right
            heading = (heading + 1) % 4
        # cmd == 1 -> straight

        dx, dy = dirs[heading]

        # move one step along the path
        x += dx
        y += dy

        # mark that step as horizontal or vertical
        if dx == 0:
            vertical.add((x, y))
        else:
            horizontal.add((x, y))

        # update bounds
        min_x = min(min_x, x)
        max_x = max(max_x, x)
        min_y = min(min_y, y)
        max_y = max(max_y, y)

        end_pos = (x, y)

    # grid size
    width  = max_x - min_x + 1
    height = max_y - min_y + 1

    grid = [[' ' for _ in range(width)] for _ in range(height)]

    def put(px, py, ch):
        cx = px - min_x
        cy = py - min_y
        if 0 <= cx < width and 0 <= cy < height:
            grid[cy][cx] = ch

    # draw segments
    all_cells = vertical | horizontal
    for cx, cy in all_cells:
        v = (cx, cy) in vertical
        h = (cx, cy) in horizontal
        if v and h:
            ch = '+'        # intersection / sharp corner
        elif v:
            ch = '|'
        else:
            ch = '_'
        put(cx, cy, ch)

    # mark start and end
    sx, sy = start_pos
    ex, ey = end_pos
    put(sx, sy, 'S')
    put(ex, ey, 'E')

    # print maze
    for row in grid:
        print(''.join(row))
