<div align="center">

<style>
  .pixel-perro-canvas {
    display: grid;
    grid-template-columns: repeat(16, 14px);
    gap: 2px;
    padding: 15px;
    background: #161b22;
    border-radius: 10px;
    width: max-content;
    margin: 20px auto;
  }
  .px {
    width: 14px;
    height: 14px;
    background-color: transparent;
    border-radius: 2px;
    animation: aparecer 0.8s ease forwards;
    animation-play-state: paused;
    animation-delay: var(--d);
  }
  .c-brown { background-color: #8D5524; }
  .c-light { background-color: #C68642; }
  .c-white { background-color: #F0E6D2; }
  .c-black { background-color: #212121; }
  .c-pink  { background-color: #FF7675; }

  @keyframes aparecer {
    to { background-color: var(--c); }
  }
</style>

<div class="pixel-perro-canvas" style="animation: playAnim 0.1s forwards;">
  <style>
    @keyframes playAnim {
      to { --dummy: 0; }
    }
    .pixel-perro-canvas .px { animation-play-state: running; }
  </style>

  <!-- Fila 1 -->
  <span class="px" style="--d:0.1s; --c:transparent"></span><span class="px" style="--d:0.1s; --c:transparent"></span><span class="px" style="--d:0.1s; --c:#8D5524"></span><span class="px" style="--d:0.1s; --c:#8D5524"></span><span class="px" style="--d:0.1s; --c:transparent"></span><span class="px" style="--d:0.1s; --c:transparent"></span><span class="px" style="--d:0.1s; --c:transparent"></span><span class="px" style="--d:0.1s; --c:transparent"></span><span class="px" style="--d:0.1s; --c:transparent"></span><span class="px" style="--d:0.1s; --c:transparent"></span><span class="px" style="--d:0.1s; --c:#8D5524"></span><span class="px" style="--d:0.1s; --c:#8D5524"></span><span class="px" style="--d:0.1s; --c:transparent"></span><span class="px" style="--d:0.1s; --c:transparent"></span><span class="px" style="--d:0.1s; --c:transparent"></span><span class="px" style="--d:0.1s; --c:transparent"></span>
  <!-- Fila 2 -->
  <span class="px" style="--d:0.2s; --c:transparent"></span><span class="px" style="--d:0.2s; --c:#8D5524"></span><span class="px" style="--d:0.2s; --c:#C68642"></span><span class="px" style="--d:0.2s; --c:#C68642"></span><span class="px" style="--d:0.2s; --c:#8D5524"></span><span class="px" style="--d:0.2s; --c:transparent"></span><span class="px" style="--d:0.2s; --c:transparent"></span><span class="px" style="--d:0.2s; --c:transparent"></span><span class="px" style="--d:0.2s; --c:transparent"></span><span class="px" style="--d:0.2s; --c:#8D5524"></span><span class="px" style="--d:0.2s; --c:#C68642"></span><span class="px" style="--d:0.2s; --c:#C68642"></span><span class="px" style="--d:0.2s; --c:#8D5524"></span><span class="px" style="--d:0.2s; --c:transparent"></span><span class="px" style="--d:0.2s; --c:transparent"></span><span class="px" style="--d:0.2s; --c:transparent"></span>
  <!-- Fila 3 -->
  <span class="px" style="--d:0.3s; --c:#8D5524"></span><span class="px" style="--d:0.3s; --c:#C68642"></span><span class="px" style="--d:0.3s; --c:#F0E6D2"></span><span class="px" style="--d:0.3s; --c:#F0E6D2"></span><span class="px" style="--d:0.3s; --c:#C68642"></span><span class="px" style="--d:0.3s; --c:#8D5524"></span><span class="px" style="--d:0.3s; --c:transparent"></span><span class="px" style="--d:0.3s; --c:transparent"></span><span class="px" style="--d:0.3s; --c:#8D5524"></span><span class="px" style="--d:0.3s; --c:#C68642"></span><span class="px" style="--d:0.3s; --c:#F0E6D2"></span><span class="px" style="--d:0.3s; --c:#F0E6D2"></span><span class="px" style="--d:0.3s; --c:#C68642"></span><span class="px" style="--d:0.3s; --c:#8D5524"></span><span class="px" style="--d:0.3s; --c:transparent"></span><span class="px" style="--d:0.3s; --c:transparent"></span>
  <!-- Fila 4 -->
  <span class="px" style="--d:0.4s; --c:#8D5524"></span><span class="px" style="--d:0.4s; --c:#C68642"></span><span class="px" style="--d:0.4s; --c:#F0E6D2"></span><span class="px" style="--d:0.4s; --c:#F0E6D2"></span><span class="px" style="--d:0.4s; --c:#C68642"></span><span class="px" style="--d:0.4s; --c:#8D5524"></span><span class="px" style="--d:0.4s; --c:#8D5524"></span><span class="px" style="--d:0.4s; --c:#8D5524"></span><span class="px" style="--d:0.4s; --c:#8D5524"></span><span class="px" style="--d:0.4s; --c:#8D5524"></span><span class="px" style="--d:0.4s; --c:#C68642"></span><span class="px" style="--d:0.4s; --c:#F0E6D2"></span><span class="px" style="--d:0.4s; --c:#F0E6D2"></span><span class="px" style="--d:0.4s; --c:#C68642"></span><span class="px" style="--d:0.4s; --c:#8D5524"></span><span class="px" style="--d:0.4s; --c:transparent"></span>
  <!-- Fila 5 -->
  <span class="px" style="--d:0.5s; --c:transparent"></span><span class="px" style="--d:0.5s; --c:#8D5524"></span><span class="px" style="--d:0.5s; --c:#C68642"></span><span class="px" style="--d:0.5s; --c:#C68642"></span><span class="px" style="--d:0.5s; --c:#C68642"></span><span class="px" style="--d:0.5s; --c:#212121"></span><span class="px" style="--d:0.5s; --c:#C68642"></span><span class="px" style="--d:0.5s; --c:#C68642"></span><span class="px" style="--d:0.5s; --c:#C68642"></span><span class="px" style="--d:0.5s; --c:#C68642"></span><span class="px" style="--d:0.5s; --c:#212121"></span><span class="px" style="--d:0.5s; --c:#C68642"></span><span class="px" style="--d:0.5s; --c:#C68642"></span><span class="px" style="--d:0.5s; --c:#C68642"></span><span class="px" style="--d:0.5s; --c:#8D5524"></span><span class="px" style="--d:0.5s; --c:transparent"></span>
  <!-- Fila 6 -->
  <span class="px" style="--d:0.6s; --c:transparent"></span><span class="px" style="--d:0.6s; --c:transparent"></span><span class="px" style="--d:0.6s; --c:#8D5524"></span><span class="px" style="--d:0.6s; --c:#C68642"></span><span class="px" style="--d:0.6s; --c:#C68642"></span><span class="px" style="--d:0.6s; --c:#C68642"></span><span class="px" style="--d:0.6s; --c:#C68642"></span><span class="px" style="--d:0.6s; --c:#C68642"></span><span class="px" style="--d:0.6s; --c:#C68642"></span><span class="px" style="--d:0.6s; --c:#C68642"></span><span class="px" style="--d:0.6s; --c:#C68642"></span><span class="px" style="--d:0.6s; --c:#C68642"></span><span class="px" style="--d:0.6s; --c:#C68642"></span><span class="px" style="--d:0.6s; --c:#8D5524"></span><span class="px" style="--d:0.6s; --c:transparent"></span><span class="px" style="--d:0.6s; --c:transparent"></span>
  <!-- Fila 7 -->
  <span class="px" style="--d:0.7s; --c:transparent"></span><span class="px" style="--d:0.7s; --c:transparent"></span><span class="px" style="--d:0.7s; --c:transparent"></span><span class="px" style="--d:0.7s; --c:#8D5524"></span><span class="px" style="--d:0.7s; --c:#8D5524"></span><span class="px" style="--d:0.7s; --c:#FF7675"></span><span class="px" style="--d:0.7s; --c:#8D5524"></span><span class="px" style="--d:0.7s; --c:#8D5524"></span><span class="px" style="--d:0.7s; --c:#8D5524"></span><span class="px" style="--d:0.7s; --c:#8D5524"></span><span class="px" style="--d:0.7s; --c:#FF7675"></span><span class="px" style="--d:0.7s; --c:#8D5524"></span><span class="px" style="--d:0.7s; --c:#8D5524"></span><span class="px" style="--d:0.7s; --c:transparent"></span><span class="px" style="--d:0.7s; --c:transparent"></span><span class="px" style="--d:0.7s; --c:transparent"></span>
  <!-- Fila 8 -->
  <span class="px" style="--d:0.8s; --c:transparent"></span><span class="px" style="--d:0.8s; --c:transparent"></span><span class="px" style="--d:0.8s; --c:transparent"></span><span class="px" style="--d:0.8s; --c:transparent"></span><span class="px" style="--d:0.8s; --c:#8D5524"></span><span class="px" style="--d:0.8s; --c:#8D5524"></span><span class="px" style="--d:0.8s; --c:#212121"></span><span class="px" style="--d:0.8s; --c:#8D5524"></span><span class="px" style="--d:0.8s; --c:#8D5524"></span><span class="px" style="--d:0.8s; --c:#212121"></span><span class="px" style="--d:0.8s; --c:#8D5524"></span><span class="px" style="--d:0.8s; --c:#8D5524"></span><span class="px" style="--d:0.8s; --c:transparent"></span><span class="px" style="--d:0.8s; --c:transparent"></span><span class="px" style="--d:0.8s; --c:transparent"></span><span class="px" style="--d:0.8s; --c:transparent"></span>
  <!-- Fila 9 -->
  <span class="px" style="--d:0.9s; --c:transparent"></span><span class="px" style="--d:0.9s; --c:transparent"></span><span class="px" style="--d:0.9s; --c:transparent"></span><span class="px" style="--d:0.9s; --c:transparent"></span><span class="px" style="--d:0.9s; --c:transparent"></span><span class="px" style="--d:0.9s; --c:#8D5524"></span><span class="px" style="--d:0.9s; --c:#8D5524"></span><span class="px" style="--d:0.9s; --c:#212121"></span><span class="px" style="--d:0.9s; --c:#212121"></span><span class="px" style="--d:0.9s; --c:#8D5524"></span><span class="px" style="--d:0.9s; --c:#8D5524"></span><span class="px" style="--d:0.9s; --c:transparent"></span><span class="px" style="--d:0.9s; --c:transparent"></span><span class="px" style="--d:0.9s; --c:transparent"></span><span class="px" style="--d:0.9s; --c:transparent"></span><span class="px" style="--d:0.9s; --c:transparent"></span>

</div>

</div>