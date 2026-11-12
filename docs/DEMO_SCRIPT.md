# PayPilot AI ACCESS: Official Video Demo Script

> **Target Duration:** 2 minutes 45 seconds (Under 2:50 hard limit).  
> **Format:** Screen recording with voiceover on the device it was built for (Windows 11 / Chrome browser).  
> **Music & Trademarks:** No copyrighted background music. No unendorsed brand claims.

---

## Shot-by-Shot Timeline

### [0:00 - 0:25] Scene 1: The Problem & Introduction
- **Visual:** Open on the PayPilot AI ACCESS landing page (`http://127.0.0.1:8000` or hosted Render URL). Show the clean high-contrast interface, yellow Sandbox banner at top, and voice toggle.
- **Voiceover:**
  > "For millions of older adults and visually impaired users, e-commerce has become a maze of cluttered filters, volatile pricing, and confusing checkout flows. Autonomous AI agents promise to help, but giving an AI authority to spend your money is risky.  
  > This is **PayPilot AI ACCESS**—an accessible, voice-first shopping assistant that grounds recommendations in real retailer inventory via Channel3 and verifies payments through PayPal Sandbox. The AI recommends; the customer always controls the money."

---

### [0:25 - 0:55] Scene 2: Live Voice Discovery & Retailer Clarity
- **Visual:** Click the **Speak** button. Speak clearly into the microphone:
  > *"Find me a jar opener for weak hands under $25"*
- **Action:**
  - Real-time transcript populates in the input field.
  - Speech synthesis immediately announces: *"Here are assistive jar openers that fit your budget."*
  - Three product cards load with images, exact prices ($2.99 to $16.99 USD), and retailer tags:
    - `"Sold by menards.com"`
    - `"Sold by kohls.com"`
    - `"Sold by containerstore.com"`
- **Voiceover:**
  > "PayPilot queries live inventory across retailers using Channel3. Every recommendation is checked against stored catalog data by our custom grounding engine. If a feature or price isn't found verbatim in the retailer's description, the model is blocked from claiming it. Notice the retailer attribution: 'Sold by Kohl's' with transparent Channel3 affiliate tracking links."

---

### [0:55 - 1:20] Scene 3: Anti-Fabrication & Over-Budget Honesty
- **Visual:** Enter an unrealistic search:
  > Query: *"diamond walking cane"*, Budget: *$10.00*
- **Action:** Click **Find Products**.
  - Assistant responds clearly: *"No products were found matching your criteria under $10.00. Try increasing your budget or broadening your search."*
- **Voiceover:**
  > "Notice what didn't happen: no fake products, no fabricated prices, and no silent fallbacks. If Channel3 has no matching in-stock items under budget, PayPilot tells the customer honestly and asks to refine the search. Anti-fabrication is enforced in code, not just in prompts."

---

### [1:20 - 1:50] Scene 4: Price Lock Quote & Customer Total Confirmation
- **Visual:** Return to the first query (*"sturdy wooden walking stick under $40"*). Select the **Natural Wood Walking Cane** at **$39.99 USD**. Click **Review & Lock Price**.
- **Action:**
  - Modal/Step opens: Price is locked with a 10-minute server timer.
  - Review order screen shows breakdown: Quantity 1, Total $39.99 USD.
  - Click **Confirm Total & Proceed to Payment**.
- **Voiceover:**
  > "Before touching payment, PayPilot creates a server-side price lock quote valid for 10 minutes. The browser never sends price amounts to the backend—only quote IDs and quantities. The customer must explicitly confirm the exact total before any PayPal order can be created."

---

### [1:50 - 2:25] Scene 5: Verified PayPal Sandbox Checkout
- **Visual:** Standard PayPal buttons render. Click the **PayPal** button.
- **Action:**
  - PayPal Sandbox popup opens.
  - Log in with dedicated sandbox test account (`John Doe`, US buyer).
  - Select funding source and click **Complete Purchase**.
  - Modal closes, backend captures payment, and transitions immediately to the verified **Receipt Page**.
  - Receipt displays:
    - Order Status: `COMPLETED`
    - Capture Status: `COMPLETED`
    - Amount & Currency: `$39.99 USD`
    - Internal Order ID & PayPal Capture ID
    - PayPal Debug ID for full auditability
- **Voiceover:**
  > "The customer approves the order directly on PayPal. Behind the scenes, our server captures the payment and verifies four strict invariants: order status is COMPLETED, capture status is COMPLETED, the amount matches the locked quote down to the penny, and the internal order ID matches. Only when all four pass does it generate a verified receipt."

---

### [2:25 - 2:45] Scene 6: "What the Assistant Did" Audit Trail & Conclusion
- **Visual:** On the receipt page, click **What the assistant did** to expand the timeline.
- **Action:**
  - Reveal server-generated timeline:
    - *Channel3 search: 3 products retrieved in 480ms*
    - *Grounding validation: 3 products verified verbatim*
    - *Price locked: $39.99 USD (walmart.com)*
    - *Customer confirmation: $39.99 USD approved*
    - *PayPal capture verified: Capture ID matched, Debug ID recorded*
  - Pan to top banner: *"Sandbox payment, no real purchase. No real money moved."*
- **Voiceover:**
  > "Every single step is logged in an unalterable server-side timeline built directly from database records—zero model hallucinations, zero secret leakage.  
  > This is PayPilot AI ACCESS: accessible, grounded, and keeping the human customer firmly in control of commerce. Thank you."

---

## Production Recording Checklist
- [ ] Windows display scale set to 100% or 125% for crisp text readability.
- [ ] Web Speech microphone input enabled and tested.
- [ ] Speaker volume audible for text-to-speech output.
- [ ] Sandbox buyer account credentials pre-cached or ready in clipboard.
- [ ] Recording timer stopwatch visible to guarantee under 2:50 duration.
