const canvas = document.getElementById('pongCanvas');
const context = canvas.getContext('2d');

let paddleWidth = 10, paddleHeight = 100;
let player = { x: 0, y: canvas.height / 2 - paddleHeight / 2, width: paddleWidth, height: paddleHeight, dy: 0 };
let computer = { x: canvas.width - paddleWidth, y: canvas.height / 2 - paddleHeight / 2, width: paddleWidth, height: paddleHeight, dy: 0 };
let ball = { x: canvas.width / 2, y: canvas.height / 2, radius: 10, dx: 5, dy: 4 };

function drawRect(x, y, width, height, color) {
    context.fillStyle = color;
    context.fillRect(x, y, width, height);
}

function drawBall(x, y, radius, color) {
    context.fillStyle = color;
    context.beginPath();
    context.arc(x, y, radius, 0, Math.PI * 2);
    context.fill();
}

function movePaddle(paddle) {
    paddle.y += paddle.dy;
    if (paddle.y < 0) paddle.y = 0;
    if (paddle.y + paddle.height > canvas.height) paddle.y = canvas.height - paddle.height;
}

function moveBall() {
    ball.x += ball.dx;
    ball.y += ball.dy;

    // Ball collision with top and bottom walls
    if (ball.y + ball.radius > canvas.height || ball.y - ball.radius < 0) {
        ball.dy *= -1;
        console.log('Ball hit the wall');
    }

    // Ball collision with paddles
    if (
        (ball.x - ball.radius < player.x + player.width && ball.y > player.y && ball.y < player.y + player.height) ||
        (ball.x + ball.radius > computer.x && ball.y > computer.y && ball.y < computer.y + computer.height)
    ) {
        ball.dx *= -1;
        console.log('Ball hit the paddle');
    }

    // Ball out of bounds
    if (ball.x - ball.radius < 0 || ball.x + ball.radius > canvas.width) {
        resetBall();
        console.log('Ball out of bounds');
    }
}

function resetBall() {
    ball.x = canvas.width / 2;
    ball.y = canvas.height / 2;
    ball.dx = -ball.dx;
}

function update() {
    movePaddle(player);
    movePaddle(computer);
    moveBall();
}

function draw() {
    drawRect(0, 0, canvas.width, canvas.height, '#000');
    drawRect(player.x, player.y, player.width, player.height, '#00ff00');
    drawRect(computer.x, computer.y, computer.width, computer.height, '#ff0000');
    drawBall(ball.x, ball.y, ball.radius, '#ffffff');
}

function gameLoop() {
    update();
    draw();
    requestAnimationFrame(gameLoop);
}

document.addEventListener('keydown', event => {
    if (event.key === 'ArrowUp') player.dy = -5;
    if (event.key === 'ArrowDown') player.dy = 5;
    console.log('Key down:', event.key);
});

document.addEventListener('keyup', event => {
    if (event.key === 'ArrowUp' || event.key === 'ArrowDown') player.dy = 0;
    console.log('Key up:', event.key);
});

gameLoop();