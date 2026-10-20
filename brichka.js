(() => {
  const links = [...document.querySelectorAll('.case-toc a')];
  const sections = links.map(link => document.querySelector(link.hash));
  let scheduled = false;
  function updateReading() {
    let active = sections[0];
    for (const section of sections) if (section.getBoundingClientRect().top <= innerHeight * .35) active = section;
    for (const link of links) {
      if (link.hash === `#${active.id}`) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    }
    const available = document.documentElement.scrollHeight - innerHeight;
    document.documentElement.style.setProperty('--reading-progress', `${available > 0 ? Math.max(0, Math.min(100, scrollY / available * 100)) : 0}%`);
    scheduled = false;
  }
  function scheduleReading() { if (!scheduled) { scheduled = true; requestAnimationFrame(updateReading); } }
  addEventListener('scroll', scheduleReading, { passive: true });
  addEventListener('resize', scheduleReading);
  addEventListener('pageshow', scheduleReading);
  updateReading();

  const dialog = document.querySelector('.bc-image-dialog');
  const expandedImage = dialog.querySelector('img');
  let opener;
  for (const button of document.querySelectorAll('[data-zoom]')) button.addEventListener('click', () => {
    opener = button;
    const original = button.querySelector('[data-zoom-image]') || button.querySelector('img');
    expandedImage.src = button.dataset.zoom;
    expandedImage.alt = original.alt;
    dialog.querySelector('figcaption').textContent = button.dataset.caption;
    dialog.classList.toggle('is-phone', original.naturalWidth < original.naturalHeight);
    dialog.showModal();
    dialog.scrollTop = 0;
  });
  dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => opener?.focus({ preventScroll: true }));

  const steps = [
    { screen: 'offers', caption: 'Предложения водителей перед началом торга', status: 'Выберите предложение, чтобы начать торг', text: 'Стоимость можно оценить вместе со временем подачи. В примере водитель с предложением 330 ₽ приедет за 5 минут.' },
    { screen: 'auction-lower', caption: 'Первый шаг торга: пассажир предлагает 310 ₽', status: 'Пассажир снижает цену на первом шаге', text: 'Пассажир снижает предложение с 330 до 310 ₽ и отправляет запрос. Заголовок и зачёркнутая сумма показывают, что изменилось.' },
    { screen: 'auction-wait', caption: 'Пассажир ожидает ответа водителя', status: 'Запрос отправлен, теперь ход водителя', text: 'Кнопка меняет состояние и сообщает об ожидании ответа. Пассажир может продолжить поиск других водителей.' },
    { screen: 'auction-final', caption: 'Второй шаг торга: принять предложение за 320 ₽', status: 'Финальная цена: 320 ₽', text: 'Водитель предлагает 320 ₽ на втором шаге. Пассажиру остаётся принять цену или вернуться к поиску.' },
  ];
  const tabs = [...document.querySelectorAll('[data-auction-step]')];
  const screen = document.querySelector('.bc-auction-screen');
  const screenImage = screen.querySelector('[data-zoom-image]');
  let stepIndex = 0;
  function showStep(index, focus = false) {
    stepIndex = (index + steps.length) % steps.length;
    const step = steps[stepIndex];
    screenImage.src = `assets/brichka/vectors/${step.screen}.svg`;
    screenImage.alt = step.caption;
    screen.dataset.zoom = screenImage.getAttribute('src');
    screen.dataset.caption = step.caption;
    screen.setAttribute('aria-label', `Увеличить: ${step.caption}`);
    document.querySelector('#auction-stage-caption').textContent = step.status;
    document.querySelector('#auction-explanation').textContent = step.text;
    document.querySelector('#auction-panel').setAttribute('aria-labelledby', tabs[stepIndex].id);
    document.querySelector('[data-auction-counter]').textContent = `${stepIndex + 1} из ${steps.length}`;
    document.querySelector('[data-auction-next]').firstChild.textContent = stepIndex === 3 ? 'К началу ' : 'Следующий шаг ';
    tabs.forEach((tab, i) => { tab.setAttribute('aria-selected', String(i === stepIndex)); tab.tabIndex = i === stepIndex ? 0 : -1; });
    if (focus) tabs[stepIndex].focus();
  }
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => showStep(i));
    tab.addEventListener('keydown', event => {
      const next = { ArrowDown: i + 1, ArrowUp: i - 1, Home: 0, End: steps.length - 1 }[event.key];
      if (next !== undefined) { event.preventDefault(); showStep(next, true); }
    });
  });
  document.querySelector('[data-auction-next]').addEventListener('click', () => showStep(stepIndex + 1));
})();
