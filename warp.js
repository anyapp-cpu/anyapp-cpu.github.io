// Local warp and pixelation follow the cursor. The original image is the fallback.
(() => {
  const portrait = document.querySelector('[data-warp]');
  const canvas = portrait?.querySelector('canvas');
  const image = portrait?.querySelector('img');
  if (!canvas || !image) return;

  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const finePointer = matchMedia('(hover: hover) and (pointer: fine)');
  if (!finePointer.matches || reducedMotion.matches) return;

  const gl = canvas.getContext('webgl', { alpha: false, antialias: false, depth: false, preserveDrawingBuffer: false });
  if (!gl) return;

  const vertexSource = `
    attribute vec2 a_position;
    varying vec2 v_uv;
    void main() {
      v_uv = a_position * 0.5 + 0.5;
      gl_Position = vec4(a_position, 0.0, 1.0);
    }
  `;

  const fragmentSource = `
    precision mediump float;
    varying vec2 v_uv;
    uniform sampler2D u_photo;
    uniform vec2 u_cover;
    uniform vec2 u_size;
    uniform float u_aspect;
    uniform vec4 u_trail[16];
    uniform float u_pixels[16];

    void main() {
      vec2 offset = vec2(0.0);
      float pixelEnergy = 0.0;
      for (int i = 0; i < 16; i++) {
        vec2 delta = (v_uv - u_trail[i].xy) * vec2(u_aspect, 1.0);
        float distance = length(delta);
        float falloff = exp(-dot(delta, delta) * 30.0);
        vec2 velocity = u_trail[i].zw;
        float energy = length(velocity);
        pixelEnergy += falloff * u_pixels[i];
        // The photo bends locally in the direction of movement, then relaxes.
        offset -= velocity * falloff * 0.55;
        offset += delta / vec2(u_aspect, 1.0)
          * sin(distance * 23.0) * falloff * energy * 0.3;
      }
      offset = clamp(offset, vec2(-0.12), vec2(0.12));
      vec2 warped = v_uv + offset;
      // Keep the pixel grid square and 16 CSS pixels wide on every screen.
      vec2 grid = u_size / 16.0;
      vec2 pixelated = (floor(warped * grid) + 0.5) / grid;
      // Match the fallback's object-fit: cover and object-position: 50% 45%.
      vec2 origin = (1.0 - u_cover) * vec2(0.5, 0.55);
      vec2 uv = warped * u_cover + origin;
      vec2 pixelUv = pixelated * u_cover + origin;
      vec4 smoothColor = texture2D(u_photo, clamp(uv, 0.001, 0.999));
      vec4 pixelColor = texture2D(u_photo, clamp(pixelUv, 0.001, 0.999));
      // Pixelation fades independently, lingering after the warp has relaxed.
      float pixelAmount = smoothstep(0.003, 0.10, pixelEnergy);
      gl_FragColor = mix(smoothColor, pixelColor, pixelAmount);
    }
  `;

  const compile = (type, source) => {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      gl.deleteShader(shader);
      throw new Error('Photo shader could not compile.');
    }
    return shader;
  };

  let frame = 0;
  let visible = true;
  let ready = false;
  let previousTime = 0;
  let previousPointer = null;
  let pointerTime = 0;
  let cursor = 0;
  let program;
  let texture;
  let uniforms;
  const trail = new Float32Array(16 * 4);
  const pixels = new Float32Array(16);

  const allowed = () => visible && !document.hidden && !reducedMotion.matches && finePointer.matches;
  const render = () => {
    gl.useProgram(program);
    gl.uniform4fv(uniforms.trail, trail);
    gl.uniform1fv(uniforms.pixels, pixels);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
  };

  const tick = (now) => {
    frame = 0;
    if (!ready || !allowed()) return;
    const dt = previousTime ? Math.min((now - previousTime) / 1000, 0.05) : 1 / 60;
    previousTime = now;
    const decay = Math.exp(-dt * 5.5);
    const pixelDecay = Math.exp(-dt * 2.4);
    let energy = 0;
    for (let i = 0; i < 16; i++) {
      const index = i * 4;
      trail[index + 2] *= decay;
      trail[index + 3] *= decay;
      pixels[i] *= pixelDecay;
      energy += Math.abs(trail[index + 2]) + Math.abs(trail[index + 3]) + pixels[i];
    }
    if (energy < 0.0001) {
      trail.fill(0);
      pixels.fill(0);
    }
    render();
    if (energy >= 0.0001) frame = requestAnimationFrame(tick);
    else previousTime = 0;
  };

  const wake = () => {
    if (ready && allowed() && !frame) frame = requestAnimationFrame(tick);
  };

  const reset = () => {
    cancelAnimationFrame(frame);
    frame = 0;
    previousTime = 0;
    previousPointer = null;
    trail.fill(0);
    pixels.fill(0);
    if (ready && !gl.isContextLost()) render();
  };

  const resize = () => {
    if (!ready) return;
    const { width, height } = portrait.getBoundingClientRect();
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    gl.viewport(0, 0, canvas.width, canvas.height);
    const aspect = width / height;
    const imageAspect = image.naturalWidth / image.naturalHeight;
    gl.useProgram(program);
    gl.uniform1f(uniforms.aspect, aspect);
    gl.uniform2f(uniforms.size, width, height);
    gl.uniform2f(uniforms.cover, Math.min(aspect / imageAspect, 1), Math.min(imageAspect / aspect, 1));
    render();
  };

  const initialize = async () => {
    try {
      await image.decode();
      const vertex = compile(gl.VERTEX_SHADER, vertexSource);
      const fragment = compile(gl.FRAGMENT_SHADER, fragmentSource);
      program = gl.createProgram();
      gl.attachShader(program, vertex);
      gl.attachShader(program, fragment);
      gl.linkProgram(program);
      gl.deleteShader(vertex);
      gl.deleteShader(fragment);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error('Photo shader could not link.');
      gl.useProgram(program);

      const buffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);
      const position = gl.getAttribLocation(program, 'a_position');
      gl.enableVertexAttribArray(position);
      gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);
      uniforms = {
        trail: gl.getUniformLocation(program, 'u_trail[0]'),
        pixels: gl.getUniformLocation(program, 'u_pixels[0]'),
        cover: gl.getUniformLocation(program, 'u_cover'),
        aspect: gl.getUniformLocation(program, 'u_aspect'),
        size: gl.getUniformLocation(program, 'u_size'),
      };
      texture = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, image);
      ready = true;
      resize();
      portrait.classList.toggle('is-ready', allowed());
    } catch {
      ready = false;
      portrait.classList.remove('is-ready');
    }
  };

  portrait.addEventListener('pointermove', (event) => {
    if (!ready || !allowed() || event.pointerType === 'touch') return;
    const bounds = portrait.getBoundingClientRect();
    const point = { x: (event.clientX - bounds.left) / bounds.width, y: 1 - (event.clientY - bounds.top) / bounds.height };
    const now = performance.now();
    if (previousPointer) {
      const timeScale = Math.min(16 / Math.max(now - pointerTime, 8), 2);
      const dx = Math.max(-0.09, Math.min(0.09, (point.x - previousPointer.x) * timeScale));
      const dy = Math.max(-0.09, Math.min(0.09, (point.y - previousPointer.y) * timeScale));
      const index = cursor * 4;
      trail[index] = point.x;
      trail[index + 1] = point.y;
      trail[index + 2] = dx;
      trail[index + 3] = dy;
      pixels[cursor] = Math.hypot(dx, dy);
      cursor = (cursor + 1) % 16;
      wake();
    }
    previousPointer = point;
    pointerTime = now;
  }, { passive: true });
  portrait.addEventListener('pointerleave', () => { previousPointer = null; });

  new ResizeObserver(resize).observe(portrait);
  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    if (!visible) reset();
  }).observe(portrait);

  const updatePreference = () => {
    reset();
    portrait.classList.toggle('is-ready', ready && allowed());
  };
  reducedMotion.addEventListener('change', updatePreference);
  finePointer.addEventListener('change', updatePreference);
  document.addEventListener('visibilitychange', reset);
  canvas.addEventListener('webglcontextlost', (event) => {
    event.preventDefault();
    ready = false;
    reset();
    portrait.classList.remove('is-ready');
  });
  canvas.addEventListener('webglcontextrestored', initialize);
  initialize();
})();
