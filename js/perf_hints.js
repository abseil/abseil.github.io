const expand = document.querySelector("#expand-details-button");
const collapse = document.querySelector("#collapse-details-button"); 

expand.addEventListener("click", (event) => {
  document.body.querySelectorAll('details')
  .forEach((it) => { if (!it.hasAttribute('open')) it.setAttribute('open', true)});
});

collapse.addEventListener("click", (event) => {
  document.body.querySelectorAll('details')
  .forEach((it) => {if (it.hasAttribute('open')) it.removeAttribute('open')});
});

