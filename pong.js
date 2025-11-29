const canvas = document.getElementById('pongCanvas');
const ctx = canvas.getContext('2d');

const paddleWidth = 10;
const paddleHeight = 100;
const ballRadius = 10;

let playerPaddleY = (canvas.height - paddleHeight) / 2;
let aiPaddleY = (canvas.height - paddleHeight) / 2;
let ballX = canvas.width / 2;
let ballY = canvas.height / 2;
let ballSpeedX = 5;
let ballSpeedY = 5;

function drawNet() {
    for (let i = 0; i < canvas.height; i += 40) {
        ctx.fillStyle = '#fff';
        ctx.fillRect(canvas.width / 2 - 1, i, 2, 20);
    }
}

function drawPaddle(x, y) {
    ctx.fillStyle = '#fff';
    ctx.fillRect(x, y, paddleWidth, paddleHeight);
}

function drawBall() {
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(ballX, ballY, ballRadius, 0, Math.PI * 2);
    ctx.fill();
    ctx.closePath();
}

function moveBall() {
    ballX += ballSpeedX;
    ballY += ballSpeedY;

    // Ball collision with top and bottom
    if (ballY + ballRadius > canvas.height || ballY - ballRadius < 0) {
        ballSpeedY = -ballSpeedY;
    }

    // Ball collision with left and right
    if (ballX - ballRadius < 0 || ballX + ballRadius > canvas.width) {
        ballSpeedX = -ballSpeedX;
        resetBall();
    }
}

function resetBall() {
    ballX = canvas.width / 2;
    ballY = canvas.height / 2;
    ballSpeedX = -ballSpeedX;
}

function moveAiPaddle() {
    const centerY = aiPaddleY + paddleHeight / 2;
    if (centerY < ballY - 35) {
        aiPaddleY += 6;
    } else if (centerY > ballY + 35) {
        aiPaddleY -= 6;
    }
}

function update() {
    moveBall();
    moveAiPaddle();
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawNet();
    drawPaddle(0, playerPaddleY); // Player paddle
    drawPaddle(canvas.width - paddleWidth, aiPaddleY); // AI paddle
    drawBall();
}

function gameLoop() {
    update();
    draw();
    requestAnimationFrame(gameLoop);
}

canvas.addEventListener('mousemove', function(event) {
    const rect = canvas.getBoundingClientRect();
    playerPaddleY = event.clientY - rect.top - paddleHeight / 2;
});

gameLoop();