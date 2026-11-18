// Vídeos de demonstração: carregam e tocam só quando aparecem na tela
const reduz = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const vids = document.querySelectorAll('video.vid');
const carrega = v => { if (!v.src && v.dataset.src) { v.src = v.dataset.src; } };
if ('IntersectionObserver' in window) {
  const io = new IntersectionObserver(entries => {
    entries.forEach(({ target: v, isIntersecting }) => {
      if (isIntersecting) {
        carrega(v);
        if (!reduz) v.play().catch(() => {});
      } else if (!v.paused) {
        v.pause();
      }
    });
  }, { rootMargin: '200px 0px', threshold: 0.15 });
  vids.forEach(v => io.observe(v));
} else {
  vids.forEach(v => { carrega(v); if (!reduz) v.play().catch(() => {}); });
}

// Lightbox (imagem ou vídeo)
const lb = document.getElementById('lb');
const lbImg = lb.querySelector('img');
const lbVid = lb.querySelector('video');
const lbCap = lb.querySelector('figcaption');
const abrir = el => {
  if (el.dataset.video) {
    lbImg.hidden = true;
    lbVid.hidden = false;
    lbVid.src = el.dataset.video;
    lbVid.currentTime = 0;
    lbVid.play().catch(() => {});
  } else {
    lbVid.hidden = true;
    lbImg.hidden = false;
    lbImg.src = el.dataset.full;
    lbImg.alt = el.dataset.cap || '';
  }
  lbCap.textContent = el.dataset.cap || '';
  lb.hidden = false;
};
document.querySelectorAll('[data-full], [data-video]').forEach(el => el.addEventListener('click', () => abrir(el)));
const fechar = () => { lb.hidden = true; lbImg.src = ''; lbVid.pause(); lbVid.removeAttribute('src'); lbVid.load(); };
lb.addEventListener('click', e => { if (e.target !== lbImg && e.target !== lbVid) fechar(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') fechar(); });

// Thumbs trocam a imagem principal (projetos ainda sem vídeo)
document.querySelectorAll('.proj').forEach(proj => {
  const main = proj.querySelector('.main-shot');
  const mainImg = main && main.querySelector('img');
  if (!mainImg) return;
  proj.querySelectorAll('.thumb').forEach(t => {
    t.addEventListener('mouseenter', () => {
      mainImg.src = t.dataset.full;
      main.dataset.full = t.dataset.full;
      main.dataset.cap = t.dataset.cap;
    });
  });
});

// Filtros por categoria
document.querySelectorAll('.f').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.f').forEach(b => b.classList.toggle('on', b === btn));
    const f = btn.dataset.f;
    document.querySelectorAll('.proj, .autos').forEach(p => { p.hidden = f !== '*' && p.dataset.cat !== f; });
  });
});

// Carrossel "O que entrega"
document.querySelectorAll('.entregas').forEach(box => {
  const track = box.querySelector('.ent-track');
  const prev = box.querySelector('.ent-prev');
  const next = box.querySelector('.ent-next');
  const nav = box.querySelector('.ent-nav');
  const passo = () => { const c = track.querySelector('.ent'); return c ? c.offsetWidth + 12 : track.clientWidth; };
  const atualiza = () => {
    const max = track.scrollWidth - track.clientWidth;
    nav.classList.toggle('off', max <= 2);
    prev.disabled = track.scrollLeft <= 2;
    next.disabled = track.scrollLeft >= max - 2;
  };
  prev.addEventListener('click', () => track.scrollBy({ left: -passo(), behavior: 'smooth' }));
  next.addEventListener('click', () => track.scrollBy({ left: passo(), behavior: 'smooth' }));
  track.addEventListener('scroll', atualiza, { passive: true });
  window.addEventListener('resize', atualiza);
  atualiza();
});
