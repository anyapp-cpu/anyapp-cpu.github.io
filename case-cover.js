// Load the local SVG player only near the cover; keep the poster on failure.
(() => {
  let playerPromise;

  function loadPlayer() {
    if (window.lottie) return Promise.resolve();
    if (!playerPromise) {
      playerPromise = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'assets/vendor/lottie-svg-5.13.0.min.js';
        script.onload = resolve;
        script.onerror = reject;
        document.head.append(script);
      });
    }
    return playerPromise;
  }

  function initializeCover(cover) {
    const container = cover?.querySelector('.project-cover-animation');
    if (!container) return;

    const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
    let animation;
    let loading = false;
    let failed = false;
    let ready = false;
    let nearby = false;
    let visible = false;

    function updatePlayback() {
      if (!ready) return;
      if (visible && !document.hidden && !reducedMotion.matches) animation.play();
      else animation.pause();
    }

    async function loadAnimation() {
      if (loading || animation || failed || reducedMotion.matches) return;
      loading = true;
      const controller = new AbortController();
      const timeout = setTimeout(() => {
        controller.abort();
        fallback();
      }, 15000);

      function fallback() {
        clearTimeout(timeout);
        failed = true;
        ready = false;
        cover.classList.remove('is-ready');
        animation?.destroy();
        animation = undefined;
        container.replaceChildren();
      }

      try {
        const [data] = await Promise.all([
          fetch(cover.dataset.lottieCover, { signal: controller.signal }).then(response => {
            if (!response.ok) throw new Error('Cover could not be loaded');
            return response.json();
          }),
          loadPlayer(),
        ]);
        if (failed) return;
        animation = window.lottie.loadAnimation({
          container,
          renderer: 'svg',
          loop: true,
          autoplay: false,
          animationData: data,
          rendererSettings: {
            preserveAspectRatio: 'xMidYMid meet',
            progressiveLoad: true,
            runExpressions: false,
            focusable: false,
          },
        });
        animation.addEventListener('data_failed', fallback);
        animation.addEventListener('error', fallback);
        animation.addEventListener('DOMLoaded', () => {
          clearTimeout(timeout);
          ready = true;
          cover.classList.add('is-ready');
          updatePlayback();
        });
      } catch {
        fallback();
      } finally {
        loading = false;
      }
    }

    if ('IntersectionObserver' in window) {
      new IntersectionObserver(([entry]) => {
        nearby = entry.isIntersecting;
        if (nearby) loadAnimation();
      }, { rootMargin: '300px' }).observe(cover);
      new IntersectionObserver(([entry]) => {
        visible = entry.isIntersecting;
        updatePlayback();
      }).observe(cover);
    } else {
      nearby = visible = true;
      loadAnimation();
    }

    reducedMotion.addEventListener('change', () => {
      if (nearby && !reducedMotion.matches) loadAnimation();
      updatePlayback();
    });
    document.addEventListener('visibilitychange', updatePlayback);
  }

  document.querySelectorAll('[data-lottie-cover]').forEach(initializeCover);
})();
