const tocLinks = [...document.querySelectorAll('.case-toc a')];
const caseSections = tocLinks.map(link => document.querySelector(link.hash));
let readingScheduled = false;

function updateReading() {
  let current = caseSections[0];
  for (const section of caseSections) {
    if (section.getBoundingClientRect().top <= innerHeight * 0.35) current = section;
  }
  for (const link of tocLinks) {
    if (link.hash === `#${current.id}`) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }
  const available = document.documentElement.scrollHeight - innerHeight;
  const progress = available > 0 ? Math.max(0, Math.min(100, scrollY / available * 100)) : 0;
  document.documentElement.style.setProperty('--reading-progress', `${progress}%`);
  readingScheduled = false;
}
function scheduleReading() {
  if (!readingScheduled) {
    readingScheduled = true;
    requestAnimationFrame(updateReading);
  }
}
addEventListener('scroll', scheduleReading, { passive: true });
addEventListener('resize', scheduleReading);
addEventListener('pageshow', scheduleReading);
updateReading();

const imageDialog = document.querySelector('.pm-image-dialog');
const dialogImage = imageDialog.querySelector('img');
const dialogCaption = imageDialog.querySelector('figcaption');
for (const button of document.querySelectorAll('[data-zoom]')) {
  button.setAttribute('aria-label', `Увеличить макет: ${button.dataset.caption}`);
  button.addEventListener('click', () => {
    const original = button.querySelector('img');
    dialogImage.src = button.dataset.zoom;
    dialogImage.alt = original.alt;
    imageDialog.classList.toggle('is-detail', original.width < original.height);
    dialogCaption.textContent = button.dataset.caption;
    imageDialog.showModal();
    imageDialog.scrollTop = 0;
  });
}
imageDialog.querySelector('.dialog-close').addEventListener('click', () => imageDialog.close());
imageDialog.addEventListener('click', event => {
  if (event.target !== imageDialog) return;
  const box = imageDialog.getBoundingClientRect();
  if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) imageDialog.close();
});
imageDialog.addEventListener('close', () => syncAllVideos());
imageDialog.addEventListener('toggle', () => syncAllVideos());

// Native muted autoplay owns playback. Scrolling never pauses a demo.
// Visibility and intersection events only retry playback after browser suspension.
const videoDialog = document.querySelector('.pm-video-dialog');
const expandedFrame = videoDialog.querySelector('.pm-expanded-frame');
let expandedDemo = null;
const demos = [...document.querySelectorAll('[data-demo]')].map(figure => ({
  figure,
  frame: figure.querySelector('.pm-video-frame'),
  mount: figure.querySelector('.pm-phone-display') || figure.querySelector('.pm-video-frame'),
  video: figure.querySelector('video'),
  button: figure.querySelector('[data-play]'),
  label: figure.dataset.label,
  userPaused: false,
  internalPause: false,
  nativeInteractionUntil: 0,
  triedFallback: false,
  starting: false,
}));

function showPlaybackState(demo) {
  const failed = Boolean(demo.video.error);
  const paused = demo.video.paused;
  demo.button.textContent = failed ? 'Повторить' : paused ? 'Смотреть ▷' : 'Пауза Ⅱ';
  demo.button.dataset.action = failed || paused ? 'play' : 'pause';
  demo.button.setAttribute('aria-label', `${failed ? 'Повторить загрузку' : paused ? 'Запустить' : 'Приостановить'} видео: ${demo.label}`);
}
function pauseVideo(demo) {
  if (demo.video.paused) return;
  demo.internalPause = true;
  demo.video.pause();
}
function playVideo(demo) {
  if (demo.starting || demo.video.error) return;
  demo.video.muted = true;
  demo.video.defaultMuted = true;
  demo.starting = true;
  demo.video.play().then(() => {
    demo.figure.querySelector('.pm-video-error')?.remove();
  }).catch(() => {
    // Keep native controls usable if the browser requires a user gesture.
  }).finally(() => {
    demo.starting = false;
    showPlaybackState(demo);
  });
}
function syncVideo(demo) {
  if (demo.userPaused || imageDialog.open || (expandedDemo && expandedDemo !== demo)) return;
  if (demo.video.paused) playVideo(demo);
}
function syncAllVideos() { demos.forEach(syncVideo); }

const videoObserver = new IntersectionObserver(entries => {
  for (const entry of entries) {
    if (entry.isIntersecting) syncVideo(demos.find(demo => demo.frame === entry.target));
  }
});
for (const demo of demos) {
  const video = demo.video;
  video.muted = true;
  video.defaultMuted = true;
  video.playsInline = true;
  video.autoplay = true;
  video.controls = true;
  videoObserver.observe(demo.frame);
  for (const event of ['loadeddata', 'canplay']) video.addEventListener(event, () => {
    if (!video.error) demo.figure.querySelector('.pm-video-error')?.remove();
    syncVideo(demo);
  });
  video.addEventListener('pointerdown', () => { demo.nativeInteractionUntil = performance.now() + 1500; });
  video.addEventListener('keydown', () => { demo.nativeInteractionUntil = performance.now() + 1500; });
  video.addEventListener('play', () => {
    demo.userPaused = false;
    showPlaybackState(demo);
  });
  video.addEventListener('pause', () => {
    if (!demo.internalPause && performance.now() < demo.nativeInteractionUntil) demo.userPaused = true;
    demo.internalPause = false;
    showPlaybackState(demo);
  });
  video.addEventListener('error', () => {
    const alternate = video.querySelector('source[type="video/webm"]');
    if (!demo.triedFallback && alternate) {
      demo.triedFallback = true;
      demo.starting = false;
      video.src = alternate.src;
      video.load();
      playVideo(demo);
      return;
    }
    if (!demo.figure.querySelector('.pm-video-error')) {
      const message = document.createElement('span');
      message.className = 'pm-video-error';
      message.setAttribute('role', 'status');
      message.textContent = 'Не удалось загрузить видео.';
      demo.figure.querySelector('.pm-demo-footer').prepend(message);
    }
    showPlaybackState(demo);
  });
  demo.button.addEventListener('click', () => {
    if (!video.paused && !video.error) {
      demo.userPaused = true;
      pauseVideo(demo);
    } else {
      demo.userPaused = false;
      if (video.error) {
        demo.triedFallback = false;
        demo.starting = false;
        video.removeAttribute('src');
        video.load();
      }
      playVideo(demo);
    }
    showPlaybackState(demo);
  });
  demo.figure.querySelector('[data-fullscreen]').addEventListener('click', () => {
    expandedDemo = demo;
    demo.userPaused = false;
    videoDialog.querySelector('.pm-video-dialog-top p').textContent = demo.label;
    videoDialog.classList.toggle('is-phone', demo.figure.dataset.demo === 'bot');
    expandedFrame.style.setProperty('--video-ratio', demo.figure.dataset.ratio);
    videoDialog.showModal();
    expandedFrame.append(video);
    for (const other of demos) if (other !== demo) pauseVideo(other);
    playVideo(demo);
  });
  showPlaybackState(demo);
}
videoDialog.querySelector('.pm-video-close').addEventListener('click', () => videoDialog.close());
videoDialog.addEventListener('close', () => {
  if (!expandedDemo) return;
  const demo = expandedDemo;
  expandedDemo = null;
  demo.mount.append(demo.video);
  syncAllVideos();
});
videoDialog.addEventListener('click', event => {
  if (event.target !== videoDialog) return;
  const box = videoDialog.getBoundingClientRect();
  if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) videoDialog.close();
});
document.addEventListener('visibilitychange', syncAllVideos);
addEventListener('pageshow', syncAllVideos);
addEventListener('focus', syncAllVideos);
// Recover autoplay after an embedded browser suspends and restores its renderer.
setInterval(syncAllVideos, 1000);
syncAllVideos();
