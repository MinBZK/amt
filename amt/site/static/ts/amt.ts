import Sortable from "sortablejs";
import htmx from "htmx.org";
import _hyperscript from "hyperscript.org";

import "../scss/tabs.scss";
import "../scss/layout.scss";
/* eslint-disable  @typescript-eslint/no-non-null-assertion */

_hyperscript.browserInit();

document.addEventListener("DOMContentLoaded", function () {
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
    // prettier-ignore
    new Sortable(column, { //NOSONAR
      group: "shared", // set both lists to same group
      animation: 150,
      onEnd: function(evt) {
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
});

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

export function showMobileMenu() {
  const el: Element | null = document.getElementById("mobile-menu-container");
  if (el != null) {
    el.classList.remove("display-none");
  }
}

export function hideMobileMenu() {
  const el: Element | null = document.getElementById("mobile-menu-container");
  if (el != null) {
    el.classList.add("display-none");
  }
}

window.setCookie = setCookie;
window.htmx = htmx;

export function openModal(id: string) {
  const el: Element | null = document.getElementById(id);
  if (el != null) {
    el.classList.remove("display-none");
  }
}

class AiActProfile {
  constructor(
    public type: string[],
    public publication_category: string[],
    public transparency_obligations: string[],
    public systemic_risk: string[],
    public role: string[],
    public open_source: string[],
  ) {}
}

export function closeModal(id: string) {
  // Do not show modal.
  const el: Element | null = document.getElementById(id);
  if (el != null) {
    el.classList.add("display-none");
  }
}

export function closeModalSave(id: string) {
  closeModal(id);

  // Get decision tree state from local store.
  const decision_tree_state = localStorage?.getItem("labelsbycategory");

  if (decision_tree_state != null) {
    // Parse decision tree state into AiActProfile object.
    const aiActProfileRaw = JSON.parse(decision_tree_state);
    const aiActProfile: AiActProfile = new AiActProfile(
      aiActProfileRaw["Soort toepassing"],
      aiActProfileRaw["Publicatiecategorie"],
      aiActProfileRaw["Transparantieverplichtingen"],
      aiActProfileRaw["Systeemrisico"],
      aiActProfileRaw["Rol"],
      aiActProfileRaw["Open-source"],
    );

    // Select the correct entries.
    Object.entries(aiActProfile).forEach(([category, el_ids]) => {
      el_ids.forEach((el_id: string) => {
        const element = document.getElementById(`${category}-${el_id}`);
        element?.click();
      });
    });
  }
}

export function reset_errorfield(id: string): void {
  const el = document.getElementById(id);
  if (el) {
    el.innerHTML = "";
  }
}

export function prevent_submit_on_enter(): void {
  // @ts-expect-error false positive
  if (event.key === "Enter") {
    // @ts-expect-error false positive
    event.preventDefault();
  }
}

export function generate_slug(sourceId: string, targetId: string) {
  if (
    document.getElementById(sourceId) != null &&
    document.getElementById(targetId) != null
  ) {
    const value = (document.getElementById(sourceId) as HTMLInputElement)!
      .value;
    (document.getElementById(targetId) as HTMLInputElement)!.value = value
      .toLowerCase()
      .replace(/[^a-z0-9-_ ]/g, "")
      .replace(/\s/g, "-");
  }
}

export function add_field(field: HTMLElement) {
  const value = field.getAttribute("data-value");
  const targetId = (field.parentNode as HTMLElement)!.getAttribute(
    "data-target-id",
  );
  const parentId = (field?.parentNode as HTMLElement).id;

  if (targetId != null) {
    const existing = document
      .getElementById(targetId)!
      .querySelectorAll(`[data-value="` + value + `"]`);
    if (existing.length === 1) {
      return;
    }
    // the new element is in the attribute field of the search result as base64 encoded string
    const newElement = atob(field.getAttribute("data-list-result") as string);
    document
      .getElementById(targetId)!
      .insertAdjacentHTML("beforeend", newElement);
    document.getElementById(parentId)!.style.display = "none";
    document.getElementById(parentId)!.innerHTML = "";
    (document.getElementById(parentId)!
      .previousElementSibling as HTMLFormElement)!.value = "";
  }
}

export function show_form_search_options(id: string) {
  document.getElementById(id)!.style.display = "block";
}

export function hide_form_search_options(id: string) {
  window.setTimeout(function () {
    document.getElementById(id)!.style.display = "none";
  }, 250);
}

export function add_field_on_enter(id: string) {
  if (!event) {
    return;
  }
  if (
    (event as KeyboardEvent).key == "ArrowUp" ||
    (event as KeyboardEvent).key == "ArrowDown"
  ) {
    // const searchOptions = document.getElementById(id)!.querySelectorAll("li");
    event.preventDefault();
    // nice to have: use arrow keys to select options
    // searchOptions[0].style.border = "1px solid red"
  }
  if ((event as KeyboardEvent).key === "Enter") {
    event.preventDefault();
    const searchOptions = document.getElementById(id)!.querySelectorAll("li");
    if (searchOptions.length === 1) {
      searchOptions[0].click();
    }
  } else {
    // make sure search results are visible when we type any key
    show_form_search_options(id);
  }
}
