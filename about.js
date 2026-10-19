const sectionLinks = [...document.querySelectorAll('.about-navigation a')];
const sections = sectionLinks.map(link => document.querySelector(link.hash));

function updateSectionNavigation() {
  const readingLine = window.innerHeight * 0.3;
  let currentSection = sections[0];
  for (const section of sections) {
    if (section.getBoundingClientRect().top <= readingLine) currentSection = section;
  }
  for (const link of sectionLinks) {
    if (link.hash === `#${currentSection.id}`) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  }
}

let scheduled = false;
window.addEventListener('scroll', () => {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(() => {
    updateSectionNavigation();
    scheduled = false;
  });
}, { passive: true });
window.addEventListener('resize', updateSectionNavigation);
window.addEventListener('pageshow', updateSectionNavigation);
updateSectionNavigation();
