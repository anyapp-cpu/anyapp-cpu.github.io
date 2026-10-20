const sectionLinks = [...document.querySelectorAll('.case-toc a')];
const sections = sectionLinks.map(link => document.querySelector(link.hash));
let scheduled = false;
function updateReadingPosition() {
  let currentSection = sections[0];
  for (const section of sections) {
    if (section.getBoundingClientRect().top <= window.innerHeight * 0.35) currentSection = section;
  }
  for (const link of sectionLinks) {
    if (link.hash === `#${currentSection.id}`) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }
  const available = document.documentElement.scrollHeight - window.innerHeight;
  const progress = available > 0 ? Math.max(0, Math.min(100, window.scrollY / available * 100)) : 0;
  document.documentElement.style.setProperty('--reading-progress', `${progress}%`);
  scheduled = false;
}
function scheduleReadingUpdate() {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(updateReadingPosition);
}
window.addEventListener('scroll', scheduleReadingUpdate, { passive: true });
window.addEventListener('resize', scheduleReadingUpdate);
window.addEventListener('pageshow', scheduleReadingUpdate);
updateReadingPosition();

const dialog = document.querySelector('.image-dialog');
const dialogImage = dialog.querySelector('img');
const dialogCaption = dialog.querySelector('figcaption');
for (const button of document.querySelectorAll('[data-zoom]')) {
  button.setAttribute('aria-label', `Увеличить макет: ${button.dataset.caption}`);
  button.addEventListener('click', () => {
    const original = button.querySelector('[data-zoom-image]') || button.querySelector('img');
    dialogImage.src = button.dataset.zoom;
    dialogImage.alt = original.alt;
    dialogImage.width = original.naturalWidth;
    dialogImage.height = original.naturalHeight;
    dialog.classList.toggle('is-tall', original.naturalWidth / original.naturalHeight < 0.8);
    dialogCaption.textContent = button.dataset.caption;
    dialog.showModal();
    dialog.scrollTop = 0;
  });
}
dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  if (event.target !== dialog) return;
  const bounds = dialog.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
});

const variableButtons = [...document.querySelectorAll('[data-variable-mode]')];
const variableImage = document.querySelector('.variables-screen');
const variableZoom = document.querySelector('.variables-zoom');
for (const button of variableButtons) {
  button.addEventListener('click', () => {
    const mode = button.dataset.variableMode;
    const source = `assets/gocomment/vectors/variables-${mode}.svg`;
    variableImage.src = source;
    variableZoom.dataset.zoom = source;
    variableZoom.dataset.caption = mode === 'theme' ? 'Коллекция theme: режимы pluto и venus' : 'Коллекция language: режимы eng и ru';
    variableZoom.setAttribute('aria-label', `Увеличить макет: ${variableZoom.dataset.caption}`);
    for (const item of variableButtons) item.setAttribute('aria-pressed', String(item === button));
  });
}

const heroStage = document.querySelector('.live-scene');
const sceneButtons = [...document.querySelectorAll('[data-scene-target]')];
for (const button of sceneButtons) {
  button.addEventListener('click', () => {
    heroStage.dataset.scene = button.dataset.sceneTarget;
    for (const item of sceneButtons) item.setAttribute('aria-pressed', String(item === button));
  });
}
