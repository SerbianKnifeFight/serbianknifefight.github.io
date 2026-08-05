const canvas = document.getElementById("bestagon");
const ctx = canvas.getContext("2d");
let w, h;
function resize() {
  w = canvas.width = window.innerWidth;
  h = canvas.height = window.innerHeight;
}
window.addEventListener("resize", resize);
resize();
const hexSize = 40;
const hexHeight = Math.sqrt(3) * hexSize;
let time = 0;
function drawHex(x, y, pulse) {
  ctx.beginPath();
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i;
    const px = x + (hexSize + pulse) * Math.cos(angle);
    const py = y + (hexSize + pulse) * Math.sin(angle);
    ctx.lineTo(px, py);
  }
  ctx.closePath();
  ctx.strokeStyle = `rgba(255, 255, 255, 0.15)`;
  ctx.stroke();
}
function animate() {
  ctx.clearRect(0, 0, w, h);
  let pulse = Math.sin(time * 0.02) * 5;
  for (let row = -1; row < h / (hexHeight * 0.75) + 2; row++) {
    for (let col = -1; col < w / hexSize + 2; col++) {
      let x = col * hexSize * 1.5;
      let y = row * hexHeight + (col % 2 ? hexHeight / 2 : 0);
      drawHex(x, y, pulse);
    }
  }
  time++;
  requestAnimationFrame(animate);
}
animate();