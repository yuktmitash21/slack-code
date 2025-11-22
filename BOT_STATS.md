# Bot Statistics

Total Tasks: 1
Last Updated: 2025-11-22 15:47:08

## Task History
- [2025-11-22 15:47:08] user: create a file called snake.html that implements a javascript snake

assistant: ━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **CHANGESET SUMMARY**
Create a simple HTML file that implements a basic JavaScript Snake game

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 **File: snake.html** [NEW]

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snake Game</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #f4f4f9;
            margin: 0;
        }
        canvas {
            border: 1px solid #000;
        }
    </style>
</head>
<body>
    <canvas id="gameCanvas" width="400" height="400"></canvas>
    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');

        const box = 20;
        let snake = [];
        snake[0] = { x: 9 * box, y: 10 * box };

        let food = {
            x: Math.floor(Math.random() * 19 + 1) * box,
            y: Math.floor(Math.random() * 19 + 1) * box
        };

        let score = 0;
        let d;

        document.addEventListener('keydown', direction);

        function direction(event) {
            if (event.keyCode === 37 && d !== "RIGHT") {
                d = "LEFT";
            } else if (event.keyCode === 38 && d !== "DOWN") {
                d = "UP";
            } else if (event.keyCode === 39 && d !== "LEFT") {
                d = "RIGHT";
            } else if (event.keyCode === 40 && d !== "UP") {
                d = "DOWN";
            }
        }

        function collision(newHead, snake) {
            for (let i = 0; i < snake.length; i++) {
                if (newHead.x === snake[i].x && newHead.y === snake[i].y) {
                    return true;
                }
            }
            return false;
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            for (let i = 0; i < snake.length; i++) {
                ctx.fillStyle = (i === 0) ? "green" : "white";
                ctx.fillRect(snake[i].x, snake[i].y, box, box);
                ctx.strokeStyle = "red";
                ctx.strokeRect(snake[i].x, snake[i].y, box, box);
            }

            ctx.fillStyle = "red";
            ctx.fillRect(food.x, food.y, box, box);

            let snakeX = snake[0].x;
            let snakeY = snake[0].y;

            if (d === "LEFT") snakeX -= box;
            if (d === "UP") snakeY -= box;
            if (d === "RIGHT") snakeX += box;
            if (d === "DOWN") snakeY += box;

            if (snakeX === food.x && snakeY === food.y) {
                score++;
                food = {
                    x: Math.floor(Math.random() * 19 + 1) * box,
                    y: Math.floor(Math.random() * 19 + 1) * box
                };
            } else {
                snake.pop();
            }

            let newHead = {
                x: snakeX,
                y: snakeY
            };

            if (snakeX < 0 || snakeY < 0 || snakeX >= 20 * box || snakeY >= 20 * box || collision(newHead, snake)) {
                clearInterval(game);
            }

            snake.unshift(newHead);

            ctx.fillStyle = "white";
            ctx.font = "45px Changa one";
            ctx.fillText(score, 2 * box, 1.6 * box);
        }

        let game = setInterval(draw, 100);
    </script>
</body>
</html>
```

━━━━━━━━━━━━━━━━━━━━━━━━━━

This changeset creates a new HTML file that implements a basic version of the classic Snake game using JavaScript and the HTML5 Canvas API. The game includes simple controls via arrow keys and basic collision detection.

---
*This file is automatically maintained by the Slack bot.*
