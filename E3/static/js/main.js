// JavaScript principal pour l'application Chatbot SAV

document.addEventListener("DOMContentLoaded", function () {
    initializeApp();
});

function initializeApp() {
    // Initialiser la sidebar responsive
    initSidebar();

    // Initialiser les tooltips Bootstrap
    initTooltips();

    // Initialiser les animations
    initAnimations();

    // Gérer les formulaires
    initForms();
}

// Gestion de la sidebar responsive
function initSidebar() {
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("sidebar");

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", function () {
            sidebar.classList.toggle("show");
        });

        // Fermer la sidebar en cliquant en dehors (mobile)
        document.addEventListener("click", function (event) {
            if (window.innerWidth <= 768) {
                if (
                    !sidebar.contains(event.target) &&
                    !sidebarToggle.contains(event.target)
                ) {
                    sidebar.classList.remove("show");
                }
            }
        });

        // Gérer le redimensionnement de la fenêtre
        window.addEventListener("resize", function () {
            if (window.innerWidth > 768) {
                sidebar.classList.remove("show");
            }
        });
    }
}

// Initialiser les tooltips Bootstrap
function initTooltips() {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Animations d'entrée pour les éléments
function initAnimations() {
    // Observer pour les animations au scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("fade-in");
            }
        });
    });

    // Observer tous les éléments avec la classe 'animate-on-scroll'
    document.querySelectorAll(".animate-on-scroll").forEach((el) => {
        observer.observe(el);
    });
}

// Gestion des formulaires
function initForms() {
    // Validation des formulaires Bootstrap
    const forms = document.querySelectorAll(".needs-validation");

    Array.from(forms).forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add("was-validated");
        });
    });

    // Auto-resize des textareas
    document.querySelectorAll("textarea").forEach((textarea) => {
        textarea.addEventListener("input", function () {
            this.style.height = "auto";
            this.style.height = this.scrollHeight + "px";
        });
    });
}

// Utilitaires pour les notifications
function showNotification(message, type = "info") {
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText =
        "top: 20px; right: 20px; z-index: 9999; min-width: 300px;";

    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    document.body.appendChild(alertDiv);

    // Auto-remove après 5 secondes
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Fonction pour confirmer les actions
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Utilitaire pour formater les dates
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString("fr-FR", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

// Utilitaire pour copier du texte dans le presse-papiers
function copyToClipboard(text) {
    navigator.clipboard
        .writeText(text)
        .then(() => {
            showNotification("Texte copié dans le presse-papiers !", "success");
        })
        .catch((err) => {
            console.error("Erreur lors de la copie:", err);
            showNotification("Erreur lors de la copie", "danger");
        });
}

// Gestion des erreurs globales
window.addEventListener("error", function (event) {
    console.error("Erreur JavaScript:", event.error);
    // En production, vous pourriez envoyer cette erreur à un service de logging
});

// Gestion des erreurs de promesses non capturées
window.addEventListener("unhandledrejection", function (event) {
    console.error("Promesse rejetée non capturée:", event.reason);
    event.preventDefault();
});

// Fonction pour débouncer les appels de fonction
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Fonction pour throttler les appels de fonction
function throttle(func, limit) {
    let inThrottle;
    return function () {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => (inThrottle = false), limit);
        }
    };
}

// Utilitaire pour les requêtes API
class ApiClient {
    static async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                "Content-Type": "application/json",
            },
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error("Erreur API:", error);
            throw error;
        }
    }

    static async get(url) {
        return this.request(url, { method: "GET" });
    }

    static async post(url, data) {
        return this.request(url, {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    static async put(url, data) {
        return this.request(url, {
            method: "PUT",
            body: JSON.stringify(data),
        });
    }

    static async delete(url) {
        return this.request(url, { method: "DELETE" });
    }
}

// Gestionnaire de loading global
class LoadingManager {
    static show(element = null) {
        if (element) {
            element.classList.add("loading");
        } else {
            document.body.classList.add("loading");
        }
    }

    static hide(element = null) {
        if (element) {
            element.classList.remove("loading");
        } else {
            document.body.classList.remove("loading");
        }
    }
}

// Export des fonctions utilitaires pour une utilisation globale
window.ChatbotSAV = {
    showNotification,
    confirmAction,
    formatDate,
    copyToClipboard,
    debounce,
    throttle,
    ApiClient,
    LoadingManager,
};
