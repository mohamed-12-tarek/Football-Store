document.addEventListener("DOMContentLoaded", function () {
  // Initialize all features
  initializeNavigation();
  initializeScrollEffects();
  autoHideFlashMessages();
});

function initializeNavigation() {
  // Mobile menu toggle (if needed for future mobile optimization)
  const navToggle = document.querySelector(".nav-toggle");
  const navMenu = document.querySelector(".nav-menu");

  if (navToggle) {
    navToggle.addEventListener("click", function () {
      navMenu.classList.toggle("active");
    });
  }
}

function initializeScrollEffects() {
  // Add scroll effect to navbar
  let lastScroll = 0;
  const navbar = document.querySelector(".navbar");

  window.addEventListener("scroll", function () {
    const currentScroll = window.pageYOffset;

    if (currentScroll > 100) {
      navbar.style.boxShadow = "0 4px 20px rgba(0, 20, 64, 0.2)";
    } else {
      navbar.style.boxShadow = "0 2px 10px rgba(0, 20, 64, 0.1)";
    }

    lastScroll = currentScroll;
  });

  // Animate elements on scroll
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -100px 0px",
  };

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1";
        entry.target.style.transform = "translateY(0)";
      }
    });
  }, observerOptions);

  // Observe all product cards and ticket cards
  const animatedElements = document.querySelectorAll(
    ".product-card, .ticket-card, .feature-box, .stat-card"
  );
  animatedElements.forEach((el) => {
    el.style.opacity = "0";
    el.style.transform = "translateY(30px)";
    el.style.transition = "all 0.6s ease";
    observer.observe(el);
  });
}

function autoHideFlashMessages() {
  const flashMessages = document.querySelectorAll(".flash-message");

  flashMessages.forEach((message) => {
    setTimeout(() => {
      message.style.opacity = "0";
      message.style.transform = "translateX(100px)";
      setTimeout(() => message.remove(), 300);
    }, 5000);
  });
}

function addToCart(itemId, itemType, quantity = 1) {
  fetch("/add-to-cart", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      item_id: itemId,
      item_type: itemType,
      quantity: quantity,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Item added to cart!", "success");
        updateCartCount(data.cart_count);

        // Add animation to cart icon
        const cartIcon = document.querySelector(".cart-icon");
        if (cartIcon) {
          cartIcon.classList.add("pulse");
          setTimeout(() => cartIcon.classList.remove("pulse"), 600);
        }
      } else {
        showNotification(data.message || "Error adding item to cart", "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("An error occurred. Please try again.", "error");
    });
}

function updateCartCount(count) {
  const cartBadge = document.getElementById("cart-count");
  if (cartBadge) {
    cartBadge.textContent = count;

    // Animate the badge
    cartBadge.style.transform = "scale(1.3)";
    setTimeout(() => {
      cartBadge.style.transform = "scale(1)";
    }, 200);
  }
}

function updateCartQuantity(cartKey, newQuantity) {
  if (newQuantity < 1) {
    if (confirm("Remove this item from cart?")) {
      window.location.href = `/remove-from-cart/${cartKey}`;
    }
    return;
  }

  fetch("/update-cart", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      cart_key: cartKey,
      quantity: newQuantity,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        location.reload();
      } else {
        showNotification("Error updating cart", "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("An error occurred. Please try again.", "error");
    });
}

function showNotification(message, type = "success") {
  const notification = document.createElement("div");
  notification.className = `notification notification-${type}`;
  notification.innerHTML = `
        <i class="fas fa-${
          type === "success" ? "check-circle" : "exclamation-circle"
        }"></i>
        <span>${message}</span>
    `;

  document.body.appendChild(notification);

  // Trigger animation
  setTimeout(() => {
    notification.classList.add("show");
  }, 100);

  // Remove notification after 3 seconds
  setTimeout(() => {
    notification.classList.remove("show");
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

function increaseQuantity(maxStock) {
  const input = document.getElementById("quantity");
  if (input && parseInt(input.value) < maxStock) {
    input.value = parseInt(input.value) + 1;
  }
}

function decreaseQuantity() {
  const input = document.getElementById("quantity");
  if (input && parseInt(input.value) > 1) {
    input.value = parseInt(input.value) - 1;
  }
}

function initializeSearch() {
  const searchInput = document.querySelector(".search-input");
  const searchForm = document.querySelector(".search-form");

  if (searchForm) {
    searchForm.addEventListener("submit", function (e) {
      if (!searchInput.value.trim()) {
        e.preventDefault();
        showNotification("Please enter a search term", "error");
      }
    });
  }
}

function initializeLazyLoading() {
  const images = document.querySelectorAll("img[data-src]");

  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute("data-src");
        observer.unobserve(img);
      }
    });
  });

  images.forEach((img) => imageObserver.observe(img));
}

function validateCheckoutForm() {
  const form = document.getElementById("checkoutForm");
  if (!form) return true;

  const address = document.getElementById("address").value;
  const city = document.getElementById("city").value;
  const country = document.getElementById("country").value;
  const cardNumber = document.getElementById("card_number").value;
  const expiry = document.getElementById("expiry").value;
  const cvv = document.getElementById("cvv").value;

  if (!address || !city || !country) {
    showNotification("Please fill in all shipping details", "error");
    return false;
  }

  if (!cardNumber || !expiry || !cvv) {
    showNotification("Please fill in all payment details", "error");
    return false;
  }

  // Basic card number validation (should be 16 digits)
  const cleanCardNumber = cardNumber.replace(/\s/g, "");
  if (!/^\d{16}$/.test(cleanCardNumber)) {
    showNotification("Please enter a valid 16-digit card number", "error");
    return false;
  }

  // Expiry validation (MM/YY format)
  if (!/^\d{2}\/\d{2}$/.test(expiry)) {
    showNotification("Please enter expiry date in MM/YY format", "error");
    return false;
  }

  // CVV validation (3 digits)
  if (!/^\d{3}$/.test(cvv)) {
    showNotification("Please enter a valid 3-digit CVV", "error");
    return false;
  }

  return true;
}

function placeOrder() {
  if (!validateCheckoutForm()) {
    return;
  }

  const form = document.getElementById("checkoutForm");
  const formData = new FormData(form);

  // Show loading state
  const submitButton = event.target;
  const originalText = submitButton.innerHTML;
  submitButton.innerHTML =
    '<i class="fas fa-spinner fa-spin"></i> Processing...';
  submitButton.disabled = true;

  fetch("/place-order", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification(
          `Order placed successfully! Order #${data.order_number}`,
          "success"
        );
        setTimeout(() => {
          window.location.href = "/";
        }, 2000);
      } else {
        showNotification("Error: " + data.message, "error");
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("An error occurred. Please try again.", "error");
      submitButton.innerHTML = originalText;
      submitButton.disabled = false;
    });
}

function showAddProductModal() {
  const modal = document.getElementById("addProductModal");
  if (modal) {
    modal.style.display = "flex";
    document.body.style.overflow = "hidden";
  }
}

function showAddTicketModal() {
  const modal = document.getElementById("addTicketModal");
  if (modal) {
    modal.style.display = "flex";
    document.body.style.overflow = "hidden";
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = "none";
    document.body.style.overflow = "auto";
  }
}

function submitProduct() {
  const form = document.getElementById("addProductForm");
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  const formData = new FormData(form);

  fetch("/admin/add-product", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Product added successfully!", "success");
        closeModal("addProductModal");
        setTimeout(() => location.reload(), 1000);
      } else {
        showNotification("Error: " + data.message, "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("An error occurred. Please try again.", "error");
    });
}

function submitTicket() {
  const form = document.getElementById("addTicketForm");
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  const formData = new FormData(form);

  fetch("/admin/add-ticket", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification("Ticket added successfully!", "success");
        closeModal("addTicketModal");
        setTimeout(() => location.reload(), 1000);
      } else {
        showNotification("Error: " + data.message, "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("An error occurred. Please try again.", "error");
    });
}

// Close modal when clicking outside
window.addEventListener("click", function (event) {
  if (event.target.classList.contains("modal")) {
    event.target.style.display = "none";
    document.body.style.overflow = "auto";
  }
});

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}


const style = document.createElement("style");
style.textContent = `
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); }
    }
    .cart-icon.pulse {
        animation: pulse 0.6s ease-in-out;
    }
`;
document.head.appendChild(style);

window.addEventListener("load", function () {
  initializeSearch();
  initializeLazyLoading();

  console.log("⚽ Football Store loaded successfully!");
});
