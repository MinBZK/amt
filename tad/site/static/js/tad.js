window.onload = function () {

  // TODO (robbert): we need (better) event handling and displaying of server errors
  document.body.addEventListener('htmx:sendError', function(evt) {
    document.getElementById("errorContainer").innerHTML = "<h1>Placeholder: Error while connecting to server</h1";
  });

  const columns = document.getElementsByClassName("progress_cards_container");
  for (let i = 0; i < columns.length; i++) {
    new Sortable(columns[i], { //NOSONAR
      group: 'shared', // set both lists to same group
      animation: 150,
      onEnd: function (evt) {
        if (evt.oldIndex !== evt.newIndex || evt.from !== evt.to) {
          let previousSiblingId = evt.item.previousElementSibling ? evt.item.previousElementSibling.getAttribute("data-id") : "-1";
          let nextSiblingId = evt.item.nextElementSibling ? evt.item.nextElementSibling.getAttribute("data-id") : "-1";
          let targetId = "#" + evt.item.getAttribute("data-target-id");
          let toStatusId = evt.to.getAttribute("data-id");
          let form = document.getElementById("cardMovedForm");
          document.getElementsByName("taskId")[0].value = evt.item.getAttribute("data-id");
          document.getElementsByName("statusId")[0].value = toStatusId;
          document.getElementsByName("previousSiblingId")[0].value = previousSiblingId;
          document.getElementsByName("nextSiblingId")[0].value = nextSiblingId;
          form.setAttribute("hx-target", targetId);
          htmx.trigger("#cardMovedForm", "cardmoved");
        }
      }
    });
  }
}

function setCookie(cookieName, cookieValue, expirationDays) {
  const date = new Date();
  date.setTime(date.getTime() + (expirationDays * 24 * 60 * 60 * 1000)); // Set expiration time
  const expires = "expires=" + date.toUTCString();
  document.cookie = cookieName + "=" + cookieValue + ";" + expires + ";path=/;SameSite=Strict";
}
