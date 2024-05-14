window.onload = function () {
  console.log("This test file has been loaded");

  var columns = document.getElementsByClassName("progress_cards_container");
  for (var i = 0; i < columns.length; i++) {
    new Sortable(columns[i], {
      group: 'shared', // set both lists to same group
      animation: 150,
      onEnd: function (evt) {
        console.log(evt);
        let previousSiblingId = evt.item.previousElementSibling ? evt.item.previousElementSibling.getAttribute("data-id") : "";
        let nextSiblingId = evt.item.nextElementSibling ? evt.item.nextElementSibling.getAttribute("data-id") : "";
        let data = {
          "taskId": evt.item.getAttribute("data-id"),
          "statusId": evt.to.getAttribute("data-id"),
          "previousSiblingId": previousSiblingId,
          "nextSiblingId": nextSiblingId
        }

        console.log(JSON.stringify(data));

        let headers = {
          'Content-Type': 'application/json'
        };
        let targetId = "#" + evt.item.getAttribute("id");
        let form = document.getElementById("cardMovedForm");
        document.getElementsByName("taskId")[0].value = evt.item.getAttribute("data-id");
        document.getElementsByName("statusId")[0].value = evt.to.getAttribute("data-id");
        document.getElementsByName("previousSiblingId")[0].value = previousSiblingId;
        document.getElementsByName("nextSiblingId")[0].value = nextSiblingId;
        form.setAttribute("hx-target", targetId);
        console.log(form)
        htmx.trigger("#cardMovedForm", "cardmoved");

        // TODO: this must be a JSON post, but I can not get it to work with HTMX...
        // https://htmx.org/api/#ajax
        //htmx.ajax('POST', "/tasks/move", {values: JSON.stringify({ data: data }), headers: headers, target: targetId, swap: 'outerHTML'})
      }
    });
  }

  window.addEventListener("cardmoved", function (e) {
    console.log("me?");
    console.log(e);
  });
}
