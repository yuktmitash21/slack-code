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

// Listen for key press events to control the snake
document.addEventListener('keydown', direction);

function direction(event) {
    if (event.keyCode == 37 && d != "RIGHT") {
        d = "LEFT";
    } else if (event.keyCode == 38 && d != "DOWN") {
        d = "UP";
    } else if (event.keyCode == 39 && d != "LEFT") {
        d = "RIGHT";
    } else if (event.keyCode == 40 && d != "UP") {
        d = "DOWN";
    }
}

// Check for collisions within the snake's body
function collision(newHead, array) {
    for (let i = 0; i < array.length; i++) {
        if (newHead.x == array[i].x && newHead.y == array[i].y) {
            return true;
        }
    }
    return false;
}

// Main function to draw the game elements
function draw() {
    // Clear the canvas for the next frame
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw the snake
    for (let i = 0; i < snake.length; i++) {
        ctx.fillStyle = (i == 0) ? "green" : "white";
        ctx.fillRect(snake[i].x, snake[i].y, box, box);
        ctx.strokeStyle = "red";
        ctx.strokeRect(snake[i].x, snake[i].y, box, box);
    }

    // Draw the food
    ctx.fillStyle = "red";
    ctx.fillRect(food.x, food.y, box, box);

    // Current position of the snake's head
    let snakeX = snake[0].x;
    let snakeY = snake[0].y;

    // Move the snake in the current direction
    if (d == "LEFT") snakeX -= box;
    if (d == "UP") snakeY -= box;
    if (d == "RIGHT") snakeX += box;
    if (d == "DOWN") snakeY += box;

    // Check if the snake eats the food
    if (snakeX == food.x && snakeY == food.y) {
        score++;
        food = {
            x: Math.floor(Math.random() * 19 + 1) * box,
            y: Math.floor(Math.random() * 19 + 1) * box
        };
    } else {
        // Remove the tail of the snake
        snake.pop();
    }

    // Create new head for the snake
    let newHead = {
        x: snakeX,
        y: snakeY
    };

    // Check for collision with walls or itself
    if (snakeX < 0 || snakeY < 0 || snakeX >= 20 * box || snakeY >= 20 * box || collision(newHead, snake)) {
        clearInterval(game);
    }

    // Add new head to the snake
    snake.unshift(newHead);

    // Display the score
    ctx.fillStyle = "white";
    ctx.font = "45px Changa one";
    ctx.fillText(score, 2 * box, 1.6 * box);
}

// Set the game to run the draw function every 100 milliseconds
let game = setInterval(draw, 100);