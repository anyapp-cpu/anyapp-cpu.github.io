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

const imageDialog = document.querySelector('.wb-image-dialog');
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

const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const videoDialog = document.querySelector('.wb-video-dialog');
const expandedFrame = videoDialog.querySelector('.wb-expanded-frame');
let expandedDemo = null;
const demos = [...document.querySelectorAll('[data-demo]')].map(figure => ({
  figure,
  frame: figure.querySelector('.wb-video-frame'),
  video: figure.querySelector('video'),
  button: figure.querySelector('[data-play]'),
  label: figure.querySelector('.wb-demo-top>span').textContent.split(' / ')[1],
  inView: false,
  manual: null,
}));

function loadVideo(demo) {
  if (demo.video.getAttribute('src')) return;
  demo.video.src = demo.video.dataset.src;
  demo.video.load();
}
function showPlaybackState(demo) {
  const paused = demo.video.paused;
  demo.button.innerHTML = paused ? 'Смотреть <span aria-hidden="true">▷</span>' : 'Пауза <span aria-hidden="true">Ⅱ</span>';
  demo.button.setAttribute('aria-label', `${paused ? 'Запустить' : 'Приостановить'} видео: ${demo.label}`);
}
function syncVideo(demo) {
  const shouldPlay = (demo.inView || expandedDemo === demo) &&
    (!expandedDemo || expandedDemo === demo) && !document.hidden && !imageDialog.open &&
    demo.manual !== 'paused' && (!reducedMotion.matches || demo.manual === 'playing');
  if (shouldPlay) {
    loadVideo(demo);
    demo.video.muted = true;
    demo.video.play().catch(() => {
      // Keep a readable poster and a manual play action if autoplay is blocked.
      showPlaybackState(demo);
    });
  } else demo.video.pause();
  showPlaybackState(demo);
}
function syncAllVideos() { demos.forEach(syncVideo); }
videoDialog.querySelector('.wb-video-close').addEventListener('click', () => videoDialog.close());
videoDialog.addEventListener('close', () => {
  if (!expandedDemo) return;
  const demo = expandedDemo;
  expandedDemo = null;
  demo.video.controls = false;
  demo.frame.append(demo.video);
  syncAllVideos();
});
videoDialog.addEventListener('click', event => {
  if (event.target !== videoDialog) return;
  const box = videoDialog.getBoundingClientRect();
  if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) videoDialog.close();
});

const loadObserver = new IntersectionObserver(entries => {
  for (const entry of entries) {
    if (!entry.isIntersecting) continue;
    const demo = demos.find(item => item.video === entry.target);
    if (!reducedMotion.matches) loadVideo(demo);
  }
}, { rootMargin: '350px 0px' });
const playObserver = new IntersectionObserver(entries => {
  for (const entry of entries) {
    const demo = demos.find(item => item.video === entry.target);
    demo.inView = entry.isIntersecting && entry.intersectionRatio >= 0.2;
    syncVideo(demo);
  }
}, { threshold: [0, 0.2, 0.65] });

for (const demo of demos) {
  // The observer owns autoplay so that offscreen media cannot start on load.
  demo.video.autoplay = false;
  demo.video.muted = true;
  loadObserver.observe(demo.video);
  playObserver.observe(demo.video);
  demo.video.addEventListener('play', () => {
    if (expandedDemo === demo) demo.manual = 'playing';
    showPlaybackState(demo);
  });
  demo.video.addEventListener('pause', () => {
    if (expandedDemo === demo && !document.hidden) demo.manual = 'paused';
    showPlaybackState(demo);
  });
  demo.video.addEventListener('error', () => {
    demo.button.textContent = 'Повторить';
    demo.button.setAttribute('aria-label', `Повторить загрузку видео: ${demo.label}`);
  });
  demo.button.addEventListener('click', () => {
    if (demo.video.error) {
      demo.video.removeAttribute('src');
      loadVideo(demo);
    }
    demo.manual = demo.video.paused ? 'playing' : 'paused';
    syncVideo(demo);
  });
  const fullscreenButton = demo.figure.querySelector('[data-fullscreen]');
  fullscreenButton.addEventListener('click', () => {
    loadVideo(demo);
    expandedDemo = demo;
    videoDialog.querySelector('.wb-video-dialog-top p').textContent = demo.label;
    demo.video.controls = true;
    videoDialog.showModal();
    expandedFrame.append(demo.video);
    syncAllVideos();
  });
  showPlaybackState(demo);
}
document.addEventListener('visibilitychange', syncAllVideos);
reducedMotion.addEventListener('change', () => {
  demos.forEach(demo => { demo.manual = null; });
  syncAllVideos();
});
