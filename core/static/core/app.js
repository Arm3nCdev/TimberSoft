// Submenús desplegables del sidebar: uno abierto a la vez.
document.querySelectorAll('.menu-toggle').forEach(function (boton) {
  boton.addEventListener('click', function () {
    var seccion = boton.parentElement;
    var abrir = !seccion.classList.contains('abierta');
    document.querySelectorAll('.menu-seccion.abierta').forEach(function (s) {
      s.classList.remove('abierta');
      s.querySelector('.menu-toggle').setAttribute('aria-expanded', 'false');
    });
    if (abrir) {
      seccion.classList.add('abierta');
      boton.setAttribute('aria-expanded', 'true');
    }
  });
});

// Menú del usuario en la barra superior.
var btnUsuario = document.getElementById('btn-usuario');
var menuUsuario = document.getElementById('menu-usuario');
btnUsuario.addEventListener('click', function (e) {
  e.stopPropagation();
  var abierto = menuUsuario.classList.toggle('abierto');
  btnUsuario.setAttribute('aria-expanded', abierto);
});
document.addEventListener('click', function () {
  menuUsuario.classList.remove('abierto');
  btnUsuario.setAttribute('aria-expanded', 'false');
});

// Sidebar en pantallas chicas.
document.getElementById('btn-menu').addEventListener('click', function () {
  document.body.classList.toggle('menu-abierto');
});
document.getElementById('velo').addEventListener('click', function () {
  document.body.classList.remove('menu-abierto');
});
