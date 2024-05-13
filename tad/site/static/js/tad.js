window.onload = function () {
  console.log("This test file has been loaded");

  var columns = document.getElementsByClassName("progress_cards_container");
  for (var i = 0; i < columns.length; i++) {
    new Sortable(columns[i], {
      group: 'shared', // set both lists to same group
      animation: 150,
      onEnd: function (evt) {
        console.log(evt);
        let data = {
          "taskId": evt.item.getAttribute("data-id"),
          "statusId": evt.to.getAttribute("data-id"),
        }
        if (evt.item.previousElementSibling) {
          data["previousSiblingId"] = evt.item.previousElementSibling.getAttribute("data-id");
        }
        if (evt.item.nextElementSibling) {
          data["nextSiblingId"] = evt.item.nextElementSibling.getAttribute("data-id");
        }
        console.log(JSON.stringify(data));

        let headers = {
          'Content-Type': 'application/json'
        };
        let targetId = "#" + evt.item.getAttribute("id");
        // TODO: this must be a JSON post, but I can not get it to work with HTMX...
        // https://htmx.org/api/#ajax
        htmx.ajax('POST', "/tasks/move", {values: data, target: targetId, swap: 'outerHTML'})
      }
    });
  }

  window.addEventListener("cardmoved", function (e) {
    console.log("me?");
    console.log(e);
  });
}
