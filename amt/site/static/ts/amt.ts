import Sortable from "sortablejs";
import htmx from "htmx.org";
import _hyperscript from "hyperscript.org";

import "../scss/tabs.scss";
import "../scss/layout.scss";
/* eslint-disable  @typescript-eslint/no-non-null-assertion */

_hyperscript.browserInit();

const currentSortables: Sortable[] = [];

if (window.location.pathname === "/algorithms/new") {
  const keysToRemove = [
    "labelsbysubcategory",
    "answers",
    "categoryState",
    "categoryTrace",
    "currentCategory",
    "currentconclusion",
    "currentquestion",
    "currentSubCategory",
    "labels",
    "previousCategory",
    "previousSubCategory",
    "subCategoryTrace",
  ];
  keysToRemove.forEach((key) => {
    sessionStorage.removeItem(key);
  });
}

/**
 * Before we send a (form) request, we want to make sure all "error messages" are cleared.
 */
document.addEventListener("htmx:beforeRequest", (e) => {
  if ((e.target as HTMLElement).nodeName === "FORM") {
    document.querySelectorAll(".htmx-error-oob").forEach((e) => {
      e.innerHTML = "";
    });
  }
});

/**
 * Sortable breaks with dynamic elements, so when tasks are 'swapped', we re-initialize the sortable elements
 */
document.addEventListener("htmx:afterSwap", (e) => {
  if (
    ["tasks-search-results", "search-tasks-container"].includes(
      (e.target as HTMLElement).getAttribute("id") as string,
    )
  ) {
    while (currentSortables.length > 0) {
      const sortable = currentSortables.shift();
      sortable!.destroy();
    }
    initPage();
  }
});

document.addEventListener("DOMContentLoaded", initPage);

function initPage() {
  // TODO (robbert): we need (better) event handling and displaying of server errors
  document.body.addEventListener("htmx:sendError", function () {
    document.getElementById("errorContainer")!.innerHTML =
      "<h1>Placeholder: Error while connecting to server</h1";
  });

  /* we register the click on the body to avoid having to dynamically add it to each element, especially after a htmlx swap event */
  document.querySelector("body")!.addEventListener("click", (e) => {
    if ((e.target as HTMLElement).classList.contains("amt-editable-block")) {
      const linkEl = (e.target as HTMLElement)!.querySelectorAll(
        ".amt-edit-link",
      )[0];
      if (linkEl) {
        (linkEl as HTMLElement).click();
      }
    }
  });

  const columns = document.getElementsByClassName(
    "sortable",
  ) as HTMLCollectionOf<HTMLDivElement>;
  for (const column of columns) {
    // prettier-ignore
    currentSortables.push(Sortable.create(column, { //NOSONAR
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

            htmx.trigger("#cardMovedForm", "cardmoved");
          }
        },
      })
    )
  }
}

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
    const contentEl = el.querySelector(".modal-content");
    if (contentEl) {
      const observer = new MutationObserver(() => {
        contentEl.scrollTop = 0;
        observer.disconnect();
      });
      observer.observe(el, { childList: true, subtree: true });
    }
    el.classList.remove("display-none");
  }
}

export function openDynamicModal(modalId: string) {
  if (modalId == "ai-act-support-tool") {
    document.getElementById("dynamic-modal-content")!.innerHTML = `<iframe
          style="display: block; width: 100%; height: 100%; border: 0; padding: 0; margin: 0; overflow: hidden;"
          src="/static/beslishulp.html"></iframe>`;
  } else {
    console.error("Unkown dynamic modalId: " + modalId);
  }
  openModal("modal");
}

export function openConfirmModal(
  title: string,
  content: string,
  action_type: string,
  action_url: string,
) {
  const template: HTMLElement | null = document.getElementById(
    "confirm-modal-template",
  );
  if (template) {
    const clone: Node = (template as HTMLTemplateElement).content.cloneNode(
      true,
    );
    (clone as HTMLElement).querySelector("[data-target='title']")!.innerHTML =
      title;
    (clone as HTMLElement).querySelector("[data-target='content']")!.innerHTML =
      content;
    (clone as HTMLElement)
      .querySelector("[data-target='confirm-button']")!
      .setAttribute(action_type, action_url);
    document.body.appendChild(clone);
    // TODO: find out why process does not work on the clone element and if there are side effects to do it on the body
    htmx.process(document.body);
  }
}

class AiActProfile {
  constructor(
    public type: string[],
    public operational: string[],
    public risk_group: string[],
    public conformity_assessment_body: string[],
    public transparency_obligations: string[],
    public systemic_risk: string[],
    public role: string[],
    public open_source: string[],
  ) {}
}

export function closeModal(id: string) {
  const el: Element | null = document.getElementById(id);
  if (el != null) {
    el.classList.add("display-none");
  } else {
    console.error(
      "Can not close modal, element with id '" + id + "' not found",
    );
  }
}

export function closeAndResetDynamicModal(id: string) {
  closeModal(id);
  const el: Element | null = document.getElementById("dynamic-modal-content");
  if (el) {
    // we want to remove all modal content to avoid unwanted or unexpected behaviour
    el.innerHTML = "";
  } else {
    console.error(
      "Can not reset modal content, element with id 'dynamic-modal-content' not found",
    );
  }
}

export function closeModalSave(id: string) {
  closeModal(id);

  // Get ai act support tool state from local store.
  const ai_act_support_tool_state = sessionStorage?.getItem(
    "labelsbysubcategory",
  );

  if (ai_act_support_tool_state != null) {
    // Parse ai act support tool state into AiActProfile object.
    const aiActProfileRaw = JSON.parse(ai_act_support_tool_state);
    const aiActProfile: AiActProfile = new AiActProfile(
      aiActProfileRaw["Soort toepassing"],
      aiActProfileRaw["Operationeel"],
      aiActProfileRaw["Risicogroep"],
      aiActProfileRaw["Conformiteitsbeoordelingsinstantie"],
      aiActProfileRaw["Transparantieverplichting"],
      aiActProfileRaw["Systeemrisico"],
      aiActProfileRaw["Rol"],
      aiActProfileRaw["Open source"],
    );

    // Select the correct entries.
    Object.entries(aiActProfile).forEach(([category, el_ids]) => {
      el_ids.forEach((el_id: string) => {
        // radio buttons and checkboxes
        try {
          const element: HTMLElement | null = document.getElementById(
            `${category}-${el_id}`,
          );
          if (element) {
            element.click();
          }
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (e) {
          // Do Nothing
        }

        // dropdowns
        try {
          const element = document.getElementById(`${category}`);
          if (element) {
            (element as HTMLInputElement).value = el_ids[0];
          }
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (e) {
          // Do Nothing
        }
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
    const element = document.getElementById(id);
    if (element) {
      element.style.display = "none";
    }
  }, 250);
}

export function hide_download_dropdown() {
  const dropdownContent = document.querySelector(
    ".dropdown-content",
  ) as HTMLElement;
  const dropdownUnderlay = document.querySelector(
    ".dropdown-underlay",
  ) as HTMLElement;

  if (dropdownContent && dropdownUnderlay) {
    dropdownContent.style.display = "none";
    dropdownUnderlay.style.display = "none";
  } else {
    console.error("Could not find dropdown elements.");
  }
}

export function show_download_dropdown() {
  const dropdownContent = document.querySelector(
    ".dropdown-content",
  ) as HTMLElement;
  const dropdownUnderlay = document.querySelector(
    ".dropdown-underlay",
  ) as HTMLElement;

  if (dropdownContent && dropdownUnderlay) {
    dropdownContent.style.display = "block";
    dropdownUnderlay.style.display = "block";
  } else {
    console.error("Could not find dropdown elements.");
  }
}

export async function download_as_yaml(
  algorithm_id: string,
  algorithm_name: string,
): Promise<void> {
  try {
    const response = await fetch(`/algorithm/${algorithm_id}/download`);
    const blob = await response.blob(); // Get the response as a Blob

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    const filename = algorithm_name + "_" + new Date().toISOString() + ".yaml";
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
  } catch (error) {
    console.error("Error downloading system card:", error);
  }
  hide_download_dropdown();
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

export function createLinkComponent(template_id: string, element_id: string) {
  const template = document.getElementById(template_id) as HTMLTemplateElement;
  const item = document.getElementById(element_id);
  const link = template?.content.cloneNode(true);
  if (link) {
    item?.appendChild(link);
  }
}

export function getFiles(element: HTMLInputElement, target_id: string) {
  if (element.files) {
    const list = document.getElementById(target_id) as HTMLElement;
    list.innerHTML = "";
    for (const file of element.files) {
      const li = document.createElement("li");
      li.className = "rvo-item-list__item";

      const container = document.createElement("div");
      container.className = "rvo-layout-row rvo-layout-gap--sm";

      const icon_el = document.createElement("span");
      icon_el.className =
        "utrecht-icon rvo-icon rvo-icon-document-met-lijnen rvo-icon--md rvo-icon--hemelblauw";
      icon_el.role = "img";
      icon_el.ariaLabel = "File";
      container.appendChild(icon_el);

      const text_el = document.createElement("span");
      text_el.textContent = file.name;
      container.appendChild(text_el);

      li.appendChild(container);

      list.appendChild(li);
    }
  }
}

function getAnchor() {
  const currentUrl = document.URL,
    urlParts = currentUrl.split("#");
  return urlParts.length > 1 ? urlParts[1] : null;
}

function scrollElementIntoViewClickAndBlur(id: string | null) {
  if (!id) {
    return;
  }
  const element = document.getElementById(id);
  if (element) {
    element.scrollIntoView({
      behavior: "smooth",
      block: "start",
      inline: "start",
    });
    element.click();
    element.blur();
  }
}

export function showRequirementDetails() {
  document.addEventListener("DOMContentLoaded", function () {
    scrollElementIntoViewClickAndBlur(getAnchor());
  });
}

export function searchInputChanged() {
  const clearElement: HTMLElement | null = (
    (event!.currentTarget as HTMLElement).parentNode as HTMLElement
  ).querySelector(".form-input-clear");
  if (!clearElement) {
    return;
  }
  if ((event!.target as HTMLInputElement).value != "") {
    clearElement.classList.remove("display-none");
  } else {
    clearElement.classList.add("display-none");
  }
}

export function resetSearchInput() {
  (event!.currentTarget as HTMLElement).classList.add("display-none");
  const inputElement: HTMLInputElement | null = (
    (event!.currentTarget as HTMLElement).parentNode as HTMLElement
  ).querySelector(".form-input-search");
  if (!inputElement) {
    return;
  }
  inputElement.value = "";
}

export function updateInlineEditorAIActProfile() {
  const jsonObject = JSON.parse(
    sessionStorage.getItem("labelsbysubcategory") as string,
  );
  const groupToFieldName = new Map<string, string>()
    .set("Rol", "role")
    .set("Soort toepassing", "type")
    .set("Risicogroep", "risk_group")
    .set("Conformiteitsbeoordelingsinstantie", "conformity_assessment_body")
    .set("Systeemrisico", "systemic_risk")
    .set("Transparantieverplichting", "transparency_obligations")
    .set("Open source", "open_source");
  for (const [groupName, formFieldName] of groupToFieldName) {
    const groupValues = jsonObject[groupName];
    const elements = document.querySelectorAll(
      '[name="' + formFieldName + '"]',
    );
    if (elements && elements.length > 1) {
      elements.forEach((element) => {
        if (
          element.getAttribute("type") === "radio" ||
          element.getAttribute("type") === "checkbox"
        ) {
          const labelValue = element.getAttribute("value");
          if (groupValues.includes(labelValue)) {
            element.setAttribute("checked", "checked");
          } else {
            element.removeAttribute("checked");
          }
        }
      });
    } else if (elements) {
      elements[0].querySelectorAll("option").forEach((optionElement) => {
        const labelValue = optionElement.getAttribute("value");
        if (groupValues.includes(labelValue)) {
          optionElement.setAttribute("selected", "selected");
        } else {
          optionElement.removeAttribute("selected");
        }
      });
    } else {
      console.error(`Element with name ${formFieldName} not found.`);
    }
  }
}

/**
 * Updates the hx-headers attribute of an element
 */
export function updateHxHeaders(
  elementId: string,
  key: string,
  value: string | number | boolean,
): void {
  const element: HTMLElement | null = document.getElementById(elementId);
  if (!element) {
    console.error(`Element with ID "${elementId}" not found`);
    return;
  }

  // Get the current hx-headers attribute
  const headersAttr: string | null = element.getAttribute("hx-headers");
  let headers: Record<string, string | number | boolean> = {};

  // Parse the existing headers if present
  if (headersAttr) {
    try {
      headers = JSON.parse(headersAttr) as Record<
        string,
        string | number | boolean
      >;
    } catch (error) {
      console.error("Invalid hx-headers JSON format:", error);
      return;
    }
  }
  headers[key] = value;
  element.setAttribute("hx-headers", JSON.stringify(headers));
}

export function updateFormStateAndSubmit(formId: string, nextState: string) {
  updateHxHeaders(formId, "X-Current-State", nextState);
  const currentForm = document.getElementById(formId);
  if (currentForm) {
    htmx.trigger(currentForm, "submit", {});
  }
}

interface HtmxBeforeSwapEvent extends Event {
  detail: {
    requestConfig: {
      elt: HTMLElement;
    };
    serverResponse: string;
  };
}

window.addEventListener("message", (event) => {
  //NOSONAR
  if (event.data.event === "beslishulp-done") {
    console.log("Received beslishulp-done:", event.data.value);
    if (window.location.pathname == "/algorithms/new") {
      closeModalSave("modal");
    } else if (/\/algorithm\/\d+\/details/.test(window.location.pathname)) {
      updateInlineEditorAIActProfile();
      closeAndResetDynamicModal("modal");
    } else {
      console.error("No handle found for location " + window.location.pathname);
    }
  }
});

window.addEventListener("openModal", () => {
  openModal("modal");
});

/**
 * This function is called when the htmx:beforeSwap event is triggered, checks if pre-processing is required and
 * what action to take.
 */
// @ts-expect-error : ignore the event type overload error
window.addEventListener(
  "htmx:beforeSwap",
  function (event: HtmxBeforeSwapEvent) {
    const sourceElement = event.detail.requestConfig.elt;
    if (sourceElement.hasAttribute("data-preprocess")) {
      const instruction = sourceElement.getAttribute("data-preprocess")!;
      const instructionParts = instruction.split(":");
      if (
        instructionParts.length === 2 &&
        instructionParts[0] === "exclude-if-exists-in"
      ) {
        const excludeValues: string[] = [];
        const targetIds = instructionParts[1].split(",");
        document
          .querySelectorAll(
            targetIds.map((id: string) => `${id} > *`).join(","),
          )
          .forEach((element) => {
            if (element.hasAttribute("data-value")) {
              excludeValues.push(element.getAttribute("data-value")!);
            }
          });
        const doc = new DOMParser().parseFromString(
          `<div>${event.detail.serverResponse}</div>`,
          "text/html",
        );
        let resultCount = 0;
        let totalCount = 0;
        doc.querySelectorAll("div > [data-value]").forEach((element) => {
          totalCount++;
          if (
            excludeValues.includes(element.getAttribute("data-value") as string)
          ) {
            element.remove();
          } else {
            resultCount++;
          }
        });
        const container = doc.body.querySelector("div");
        const sourceType = sourceElement.getAttribute("data-type");
        if (
          ((sourceType == "organization" &&
            totalCount > 0 &&
            resultCount == 0) ||
            (sourceType == "algorithm" && resultCount === 0)) &&
          container
        ) {
          container
            .querySelector("#no-persons-found-message")!
            .classList.remove("display-none");
        }
        event.detail.serverResponse = container
          ? container.innerHTML
          : event.detail.serverResponse;
      }
    }
  },
);

// for debugging htmx use -> htmx.logAll();
