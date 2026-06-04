function initPasswordToggles() {
    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        const inputId = button.getAttribute("aria-controls");
        const input = document.getElementById(inputId);
        if (!input) {
            return;
        }

        button.addEventListener("click", () => {
            const isHidden = input.type === "password";
            input.type = isHidden ? "text" : "password";
            button.textContent = isHidden ? "Hide" : "Show";
            button.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
        });
    });
}

document.addEventListener("DOMContentLoaded", initPasswordToggles);
