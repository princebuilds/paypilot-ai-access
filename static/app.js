// ============================================================================
// PayPilot AI ACCESS - Core Frontend Application
// Rules:
// 1. All dynamic text is rendered strictly with textContent / DOM APIs (no direct HTML injection).
// 2. Client NEVER sends price or amount to orders or capture endpoints.
// 3. PayPal client-id is fetched dynamically from /api/config.
// 4. Voice-first: Web Speech API recognition + speechSynthesis TTS.
// 5. Accessible: keyboard navigable, ARIA live region announcements, focus management.
// ============================================================================

(function () {
  "use strict";

  // Application State
  const state = {
    ttsEnabled: true,
    isListening: false,
    currentQuote: null,
    currentOrder: null,
    paypalSdkLoaded: false,
    paypalButtonsRendered: false,
    recognition: null,
  };

  // DOM Elements
  const agentMessageEl = document.getElementById("agent-message");
  const agentSubEl = document.getElementById("agent-state-sub");
  const liveAnnouncerEl = document.getElementById("live-announcer");
  const liveAlertEl = document.getElementById("live-alert");

  const searchFormEl = document.getElementById("search-form");
  const requestInputEl = document.getElementById("request-input");
  const budgetInputEl = document.getElementById("budget-input");
  const micBtnEl = document.getElementById("mic-btn");
  const submitBtnEl = document.getElementById("submit-btn");
  const ttsToggleEl = document.getElementById("tts-toggle");
  const ttsLabelEl = document.getElementById("tts-label");

  const resultsSectionEl = document.getElementById("results-section");
  const productsListEl = document.getElementById("products-list");
  const channel3MetaEl = document.getElementById("channel3-meta");

  const quoteSectionEl = document.getElementById("quote-section");
  const quoteDetailsEl = document.getElementById("quote-details");
  const confirmTotalDisplayEl = document.getElementById("confirm-total-display");
  const confirmQuoteBtnEl = document.getElementById("confirm-quote-btn");
  const cancelQuoteBtnEl = document.getElementById("cancel-quote-btn");
  const paypalWrapperEl = document.getElementById("paypal-container-wrapper");
  const paypalButtonContainerEl = document.getElementById("paypal-button-container");

  // ==========================================================================
  // Assistant Speech & Announcer Utilities
  // ==========================================================================

  function updateAssistant(message, subState, speak = true, isAlert = false) {
    if (agentMessageEl) {
      agentMessageEl.textContent = message;
    }
    if (agentSubEl && subState) {
      agentSubEl.textContent = subState;
    }

    // Accessible live region announcement
    if (isAlert && liveAlertEl) {
      liveAlertEl.textContent = "";
      setTimeout(() => { liveAlertEl.textContent = message; }, 50);
    } else if (liveAnnouncerEl) {
      liveAnnouncerEl.textContent = "";
      setTimeout(() => { liveAnnouncerEl.textContent = message; }, 50);
    }

    // Spoken voice output via Web Speech Synthesis
    if (speak && state.ttsEnabled && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(message);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      utterance.lang = "en-US";
      window.speechSynthesis.speak(utterance);
    }
  }

  // ==========================================================================
  // Web Speech API Voice Recognition
  // ==========================================================================

  function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      if (micBtnEl) {
        micBtnEl.title = "Voice input is not supported in this browser. Please type below.";
      }
      return;
    }

    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = "en-US";

    rec.onstart = () => {
      state.isListening = true;
      micBtnEl.classList.add("listening");
      micBtnEl.setAttribute("aria-pressed", "true");
      updateAssistant("I am listening.", "Listening", false);
    };

    rec.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (requestInputEl) {
        requestInputEl.value = transcript;
        requestInputEl.focus();
      }
      updateAssistant('Heard: "' + transcript + '". Searching now.', "Processing", false);
      handleAgentSearch(transcript, budgetInputEl ? budgetInputEl.value : null);
    };

    rec.onerror = (event) => {
      state.isListening = false;
      micBtnEl.classList.remove("listening");
      micBtnEl.setAttribute("aria-pressed", "false");
      if (event.error !== "no-speech") {
        updateAssistant("Could not hear speech. You can type in the box.", "Ready", false);
      }
    };

    rec.onend = () => {
      state.isListening = false;
      micBtnEl.classList.remove("listening");
      micBtnEl.setAttribute("aria-pressed", "false");
    };

    state.recognition = rec;
  }

  function toggleSpeechRecognition() {
    if (!state.recognition) {
      updateAssistant("Voice recognition is not available in this browser. Type below.", "Ready", true);
      return;
    }

    if (state.isListening) {
      state.recognition.stop();
    } else {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      state.recognition.start();
    }
  }

  // ==========================================================================
  // Dynamic PayPal SDK Initialization
  // ==========================================================================

  async function loadPayPalSdk() {
    if (state.paypalSdkLoaded || window.paypal) {
      state.paypalSdkLoaded = true;
      return true;
    }

    try {
      const res = await fetch("/api/config");
      if (!res.ok) {
        return false;
      }
      const cfg = await res.json();
      if (!cfg.paypal_client_id) {
        return false;
      }

      return new Promise((resolve) => {
        const script = document.createElement("script");
        script.src = "https://www.paypal.com/sdk/js?client-id=" + encodeURIComponent(cfg.paypal_client_id) + "&currency=USD&intent=capture&components=buttons";
        script.onload = () => {
          state.paypalSdkLoaded = true;
          resolve(true);
        };
        script.onerror = () => {
          resolve(false);
        };
        document.head.appendChild(script);
      });
    } catch (e) {
      return false;
    }
  }

  // ==========================================================================
  // Agent Query Execution (POST /api/agent)
  // ==========================================================================

  async function handleAgentSearch(message, budget) {
    const cleanMsg = (message || "").trim();
    if (!cleanMsg) {
      updateAssistant("Please type or speak what you are looking for.", "Idle", true);
      return;
    }

    // Hide any previous quote / results during fresh search
    if (quoteSectionEl) quoteSectionEl.hidden = true;
    if (resultsSectionEl) resultsSectionEl.hidden = true;
    if (productsListEl) {
      while (productsListEl.firstChild) {
        productsListEl.removeChild(productsListEl.firstChild);
      }
    }

    updateAssistant("Looking for products now.", "Searching", true);
    if (submitBtnEl) submitBtnEl.disabled = true;

    const payload = { message: cleanMsg };
    if (budget && String(budget).trim() !== "") {
      payload.budget = parseFloat(budget).toFixed(2);
    }

    try {
      const res = await fetch("/api/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const errCode = errData.error ? errData.error.code : "";
        let friendlyMsg = "Something went wrong. Please try again.";

        if (res.status === 429 || errCode === "RATE_LIMITED") {
          friendlyMsg = (errData.error && errData.error.message) ? errData.error.message : "Many people are using this demo. Please wait a minute and try again.";
        } else if (errCode === "AI_SERVICE_UNAVAILABLE" || res.status === 503) {
          friendlyMsg = (errData.error && errData.error.message) ? errData.error.message : "The assistant is not responding. Please try again.";
        } else if (errCode === "UPSTREAM_ERROR" || res.status === 502) {
          friendlyMsg = (errData.error && errData.error.message) ? errData.error.message : "The product service is not responding. Please try again.";
        }

        updateAssistant(friendlyMsg, "Error", true, true);
        return;
      }

      const data = await res.json();

      // Check clarifying question
      if (data.clarifying_question && (!data.recommendations || data.recommendations.length === 0)) {
        updateAssistant(data.clarifying_question, "Clarification Needed", true);
        return;
      }

      // Check if recommendations exist
      const recs = data.recommendations || [];
      if (recs.length === 0) {
        updateAssistant("I could not find a confident match. Try describing it another way.", "No Match", true);
        return;
      }

      // Render recommendations
      renderRecommendations(recs, data.live_data);

      const count = recs.length;
      const countMsg = "I found " + count + " options. Here is why each one may fit.";
      updateAssistant(countMsg, "Results", true);

    } catch (e) {
      updateAssistant("Network error connecting to assistant. Please try again.", "Error", true, true);
    } finally {
      if (submitBtnEl) submitBtnEl.disabled = false;
    }
  }

  // ==========================================================================
  // Render Product Recommendation Cards (Strictly via DOM APIs)
  // ==========================================================================

  function renderRecommendations(recs, liveData) {
    if (!productsListEl || !resultsSectionEl) return;

    while (productsListEl.firstChild) {
      productsListEl.removeChild(productsListEl.firstChild);
    }

    if (channel3MetaEl && liveData) {
      const fetchTime = liveData.fetched_at ? new Date(liveData.fetched_at).toLocaleTimeString() : "recently";
      channel3MetaEl.textContent = "Live data from Channel3, fetched at " + fetchTime;
    }

    recs.forEach((prod, index) => {
      const card = document.createElement("article");
      card.className = "product-card";
      card.setAttribute("role", "listitem");
      card.setAttribute("aria-labelledby", "prod-title-" + index);

      // Product Image
      if (prod.image_url) {
        const imgWrap = document.createElement("div");
        imgWrap.className = "product-img-wrapper";
        const img = document.createElement("img");
        img.src = prod.image_url;
        img.alt = prod.title || "Product image";
        img.className = "product-img";
        img.loading = "lazy";
        imgWrap.appendChild(img);
        card.appendChild(imgWrap);
      }

      // Product Title
      const titleEl = document.createElement("h3");
      titleEl.id = "prod-title-" + index;
      titleEl.className = "product-title";
      titleEl.textContent = prod.title || "Product";
      card.appendChild(titleEl);

      // Price & Merchant Bar
      const priceBar = document.createElement("div");
      priceBar.className = "product-price-bar";

      const priceEl = document.createElement("span");
      priceEl.className = "product-price";
      priceEl.textContent = "$" + (prod.price || "0.00") + " " + (prod.currency || "USD");
      priceBar.appendChild(priceEl);

      const merchantEl = document.createElement("span");
      merchantEl.className = "product-merchant";
      merchantEl.textContent = prod.merchant_domain || "channel3";
      priceBar.appendChild(merchantEl);

      card.appendChild(priceBar);

      // Reasons Box
      if (prod.reasons && prod.reasons.length > 0) {
        const reasonsBox = document.createElement("div");
        reasonsBox.className = "reasons-box";

        const reasonsTitle = document.createElement("h4");
        reasonsTitle.className = "reasons-title";
        reasonsTitle.textContent = "Why PayPilot recommends this:";
        reasonsBox.appendChild(reasonsTitle);

        const reasonsList = document.createElement("ul");
        reasonsList.className = "reasons-list";

        prod.reasons.forEach((r) => {
          const item = document.createElement("li");
          const claimSpan = document.createElement("span");
          claimSpan.textContent = r.claim;
          item.appendChild(claimSpan);

          if (r.evidence_text) {
            const evSpan = document.createElement("span");
            evSpan.className = "evidence-tag";
            evSpan.textContent = 'Evidence (' + r.evidence_field + '): "' + r.evidence_text + '"';
            item.appendChild(evSpan);
          }
          reasonsList.appendChild(item);
        });

        reasonsBox.appendChild(reasonsList);
        card.appendChild(reasonsBox);
      }

      // Select / Request Quote Button
      const actionWrap = document.createElement("div");
      actionWrap.className = "card-action";

      if (prod.purchasable) {
        const quoteBtn = document.createElement("button");
        quoteBtn.type = "button";
        quoteBtn.className = "primary-btn";
        quoteBtn.style.width = "100%";
        quoteBtn.textContent = "Select & Lock Price";
        quoteBtn.addEventListener("click", () => {
          requestQuote(prod.snapshot_id, 1, budgetInputEl ? budgetInputEl.value : null);
        });
        actionWrap.appendChild(quoteBtn);
      } else {
        const unavailMsg = document.createElement("p");
        unavailMsg.className = "meta-notice";
        unavailMsg.style.color = "var(--color-failed)";
        unavailMsg.textContent = prod.not_purchasable_reason || "Currently unavailable in Sandbox USD.";
        actionWrap.appendChild(unavailMsg);
      }

      card.appendChild(actionWrap);
      productsListEl.appendChild(card);
    });

    resultsSectionEl.hidden = false;
  }

  // ==========================================================================
  // Quote Generation & Price Lock (POST /api/quotes)
  // ==========================================================================

  async function requestQuote(snapshotId, quantity = 1, budget = null) {
    updateAssistant("Locking price and checking live availability...", "Quoting", true);

    const payload = {
      snapshot_id: snapshotId,
      quantity: quantity,
    };
    if (budget && String(budget).trim() !== "") {
      payload.budget = parseFloat(budget).toFixed(2);
    }

    try {
      const res = await fetch("/api/quotes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const errData = err.error || {};
        if (errData.code === "BUDGET_EXCEEDED") {
          updateAssistant(errData.message || "That is above your budget. You can raise the budget or pick another item.", "Budget Exceeded", true, true);
        } else if (errData.code === "PRICE_CHANGED") {
          updateAssistant(errData.message || "The price changed. Please confirm again.", "Price Changed", true, true);
        } else if (errData.code === "NOT_PURCHASABLE") {
          updateAssistant("This item is unavailable or not priced in USD.", "Unavailable", true, true);
        } else {
          updateAssistant(errData.message || "Could not generate quote.", "Error", true, true);
        }
        return;
      }

      const quote = await res.json();
      state.currentQuote = quote;

      // Render Quote Details
      renderQuote(quote);

      const quoteSpeech = quote.title + ", quantity " + quote.quantity + ". The total is $" + quote.total + (quote.budget ? ". Your budget is $" + quote.budget + "." : ".");
      updateAssistant(quoteSpeech, "Quote Locked", true);

      // Focus management: move focus programmatically to confirm action
      if (confirmQuoteBtnEl) {
        confirmQuoteBtnEl.focus();
      }

    } catch (e) {
      updateAssistant("Network error creating quote. Please try again.", "Error", true, true);
    }
  }

  function renderQuote(quote) {
    if (!quoteSectionEl || !quoteDetailsEl) return;

    while (quoteDetailsEl.firstChild) {
      quoteDetailsEl.removeChild(quoteDetailsEl.firstChild);
    }

    // Product Title
    const title = document.createElement("h3");
    title.textContent = quote.title;
    quoteDetailsEl.appendChild(title);

    // Quantity and Unit Price
    const pDetails = document.createElement("p");
    pDetails.textContent = "Quantity: " + quote.quantity + " × $" + quote.unit_price + " " + quote.currency;
    quoteDetailsEl.appendChild(pDetails);

    // Total
    const pTotal = document.createElement("p");
    pTotal.style.fontSize = "1.3rem";
    pTotal.style.fontWeight = "800";
    pTotal.style.color = "var(--color-primary)";
    pTotal.textContent = "Exact Total: $" + quote.total + " " + quote.currency;
    quoteDetailsEl.appendChild(pTotal);

    if (confirmTotalDisplayEl) {
      confirmTotalDisplayEl.textContent = "$" + quote.total;
    }

    if (paypalWrapperEl) {
      paypalWrapperEl.hidden = true;
    }
    if (confirmQuoteBtnEl) {
      confirmQuoteBtnEl.hidden = false;
      confirmQuoteBtnEl.disabled = false;
    }

    quoteSectionEl.hidden = false;
  }

  // ==========================================================================
  // Quote Confirmation (POST /api/quotes/{id}/confirm)
  // ==========================================================================

  async function confirmCurrentQuote() {
    if (!state.currentQuote) return;

    updateAssistant("Confirming total with server...", "Confirming", false);
    if (confirmQuoteBtnEl) confirmQuoteBtnEl.disabled = true;

    try {
      const res = await fetch("/api/quotes/" + encodeURIComponent(state.currentQuote.quote_id) + "/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Exact total confirmation per SPEC.md Section 4
        body: JSON.stringify({ confirmed_total: state.currentQuote.total }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const errData = err.error || {};
        updateAssistant(errData.message || "Confirmation failed. Quote may have expired.", "Error", true, true);
        if (confirmQuoteBtnEl) confirmQuoteBtnEl.disabled = false;
        return;
      }

      // Confirmed successfully! Prepare PayPal buttons
      if (confirmQuoteBtnEl) confirmQuoteBtnEl.hidden = true;
      if (paypalWrapperEl) paypalWrapperEl.hidden = false;

      updateAssistant("PayPal will open. Approve there when you are ready.", "Ready for PayPal", true);

      // Render PayPal Standard Checkout Buttons
      renderPayPalButtons();

    } catch (e) {
      updateAssistant("Error confirming quote. Please try again.", "Error", true, true);
      if (confirmQuoteBtnEl) confirmQuoteBtnEl.disabled = false;
    }
  }

  // ==========================================================================
  // PayPal Standard Checkout Button Wiring
  // ==========================================================================

  async function renderPayPalButtons() {
    if (!state.currentQuote || !paypalButtonContainerEl) return;

    while (paypalButtonContainerEl.firstChild) {
      paypalButtonContainerEl.removeChild(paypalButtonContainerEl.firstChild);
    }

    const loaded = await loadPayPalSdk();
    if (!loaded || !window.paypal || !window.paypal.Buttons) {
      updateAssistant("PayPal Sandbox SDK could not load. Please check your network or credentials.", "PayPal Error", true, true);
      return;
    }

    window.paypal.Buttons({
      style: {
        layout: "vertical",
        color: "gold",
        shape: "rect",
        label: "paypal",
      },

      // 1. Create Order: Server receives ONLY quote_id (browser never sends amounts)
      createOrder: async () => {
        try {
          const res = await fetch("/api/orders", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ quote_id: state.currentQuote.quote_id }),
          });

          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error ? err.error.message : "Failed to create PayPal order.");
          }

          const orderData = await res.json();
          state.currentOrder = orderData;
          return orderData.paypal_order_id;
        } catch (e) {
          updateAssistant("Could not create PayPal order: " + e.message, "Order Creation Error", true, true);
          throw e;
        }
      },

      // 2. On Approve: Capture server-side and verify invariants
      onApprove: async (data) => {
        updateAssistant("Verifying Sandbox payment with server...", "Verifying", true);

        try {
          const orderId = state.currentOrder ? state.currentOrder.order_id : null;
          if (!orderId) {
            throw new Error("Missing internal order reference.");
          }

          const res = await fetch("/api/orders/" + encodeURIComponent(orderId) + "/capture", {
            method: "POST",
          });

          const captureData = await res.json();

          if (captureData.status === "CAPTURED_VERIFIED") {
            const successMsg = "Payment verified. This was a Sandbox test, so no real money moved and no order was placed with the store.";
            updateAssistant(successMsg, "Verified", true);
            setTimeout(() => {
              window.location.href = captureData.receipt_url || ("/receipt.html?order=" + encodeURIComponent(orderId));
            }, 1200);
          } else if (captureData.status === "PENDING") {
            updateAssistant("PayPal says this payment is still pending. Do not treat it as paid.", "Pending", true);
          } else {
            updateAssistant("The payment did not go through. You were not charged.", "Payment Failed", true, true);
          }
        } catch (e) {
          updateAssistant("Verification error: " + e.message, "Verification Failed", true, true);
        }
      },

      // 3. On Cancel: Notify server and inform user
      onCancel: async () => {
        if (state.currentOrder && state.currentOrder.order_id) {
          fetch("/api/orders/" + encodeURIComponent(state.currentOrder.order_id) + "/cancel", { method: "POST" });
        }
        updateAssistant("You cancelled. Nothing was charged.", "Cancelled", true);
      },

      // 4. On Error: Leave quote usable and show plain-language error
      onError: (err) => {
        updateAssistant("Payment error occurred in PayPal Sandbox. Your quote is still valid.", "PayPal Error", true, true);
      },
    }).render("#paypal-button-container");
  }

  // ==========================================================================
  // Event Listeners & Setup
  // ==========================================================================

  document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize Speech Recognition
    initSpeechRecognition();

    // 2. Pre-fetch client config and PayPal SDK asynchronously
    loadPayPalSdk();

    // 3. Search Form Submit
    if (searchFormEl) {
      searchFormEl.addEventListener("submit", (e) => {
        e.preventDefault();
        const msg = requestInputEl ? requestInputEl.value : "";
        const bgt = budgetInputEl ? budgetInputEl.value : null;
        handleAgentSearch(msg, bgt);
      });
    }

    // 4. Mic Button Click
    if (micBtnEl) {
      micBtnEl.addEventListener("click", () => {
        toggleSpeechRecognition();
      });
    }

    // 5. TTS Voice Output Toggle
    if (ttsToggleEl && ttsLabelEl) {
      ttsToggleEl.addEventListener("click", () => {
        state.ttsEnabled = !state.ttsEnabled;
        ttsToggleEl.setAttribute("aria-pressed", state.ttsEnabled ? "true" : "false");
        ttsLabelEl.textContent = state.ttsEnabled ? "Voice: On" : "Voice: Off";
        if (!state.ttsEnabled && "speechSynthesis" in window) {
          window.speechSynthesis.cancel();
        }
      });
    }

    // 6. Confirm Quote Button
    if (confirmQuoteBtnEl) {
      confirmQuoteBtnEl.addEventListener("click", () => {
        confirmCurrentQuote();
      });
    }

    // 7. Cancel Quote Button
    if (cancelQuoteBtnEl) {
      cancelQuoteBtnEl.addEventListener("click", () => {
        state.currentQuote = null;
        if (quoteSectionEl) quoteSectionEl.hidden = true;
        updateAssistant("Quote cancelled. Tell me what else you need.", "Idle", true);
        if (requestInputEl) requestInputEl.focus();
      });
    }
  });

})();
