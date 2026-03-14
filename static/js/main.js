// ── Scroll reveal (Intersection Observer) ───────────
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  },
  { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
);

document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));

// ── Navbar: dark glass over hero, light glass over white sections ──
const navbar = document.getElementById('navbar');
const hero = document.querySelector('.hero');

function updateNavbar() {
  const heroBottom = hero ? hero.offsetTop + hero.offsetHeight : 0;
  navbar.classList.toggle('nav-light', window.scrollY > heroBottom - 80);
}

window.addEventListener('scroll', updateNavbar, { passive: true });
updateNavbar();
