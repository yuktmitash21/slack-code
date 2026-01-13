const canvas = document.getElementById('pongCanvas');
const context = canvas.getContext('2d');

// Create the paddle
const paddleWidth = 10, paddleHeight = 100;
const player = { x: 0, y: canvas.height / 2 - paddleHeight / 2, width: paddleWidth, height: paddleHeight, color: 'white', dy: 4 };
const ai = { x: canvas.width - paddleWidth, y: canvas.height / 2 - paddleHeight / 2, width: paddleWidth, height: paddleHeight, color: 'white', dy: 4 };

// Create the ball
const ball = { x: canvas.width / 2, y: canvas.height / 2, radius: 10, speed: 4, dx: 4, dy: 4, color: 'white' };

// Draw everything
function drawRect(x, y, w, h, color) {
    context.fillStyle = color;
    context.fillRect(x, y, w, h);
}

function drawCircle(x, y, r, color) {
    context.fillStyle = color;
    context.beginPath();
    context.arc(x, y, r, 0, Math.PI * 2, false);
    context.closePath();
    context.fill();
}

function drawNet() {
    for (let i = 0; i <= canvas.height; i += 15) {
        drawRect(canvas.width / 2 - 1, i, 2, 10, 'white');
    }
}

function drawText(text, x, y) {
    context.fillStyle = 'white';
    context.font = '45px sans-serif';
    context.fillText(text, x, y);
}

// Control the player
document.addEventListener('keydown', function(event) {
    switch(event.keyCode) {
        case 38:
            player.y -= player.dy;
            break;
        case 40:
            player.y += player.dy;
            break;
    }
});

// Collision detection
function collision(b, p) {
    b.top = b.y - b.radius;
    b.bottom = b.y + b.radius;
    b.left = b.x - b.radius;
    b.right = b.x + b.radius;

    p.top = p.y;
    p.bottom = p.y + p.height;
    p.left = p.x;
    p.right = p.x + p.width;

    return b.right > p.left && b.bottom > p.top && b.left < p.right && b.top < p.bottom;
}

// Reset the ball
function resetBall() {
    ball.x = canvas.width / 2;
    ball.y = canvas.height / 2;
    ball.speed = 4;
    ball.dx = -ball.dx;
}

// Update the game
function update() {
    ball.x += ball.dx;
    ball.y += ball.dy;

    // AI paddle movement
    ai.y += (ball.y - (ai.y + ai.height / 2)) * 0.1;

    // Ball collision with top and bottom walls
    if (ball.y + ball.radius > canvas.height || ball.y - ball.radius < 0) {
        ball.dy = -ball.dy;
    }

    // Ball collision with paddles
    let playerOrAI = (ball.x < canvas.width / 2) ? player : ai;
    if (collision(ball, playerOrAI)) {
        let collidePoint = (ball.y - (playerOrAI.y + playerOrAI.height / 2));
        collidePoint = collidePoint / (playerOrAI.height / 2);
        let angleRad = (Math.PI / 4) * collidePoint;
        let direction = (ball.x < canvas.width / 2) ? 1 : -1;
        ball.dx = direction * ball.speed * Math.cos(angleRad);
        ball.dy = ball.speed * Math.sin(angleRad);
        ball.speed += 0.5;
    }

    // Ball goes to the left or right
    if (ball.x - ball.radius < 0) {
        resetBall();
    } else if (ball.x + ball.radius > canvas.width) {
        resetBall();
    }
}

// Render the game
function render() {
    drawRect(0, 0, canvas.width, canvas.height, 'black');
    drawNet();
    drawText('Player', canvas.width / 4, canvas.height / 5);
    drawText('AI', 3 * canvas.width / 4, canvas.height / 5);
    drawRect(player.x, player.y, player.width, player.height, player.color);
    drawRect(ai.x, ai.y, ai.width, ai.height, ai.color);
    drawCircle(ball.x, ball.y, ball.radius, ball.color);
}

// Game loop
function game() {
    update();
    render();
}

// Number of frames per second
const framePerSecond = 50;
setInterval(game, 1000 / framePerSecond);