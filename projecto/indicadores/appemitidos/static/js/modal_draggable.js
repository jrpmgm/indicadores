function makeModalDraggable(modalSelector) {
  const modal = document.querySelector(modalSelector);
  if (!modal) return;

  const dialog = modal.querySelector(".modal-dialog");
  const header = modal.querySelector(".modal-header");
  if (!dialog || !header) return;

  let isDragging = false;
  let startX = 0, startY = 0;
  let initialLeft = 0, initialTop = 0;

  header.style.cursor = "move";

  modal.addEventListener("shown.bs.modal", () => {
    setTimeout(() => {
      const rect = dialog.getBoundingClientRect();

      dialog.style.transform = "none";
      dialog.style.margin = "0";
      dialog.style.position = "fixed";
      dialog.style.top = `${(window.innerHeight - rect.height) / 2}px`;
      dialog.style.left = `${(window.innerWidth - rect.width) / 2}px`;
      dialog.style.width = `${rect.width}px`;
    }, 200);
  });

  header.addEventListener("mousedown", (e) => {
    if (e.target.closest(".btn-close")) return;

    isDragging = true;
    const rect = dialog.getBoundingClientRect();
    startX = e.clientX;
    startY = e.clientY;
    initialLeft = rect.left;
    initialTop = rect.top;

    document.body.style.userSelect = "none";
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;

    const dx = e.clientX - startX;
    const dy = e.clientY - startY;

    dialog.style.left = `${initialLeft + dx}px`;
    dialog.style.top = `${initialTop + dy}px`;
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    document.body.style.userSelect = "auto";
  });

  modal.addEventListener("hidden.bs.modal", () => {
    dialog.removeAttribute("style");
  });
}