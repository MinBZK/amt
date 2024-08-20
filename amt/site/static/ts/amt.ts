import Sortable from "sortablejs";
import "htmx.org";

window.onload = function () {
  // TODO (robbert): we need (better) event handling and displaying of server errors
  document.body.addEventListener("htmx:sendError", function () {
    document.getElementById("errorContainer")!.innerHTML =
      "<h1>Placeholder: Error while connecting to server</h1";
  });

  const columns = document.getElementsByClassName(
    "progress_cards_container",
  ) as HTMLCollectionOf<HTMLDivElement>;
  for (let i = 0; i < columns.length; i++) {
    new Sortable(columns[i], {
      //NOSONAR
      group: "shared", // set both lists to same group
      animation: 150,
      onEnd: function (evt) {
        if (evt.oldIndex !== evt.newIndex || evt.from !== evt.to) {
          let previousSiblingId = evt.item.previousElementSibling
            ? evt.item.previousElementSibling.getAttribute("data-id")
            : "-1";
          let nextSiblingId = evt.item.nextElementSibling
            ? evt.item.nextElementSibling.getAttribute("data-id")
            : "-1";
          let targetId = "#" + evt.item.getAttribute("data-target-id");
          let toStatusId = evt.to.getAttribute("data-id");
          let form = document.getElementById("cardMovedForm");

          (document.getElementsByName("taskId")[0] as HTMLInputElement).value =
            evt.item.getAttribute("data-id") ?? "";
          (
            document.getElementsByName("statusId")[0] as HTMLInputElement
          ).value = toStatusId ?? "";
          (
            document.getElementsByName(
              "previousSiblingId",
            )[0] as HTMLInputElement
          ).value = previousSiblingId ?? "";
          (
            document.getElementsByName("nextSiblingId")[0] as HTMLInputElement
          ).value = nextSiblingId ?? "";
          form!.setAttribute("hx-target", targetId);

          // @ts-expect-error"
          htmx.trigger("#cardMovedForm", "cardmoved");
        }
      },
    });
  }
};

// @ts-expect-error"
function setCookie(
  cookieName: string,
  cookieValue: string,
  expirationDays: number,
) {
  const date = new Date();
  date.setTime(date.getTime() + expirationDays * 24 * 60 * 60 * 1000); // Set expiration time
  const expires = "expires=" + date.toUTCString();
  document.cookie =
    cookieName + "=" + cookieValue + ";" + expires + ";path=/;SameSite=Strict";
}
