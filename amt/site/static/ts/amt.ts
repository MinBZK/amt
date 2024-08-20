import Sortable from "sortablejs";
import htmx from "htmx.org";
import _hyperscript from "hyperscript.org";

import "../scss/layout.scss";

_hyperscript.browserInit();

window.onload = function () {
  // TODO (robbert): we need (better) event handling and displaying of server errors
  document.body.addEventListener("htmx:sendError", function () {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    document.getElementById("errorContainer")!.innerHTML =
      "<h1>Placeholder: Error while connecting to server</h1";
  });

  const columns = document.getElementsByClassName(
    "progress-cards-container",
  ) as HTMLCollectionOf<HTMLDivElement>;
  for (const column of columns) {
    new Sortable(column, {
      //NOSONAR
      group: "shared", // set both lists to same group
      animation: 150,
      onEnd: function (evt) {
        if (evt.oldIndex !== evt.newIndex || evt.from !== evt.to) {
          const previousSiblingId = evt.item.previousElementSibling
            ? evt.item.previousElementSibling.getAttribute("data-id")
            : "-1";
          const nextSiblingId = evt.item.nextElementSibling
            ? evt.item.nextElementSibling.getAttribute("data-id")
            : "-1";
          const targetId = "#" + evt.item.getAttribute("data-target-id");
          const toStatusId = evt.to.getAttribute("data-id");
          const form = (document.getElementById("cardMovedForm") ??
            "") as HTMLFormElement;

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
          form.setAttribute("hx-target", targetId);

          // @ts-expect-error Description: Ignoring type error because the htmx.trigger function is not recognized by TypeScript.
          htmx.trigger("#cardMovedForm", "cardmoved");
        }
      },
    });
  }
};

export function setCookie(
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

declare global {
  interface Window {
    setCookie: (
      cookieName: string,
      cookieValue: string,
      expirationDays: number,
    ) => void;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    htmx: any;
  }
}

window.setCookie = setCookie;
window.htmx = htmx;
