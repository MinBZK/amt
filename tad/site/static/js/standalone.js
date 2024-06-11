function showPopup() {

  var css = document.createElement("link");
  css.rel = "stylesheet";
  css.href = "http://localhost:8000/static/css/layout.css"
  document.body.appendChild(css);

  var div = document.createElement("div");
  div.className = "tad-overlay"
  document.body.appendChild(div)

  var div = document.createElement("iframe");
  div.className = "tad-holder"
  div.setAttribute("scrolling", "no")
  div.setAttribute("allowtransparency","true")
  div.setAttribute("src", "http://localhost:8000/static/standalone.html")
  document.body.appendChild(div)
}

function closePopup() {
  try {
    document.getElementsByClassName("tad-holder")[0].remove()
    document.getElementsByClassName("tad-overlay")[0].remove()
  } catch (e) {
    error.log(e);
  }
}

showPopup();
