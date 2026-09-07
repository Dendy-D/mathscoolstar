/* ══════════════════════════════════════════════════════════════
   Математика с Василенко А. В. — скрипты лендинга
   ══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $  = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ── Контакты ──────────────────────────────────────────────
     Телефон и WhatsApp — один и тот же номер.                 */
  var CONTACTS = {
    phone:    '+79160164559',
    whatsapp: '79160164559',
    telegram: 'AlViStar2',
    email:    'infomathege@mail.ru'
  };

  /* Тексты модального окна под каждый повод обращения */
  var INTENTS = {
    trial: {
      title: 'Как вам удобнее?',
      lead:  'Напишите или позвоните — отвечу и подберём время бесплатного диагностического урока.',
      msg:   'Здравствуйте, Алевтина Викторовна! Хочу записаться на бесплатный диагностический урок по математике.'
    },
    question: {
      title: 'Задать вопрос',
      lead:  'Спрашивайте о программе, расписании или подготовке к экзамену — отвечу лично.',
      msg:   'Здравствуйте, Алевтина Викторовна! У меня вопрос по занятиям математикой.'
    },
    individual: {
      title: 'Индивидуальные занятия',
      lead:  'Напишите класс ученика и цель — расскажу про программу, расписание и стоимость.',
      msg:   'Здравствуйте, Алевтина Викторовна! Интересуют индивидуальные занятия по математике. Подскажите, пожалуйста, стоимость и расписание.'
    },
    group: {
      title: 'Занятия в мини-группе',
      lead:  'Напишите класс ученика и цель — расскажу про ближайшие группы и стоимость.',
      msg:   'Здравствуйте, Алевтина Викторовна! Интересуют занятия по математике в группе. Подскажите, пожалуйста, стоимость и расписание.'
    }
  };

  /* ── 1. Шапка: фон при скролле ─────────────────────────────── */
  var header = $('#siteHeader');
  var onScrollHeader = function () {
    header.classList.toggle('is-stuck', window.scrollY > 12);
  };
  onScrollHeader();

  /* ── 2. Бургер-меню ────────────────────────────────────────── */
  var burger = $('#burger');
  var nav = $('#nav');
  var closeNav = function () {
    nav.classList.remove('is-open');
    burger.setAttribute('aria-expanded', 'false');
  };
  burger.addEventListener('click', function () {
    var open = nav.classList.toggle('is-open');
    burger.setAttribute('aria-expanded', String(open));
  });
  $$('a', nav).forEach(function (a) { a.addEventListener('click', closeNav); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeNav(); });

  /* ── 3. Появление блоков при скролле ───────────────────────── */
  var revealables = $$('[data-reveal]');
  if (reduced || !('IntersectionObserver' in window)) {
    revealables.forEach(function (el) { el.classList.add('is-in'); });
  } else {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        revealObserver.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });
    revealables.forEach(function (el) { revealObserver.observe(el); });
  }

  /* ── 4. Счётчики в блоке с цифрами ─────────────────────────── */
  var counters = $$('[data-count]');
  var runCounter = function (el) {
    var target = parseInt(el.dataset.count, 10);
    var prefix = el.dataset.prefix || '';
    var suffix = el.dataset.suffix || '';
    if (reduced) { el.textContent = prefix + target + suffix; return; }
    var duration = 1400, start = null;
    var tick = function (now) {
      if (start === null) start = now;
      var p = Math.min((now - start) / duration, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = prefix + Math.round(target * eased) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };
  if ('IntersectionObserver' in window) {
    var countObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        runCounter(entry.target);
        countObserver.unobserve(entry.target);
      });
    }, { threshold: 0.5 });
    counters.forEach(function (el) { countObserver.observe(el); });
  }

  /* ── 5. Подсветка активного пункта меню ────────────────────── */
  var navLinks = $$('a[href^="#"]', nav);
  var sections = navLinks
    .map(function (a) { return $(a.getAttribute('href')); })
    .filter(Boolean);

  if ('IntersectionObserver' in window && sections.length) {
    var visible = new Set();
    var setActive = function () {
      var current = sections.filter(function (s) { return visible.has(s.id); }).pop();
      navLinks.forEach(function (a) {
        a.classList.toggle('is-active', !!current && a.getAttribute('href') === '#' + current.id);
      });
    };
    var navObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) visible.add(entry.target.id);
        else visible.delete(entry.target.id);
      });
      setActive();
    }, { rootMargin: '-45% 0px -50% 0px' });
    sections.forEach(function (s) { navObserver.observe(s); });
  }

  /* ── 6. Модальное окно контактов ───────────────────────────── */
  var dialog = $('#contactDialog');
  var dialogTitle = $('#dialogTitle');
  var dialogLead = $('#dialogLead');
  var optWhatsapp = $('#optWhatsapp');
  var optTelegram = $('#optTelegram');
  var lastFocused = null;

  optTelegram.href = 'https://t.me/' + CONTACTS.telegram;

  var openDialog = function (intentKey) {
    var intent = INTENTS[intentKey] || INTENTS.trial;
    dialogTitle.textContent = intent.title;
    dialogLead.textContent = intent.lead;
    optWhatsapp.href = 'https://wa.me/' + CONTACTS.whatsapp + '?text=' + encodeURIComponent(intent.msg);
    lastFocused = document.activeElement;
    closeNav();
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', '');
  };

  $$('[data-open-dialog]').forEach(function (btn) {
    btn.addEventListener('click', function () { openDialog(btn.dataset.openDialog); });
  });
  $$('[data-close-dialog]').forEach(function (btn) {
    btn.addEventListener('click', function () { dialog.close(); });
  });
  /* клик по подложке закрывает окно */
  dialog.addEventListener('click', function (e) {
    if (e.target !== dialog) return;
    var box = dialog.getBoundingClientRect();
    var outside = e.clientY < box.top || e.clientY > box.bottom ||
                  e.clientX < box.left || e.clientX > box.right;
    if (outside) dialog.close();
  });
  dialog.addEventListener('close', function () {
    if (lastFocused && typeof lastFocused.focus === 'function') lastFocused.focus();
  });

  /* ── 7. Липкая кнопка на мобильных ─────────────────────────── */
  var mobileBar = $('#mobileBar');
  var hero = $('#hero');
  if ('IntersectionObserver' in window && hero) {
    var barObserver = new IntersectionObserver(function (entries) {
      mobileBar.classList.toggle('is-visible', !entries[0].isIntersecting);
    }, { rootMargin: '-60% 0px 0px 0px' });
    barObserver.observe(hero);
  }

  /* ── 8. Мелочи ─────────────────────────────────────────────── */
  $('#year').textContent = new Date().getFullYear();
  window.addEventListener('scroll', onScrollHeader, { passive: true });
})();
