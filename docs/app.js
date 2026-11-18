// Lightbox
const lb = document.getElementById('lb');
const lbImg = lb.querySelector('img');
const lbCap = lb.querySelector('figcaption');
document.querySelectorAll('[data-full]').forEach(el => {
  el.addEventListener('click', () => {
    lbImg.src = el.dataset.full;
    lbImg.alt = el.dataset.cap || '';
    lbCap.textContent = el.dataset.cap || '';
    lb.hidden = false;
  });
});
const fechar = () => { lb.hidden = true; lbImg.src = ''; };
lb.addEventListener('click', e => { if (e.target !== lbImg) fechar(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') fechar(); });

// Thumbs trocam a imagem principal
document.querySelectorAll('.proj').forEach(proj => {
  const main = proj.querySelector('.main-shot');
  const mainImg = main.querySelector('img');
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
