"""Generate sample knowledge-base PDFs for NovaTech Solutions.

Run:  python generate_knowledge_base.py
Output: knowledge_base/*.pdf
"""

import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
os.makedirs(OUTPUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("DocTitle", parent=styles["Title"], fontSize=20, spaceAfter=20)
heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=14, spaceAfter=10, spaceBefore=16)
body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=11, leading=15, spaceAfter=8)
sub_heading = ParagraphStyle("SubHeading", parent=styles["Heading3"], fontSize=12, spaceAfter=8, spaceBefore=12)


def build_pdf(filename: str, title: str, sections: list[tuple[str, str]]):
    """Build a PDF from a list of (heading, body_text) tuples."""
    path = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(path, pagesize=LETTER, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    story = [Paragraph(title, title_style), Spacer(1, 12)]
    for heading, body in sections:
        story.append(Paragraph(heading, heading_style))
        for para in body.strip().split("\n\n"):
            story.append(Paragraph(para.strip(), body_style))
        story.append(Spacer(1, 6))
    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────
# 1. Company Overview
# ─────────────────────────────────────────────────────────────
build_pdf("NovaTech_Company_Overview.pdf", "NovaTech Solutions — Company Overview", [
    ("About NovaTech Solutions", """
NovaTech Solutions is a technology company founded in 2018 and headquartered in Austin, Texas. We specialize in cloud-based productivity software, smart home devices, and enterprise IT solutions. Our mission is to make technology accessible, reliable, and delightful for individuals and businesses of all sizes.

We serve over 500,000 customers across North America, Europe, and Asia-Pacific. Our product lineup includes the NovaTech Cloud Suite (productivity and collaboration tools), the NovaHome smart home ecosystem, and NovaTech Enterprise solutions for businesses.

NovaTech is publicly traded on NASDAQ under the ticker symbol NVTK. We employ approximately 2,400 people worldwide with offices in Austin, London, Berlin, and Singapore.
"""),
    ("Our Values", """
Customer First: Every decision we make starts with the question "How does this help our customers?" We are committed to providing world-class support within 24 hours for all inquiries.

Innovation with Purpose: We build technology that solves real problems. We avoid feature bloat and focus on making our products intuitive and reliable.

Transparency: We communicate openly about our products, pricing, data practices, and any incidents that affect our customers. Our status page at status.novatech.com is updated in real-time.

Sustainability: We are carbon-neutral since 2023. All NovaTech hardware is made from at least 60% recycled materials and is designed for a minimum 5-year lifespan.
"""),
    ("Contact Information", """
General Support: support@novatech.com or call 1-800-NOVA-TECH (1-800-668-2832), available Monday through Friday 8 AM to 8 PM Central Time, and Saturday 9 AM to 5 PM Central Time.

Enterprise Support: enterprise@novatech.com or call 1-800-NOVA-BIZ (1-800-668-2249). Enterprise customers with a Premium Support plan have access to 24/7 phone support and a dedicated account manager.

Live Chat: Available on our website novatech.com during business hours. Average wait time is under 2 minutes.

Social Media: Twitter/X @NovaTechSupport, Facebook /NovaTechSolutions. Social media inquiries are monitored during business hours and we aim to respond within 1 hour.

Mailing Address: NovaTech Solutions Inc., 4200 Innovation Drive, Suite 300, Austin, TX 78759, United States.
"""),
])

# ─────────────────────────────────────────────────────────────
# 2. Products Catalog
# ─────────────────────────────────────────────────────────────
build_pdf("NovaTech_Products_Catalog.pdf", "NovaTech Solutions — Product Catalog", [
    ("NovaTech Cloud Suite", """
The NovaTech Cloud Suite is our flagship cloud-based productivity platform used by over 350,000 subscribers. It includes the following applications:

NovaDocs: A collaborative document editor with real-time co-editing, version history (up to 365 days), commenting, and export to PDF, DOCX, and HTML formats. Storage is unlimited for paid plans and 5 GB for free accounts.

NovaSheets: A powerful spreadsheet application with over 400 built-in functions, pivot tables, conditional formatting, and integration with external databases via our API connector. Supports CSV, XLSX, and Google Sheets import.

NovaSlides: A presentation tool with 50+ professional templates, animation support, presenter view, and the ability to embed live content such as videos, charts, and web pages.

NovaMail: A business email service with 50 GB mailbox storage, custom domain support, spam filtering with 99.7% accuracy, and calendar integration. Supports IMAP, POP3, and Exchange ActiveSync.

NovaChat: A team messaging platform with channels, direct messages, file sharing (up to 500 MB per file), screen sharing, and video calls for up to 25 participants. Integrates with all other Cloud Suite apps.
"""),
    ("NovaTech Cloud Suite — Pricing", """
Free Plan: Includes NovaDocs, NovaSheets, and NovaSlides with 5 GB storage. Limited to 3 collaborators per document. No NovaMail or NovaChat access. No credit card required.

Personal Plan ($9.99/month or $99/year): Everything in Free, plus 100 GB storage, unlimited collaborators, NovaMail with custom domain, priority email support, and advanced sharing controls.

Team Plan ($14.99/user/month or $149/user/year): Everything in Personal, plus NovaChat, admin console, team analytics dashboard, SSO integration (SAML 2.0), and 1 TB storage per user. Minimum 5 users.

Enterprise Plan (custom pricing): Everything in Team, plus unlimited storage, 24/7 premium phone support, dedicated account manager, custom integrations, SLA guarantee of 99.99% uptime, data residency options (US, EU, APAC), and advanced compliance features (SOC 2 Type II, HIPAA, GDPR). Contact sales@novatech.com for a quote.

All paid plans include a 14-day free trial with full functionality. No long-term contracts required — you can cancel anytime. Annual billing saves approximately 17% compared to monthly billing.
"""),
    ("NovaHome Smart Home Devices", """
NovaHome Hub (Model NH-100): The central controller for the NovaHome ecosystem. Features a 7-inch touchscreen display, built-in speaker with voice assistant, Wi-Fi 6 and Bluetooth 5.2 connectivity, Zigbee and Z-Wave support for third-party smart devices. Price: $149.99. Available in Midnight Black, Arctic White, and Sage Green.

NovaHome Camera (Model NC-200): Indoor/outdoor security camera with 2K HDR video, 160-degree field of view, night vision up to 30 feet, two-way audio, motion detection with AI person/vehicle/animal recognition, and local storage via microSD card (up to 256 GB) or cloud storage. Weather-resistant (IP66 rating). Price: $89.99.

NovaHome Thermostat (Model NT-300): Smart thermostat with learning capabilities, occupancy sensing, humidity monitoring, and energy usage reports. Compatible with most HVAC systems (2H/2C, heat pump). Works with NovaTech voice assistant, Amazon Alexa, Google Home, and Apple HomeKit. ENERGY STAR certified. Price: $199.99.

NovaHome Doorbell (Model ND-400): Video doorbell with 2K HDR camera, 180-degree field of view, package detection, customizable motion zones, and pre-roll video capture. Wired or battery-powered options. Includes free 30-day cloud storage for video clips. Price: $129.99.

NovaHome Smart Lock (Model NL-500): Keyless entry smart lock with fingerprint reader (stores up to 100 fingerprints), PIN code, NFC, and physical key backup. Auto-lock feature, activity log, and temporary guest access codes. Works with NovaTech, Alexa, and Google Home. ANSI/BHMA Grade 2 certified. Price: $249.99.
"""),
    ("NovaTech Enterprise Solutions", """
NovaTech Enterprise Platform: A comprehensive IT management and collaboration platform designed for businesses with 50 to 50,000 employees. Includes all Cloud Suite apps plus:

Enterprise Admin Console: Centralized user management, role-based access controls, audit logs, and compliance reporting. Supports Active Directory and LDAP synchronization.

NovaDrive for Business: Secure file storage and sharing with 1 TB per user (expandable), data loss prevention (DLP) rules, eDiscovery, and legal hold capabilities.

NovaConnect: Enterprise video conferencing with up to 500 participants, webinar mode for up to 10,000 attendees, recording with automatic transcription, and breakout rooms.

NovaTech API Platform: RESTful API access to all NovaTech services. Rate limits: 1,000 requests per minute for Team plans, 10,000 for Enterprise. Full API documentation at developers.novatech.com.

Deployment options include multi-tenant cloud (hosted in AWS US-East, EU-West, or APAC-Southeast), single-tenant dedicated cloud, or on-premises deployment for regulated industries.
"""),
])

# ─────────────────────────────────────────────────────────────
# 3. Return & Refund Policy
# ─────────────────────────────────────────────────────────────
build_pdf("NovaTech_Return_Refund_Policy.pdf", "NovaTech Solutions — Return & Refund Policy", [
    ("Hardware Return Policy", """
NovaTech offers a 30-day satisfaction guarantee on all hardware products purchased directly from novatech.com or authorized retail partners. If you are not completely satisfied with your purchase, you may return it within 30 calendar days of the delivery date for a full refund.

To be eligible for a return, the product must be in its original packaging with all accessories, manuals, and cables included. The product must be free of physical damage beyond normal unboxing wear. Products with signs of intentional damage, water damage, or unauthorized modifications are not eligible for return.

Refurbished or clearance items purchased from our outlet store are subject to a 15-day return window and may be subject to a 15% restocking fee.

Products purchased from third-party retailers must be returned to the original place of purchase in accordance with that retailer's return policy. NovaTech cannot process returns for products not purchased directly from us.
"""),
    ("How to Initiate a Return", """
Step 1: Log in to your NovaTech account at novatech.com/account and navigate to "Order History." Find the order containing the item you wish to return and click "Request Return."

Step 2: Select the reason for your return from the dropdown menu and provide any additional details. This helps us improve our products and services.

Step 3: You will receive a prepaid return shipping label via email within 1 business day. Print the label and securely pack the item in its original packaging.

Step 4: Drop off the package at any UPS or FedEx location. You can also schedule a free pickup by calling UPS at 1-800-742-5877.

Step 5: Once we receive and inspect the returned item, your refund will be processed within 5 to 7 business days. You will receive a confirmation email when the refund is issued. The refund will be applied to your original payment method.

If you purchased the item as a gift, we can issue a NovaTech store credit instead of refunding the original payment method. Please contact support@novatech.com to request this option.
"""),
    ("Software and Subscription Refunds", """
Monthly Subscriptions: You may cancel your NovaTech Cloud Suite subscription at any time. No refunds are issued for partial months already billed. Your access continues until the end of the current billing period.

Annual Subscriptions: If you cancel within the first 30 days of an annual subscription, you will receive a full refund. After 30 days, you may cancel at any time but no prorated refund will be issued — your access continues until the end of the annual period.

Enterprise Contracts: Enterprise plan refunds are governed by the terms of your individual service agreement. Please contact your account manager or enterprise@novatech.com for assistance.

In-App Purchases: Purchases of add-ons, extra storage, or premium templates are non-refundable once delivered. If you experience a technical issue with an in-app purchase, please contact support for assistance — we may offer credit at our discretion.
"""),
    ("Warranty Information", """
All NovaTech hardware products come with a standard 2-year limited warranty that covers defects in materials and workmanship under normal use conditions. The warranty period begins on the date of original purchase.

What is covered: Manufacturing defects, hardware malfunctions not caused by user misuse, battery defects (battery capacity guaranteed to retain at least 80% of original capacity for 2 years).

What is not covered: Physical damage from drops, spills, or misuse. Damage caused by unauthorized repair or modification. Cosmetic damage such as scratches or dents that do not affect functionality. Damage from power surges or lightning strikes. Normal wear and tear.

Extended Warranty: You may purchase NovaCare+ extended warranty within 60 days of your original purchase. NovaCare+ extends your coverage to 3 years total and adds accidental damage protection (2 incidents covered with a $49 service fee per incident). NovaCare+ pricing: $29.99 for accessories, $79.99 for cameras and doorbells, $99.99 for Hub, thermostat, and smart lock.

To make a warranty claim, contact support@novatech.com with your order number and a description of the issue. We may ask you to perform basic troubleshooting steps. If the issue cannot be resolved, we will arrange for a replacement device to be shipped to you at no cost.
"""),
])

# ─────────────────────────────────────────────────────────────
# 4. Troubleshooting Guide
# ─────────────────────────────────────────────────────────────
build_pdf("NovaTech_Troubleshooting_Guide.pdf", "NovaTech Solutions — Troubleshooting Guide", [
    ("NovaTech Cloud Suite — Common Issues", """
Issue: I cannot log in to my NovaTech account.
Solution: First, verify that you are using the correct email address associated with your account. If you have forgotten your password, click "Forgot Password" on the login page and follow the instructions sent to your email. If you have two-factor authentication enabled, make sure you have access to your authenticator app or backup codes. If you are still unable to log in, contact support@novatech.com and we will help verify your identity and restore access within 24 hours.

Issue: My documents are not syncing across devices.
Solution: Ensure that you are signed in to the same NovaTech account on all devices. Check that your internet connection is active and stable. If sync is delayed, try clicking the sync icon in the top-right corner of NovaDocs to force a manual sync. If the problem persists, clear your browser cache, log out, and log back in. Documents last synced more than 7 days ago will automatically sync when you reconnect.

Issue: I cannot share a document with external users.
Solution: External sharing must be enabled by your team administrator in the Admin Console under Settings, then Sharing, then External Sharing. If you are on the Free plan, external sharing is limited to view-only access. Paid plans support full edit permissions for external collaborators. Make sure the person you are inviting has a valid email address.

Issue: NovaMail is not receiving emails.
Solution: Check your spam and junk folders. Verify that your custom domain DNS records (MX, SPF, DKIM) are correctly configured — you can check this in the NovaMail Admin Console under Domain Settings, then DNS Status. If all records are correct but you are still not receiving emails, check if any email filtering rules are redirecting messages. Contact support if the issue persists for more than 2 hours.
"""),
    ("NovaHome Hub — Common Issues", """
Issue: The NovaHome Hub is not connecting to Wi-Fi.
Solution: Make sure your Wi-Fi router is broadcasting on the 2.4 GHz band — the Hub supports both 2.4 GHz and 5 GHz, but initial setup requires 2.4 GHz. Move the Hub closer to your router during setup (within 15 feet). If the Hub was previously connected and lost connection, press and hold the reset button on the back for 5 seconds until the LED flashes blue, then restart the setup process in the NovaHome app. Make sure your router firmware is up to date.

Issue: Voice commands are not being recognized.
Solution: Ensure the Hub's microphone is not muted (check the physical mute button on the top of the device). Speak clearly and face the Hub from within 15 feet. If the Hub responds with "I didn't understand that," try rephrasing your command. You can view a list of supported voice commands in the NovaHome app under Settings, then Voice Commands. If recognition accuracy is low, go to Settings, then Voice Training, and complete the 2-minute calibration exercise.

Issue: Smart devices are showing as "offline" in the app.
Solution: Check that the smart device is powered on and within range of the Hub (up to 100 feet for Zigbee devices, 30 feet for Bluetooth). Try power-cycling the device by unplugging it for 10 seconds and plugging it back in. If the device still shows offline, remove it from the app and re-add it by going to Devices, then Add Device. If you recently updated the Hub firmware, some devices may need to be re-paired.
"""),
    ("NovaHome Camera — Common Issues", """
Issue: Camera video feed is blurry or low quality.
Solution: Clean the camera lens with a soft, dry cloth. Check your internet connection — the camera requires at least 2 Mbps upload speed for 2K streaming. If you are on a slow connection, the camera automatically reduces video quality. You can adjust quality preferences in the NovaHome app under the camera settings. If the camera is mounted outdoors, check for water droplets or condensation on the lens.

Issue: Motion detection is sending too many false alerts.
Solution: Adjust the motion sensitivity in the NovaHome app — go to the camera settings, then Motion Detection, then Sensitivity. Set it to "Medium" or "Low" to reduce false triggers from trees, animals, or passing cars. You can also set up custom motion zones to monitor only specific areas of the camera's field of view. Enable "Person Detection Only" mode to receive alerts only when a person is detected.

Issue: Night vision is not working.
Solution: Verify that night vision is enabled in the camera settings (it is on by default). Check that the infrared LEDs on the front of the camera are not obstructed. Note that highly reflective surfaces near the camera (glass windows, mirrors) can cause IR glare. If the camera is mounted behind a window, disable night vision and use ambient lighting instead, as IR light reflects off glass.
"""),
    ("NovaHome Thermostat — Common Issues", """
Issue: The thermostat is not heating or cooling my home.
Solution: Verify that your HVAC system is turned on at the breaker. Check that the thermostat is set to the correct mode (Heat, Cool, or Auto). If the display shows "Waiting," the thermostat is applying a compressor protection delay — wait 5 minutes for the system to start. Check that the temperature differential is at least 2 degrees between the set temperature and the current room temperature. If the thermostat display is blank, the C-wire may not be connected — refer to the installation guide or contact support.

Issue: The energy report shows unusual usage spikes.
Solution: Energy spikes can be caused by extreme weather, HVAC maintenance issues (such as a dirty air filter), or changes in occupancy patterns. Check and replace your HVAC air filter if it has not been changed in the last 3 months. If your system is running constantly without reaching the set temperature, your HVAC system may need professional servicing. You can view detailed energy reports in the NovaHome app under Thermostat, then Energy History.
"""),
    ("Account and Billing Issues", """
Issue: I was charged twice for my subscription.
Solution: Duplicate charges occasionally occur due to payment processing delays. Check your bank statement after 3 to 5 business days — one of the charges may be a pending authorization that will automatically drop off. If the duplicate charge persists after 5 business days, contact support@novatech.com with your order number and a screenshot of the duplicate charges. We will investigate and issue a refund within 2 business days.

Issue: I want to upgrade or downgrade my plan.
Solution: Log in to your NovaTech account and go to Account Settings, then Subscription. Click "Change Plan" and select your desired plan. Upgrades take effect immediately and you will be charged the prorated difference for the remainder of your billing period. Downgrades take effect at the start of your next billing period — you retain access to premium features until then.

Issue: My account was suspended.
Solution: Account suspension can occur due to payment failure, a Terms of Service violation, or suspicious activity detected on the account. If your payment method failed, update your payment information at novatech.com/account/billing. If you believe the suspension is an error, contact support@novatech.com with your account email and we will review your account within 24 hours. During suspension, your data is safely preserved for 90 days.
"""),
])

# ─────────────────────────────────────────────────────────────
# 5. Privacy & Data Policy
# ─────────────────────────────────────────────────────────────
build_pdf("NovaTech_Privacy_Data_Policy.pdf", "NovaTech Solutions — Privacy & Data Policy", [
    ("Data Collection", """
NovaTech collects the following categories of personal data:

Account Information: Name, email address, phone number (optional), billing address, and payment method details. This information is collected when you create an account or make a purchase.

Usage Data: We collect information about how you use our products, including feature usage statistics, session duration, and crash reports. This data is anonymized and used to improve product quality. You can opt out of usage analytics in your account settings.

Device Data: For NovaHome products, we collect device identifiers, firmware version, network information (Wi-Fi signal strength, connected devices), and sensor data (temperature readings, motion events). Camera footage is stored only when you have cloud recording enabled and is encrypted at rest and in transit.

Communication Data: When you contact our support team, we retain records of your communications (emails, chat transcripts, phone call summaries) for quality assurance and training purposes. Call recordings are retained for 90 days and then permanently deleted.
"""),
    ("Data Storage and Security", """
All NovaTech customer data is stored in SOC 2 Type II certified data centers operated by Amazon Web Services (AWS). Data is encrypted at rest using AES-256 encryption and in transit using TLS 1.3.

Cloud Suite Data: Documents, spreadsheets, and other files are stored in the AWS region you or your administrator selects during account setup. Available regions are US-East (Virginia), EU-West (Ireland), and APAC-Southeast (Singapore). Data does not leave your selected region unless you explicitly share a document with a user in a different region.

NovaHome Data: Camera footage and device logs are stored in the same region as your account. Local storage options (microSD card for cameras) keep data entirely on your premises.

Password Security: Passwords are hashed using bcrypt with a work factor of 12. We never store passwords in plain text. We support two-factor authentication via TOTP authenticator apps and hardware security keys (FIDO2/WebAuthn).

We perform annual third-party penetration testing and publish a summary report at novatech.com/security. Our bug bounty program offers rewards from $100 to $10,000 for responsibly disclosed vulnerabilities.
"""),
    ("Data Retention and Deletion", """
Account Data: Your account data is retained for as long as your account is active. If you delete your account, all personal data is permanently erased within 30 days, except for data we are legally required to retain (such as financial transaction records, which are retained for 7 years per tax regulations).

Cloud Suite Files: When you delete a file, it moves to the Trash folder where it remains for 30 days before permanent deletion. Team administrators can adjust the trash retention period from 7 to 90 days. After permanent deletion, the data is purged from our backup systems within 14 additional days.

NovaHome Camera Footage: Cloud-stored camera clips are retained based on your subscription plan — 30 days for free accounts, 60 days for NovaCare+, and 90 days for Enterprise accounts. After the retention period, footage is automatically and permanently deleted. You can manually delete clips at any time from the NovaHome app.

Data Export: You may export all your data at any time by going to Account Settings, then Privacy, then Download My Data. We will prepare a zip file containing all your personal data, documents, and account information. This process takes up to 48 hours and you will receive an email with a secure download link.

To request complete account deletion, email privacy@novatech.com or use the "Delete My Account" button in Account Settings. Deletion is irreversible.
"""),
    ("GDPR and CCPA Compliance", """
NovaTech complies with the General Data Protection Regulation (GDPR) for customers in the European Economic Area and the California Consumer Privacy Act (CCPA) for California residents.

Under GDPR, you have the right to access, correct, port, and delete your personal data. You also have the right to object to processing and to withdraw consent at any time. Our Data Protection Officer can be reached at dpo@novatech.com.

Under CCPA, California residents have the right to know what personal information is collected, the right to delete it, the right to opt out of the sale of personal information, and the right to non-discrimination for exercising these rights. NovaTech does not sell personal information to third parties.

For data processing agreements (DPA) required by GDPR for enterprise customers, contact legal@novatech.com.
"""),
])

# ─────────────────────────────────────────────────────────────
# 6. Shipping & Delivery Guide
# ─────────────────────────────────────────────────────────────
build_pdf("NovaTech_Shipping_Delivery.pdf", "NovaTech Solutions — Shipping & Delivery Guide", [
    ("Shipping Options and Costs", """
NovaTech offers the following shipping options for hardware orders placed on novatech.com:

Standard Shipping (5 to 7 business days): Free on all orders over $50. Orders under $50 are charged a flat rate of $5.99. Available to all 50 US states and US territories.

Expedited Shipping (2 to 3 business days): $12.99 flat rate regardless of order size. Available to the contiguous 48 US states only.

Next-Day Shipping (1 business day): $24.99 flat rate. Orders must be placed before 2 PM Central Time for same-day processing. Available to the contiguous 48 US states only. Not available for orders placed on weekends or federal holidays.

International Shipping: Available to Canada, United Kingdom, Germany, France, Australia, Japan, and Singapore. Shipping costs and delivery times vary by destination — calculated at checkout. International orders may be subject to customs duties and import taxes, which are the responsibility of the buyer. Typical delivery times range from 7 to 14 business days.

All orders receive a shipping confirmation email with a tracking number within 24 hours of shipment. You can track your order at novatech.com/track or directly through the carrier's website (UPS or FedEx).
"""),
    ("Order Processing", """
Orders placed Monday through Friday before 2 PM Central Time are typically processed and shipped the same business day. Orders placed after 2 PM or on weekends and holidays are processed on the next business day.

During peak periods such as Black Friday, Cyber Monday, and holiday season (November 20 through December 31), processing times may be extended by 1 to 2 additional business days. We recommend ordering early during these periods.

You will receive an email confirmation immediately after placing your order, followed by a shipping confirmation with tracking information once your order has been dispatched.

Order Modifications: You may modify or cancel your order within 1 hour of placing it by contacting support@novatech.com or calling our support line. Once the order has entered the fulfillment process, it cannot be modified — but you can return the item after delivery under our 30-day return policy.
"""),
    ("Delivery Issues", """
If your package shows as delivered but you have not received it, please check around your delivery area including porches, side doors, mailroom (for apartments), and with neighbors. Carriers sometimes mark packages as delivered slightly before the actual delivery.

If you still cannot locate your package after 24 hours, contact support@novatech.com with your order number and tracking number. We will initiate a carrier investigation, which typically takes 3 to 5 business days. If the package cannot be located, we will ship a replacement at no cost or issue a full refund — your choice.

Damaged packages: If your package arrives damaged, take photos of the packaging and the product, and contact support@novatech.com within 48 hours. We will arrange for a replacement to be shipped immediately at no cost. You do not need to return the damaged item.

Incorrect items: If you received the wrong item, contact support@novatech.com and we will ship the correct item immediately with expedited shipping at no cost. We will provide a prepaid return label for the incorrect item.
"""),
])

# ─────────────────────────────────────────────────────────────
# 7. Account Management Guide
# ─────────────────────────────────────────────────────────────
build_pdf("NovaTech_Account_Management.pdf", "NovaTech Solutions — Account Management Guide", [
    ("Creating and Managing Your Account", """
To create a NovaTech account, visit novatech.com/register and provide your name, email address, and a password. Passwords must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, and one number. After registration, you will receive a verification email — click the link to activate your account.

You can manage your account settings at novatech.com/account. From there you can update your name, email, password, phone number, profile photo, and notification preferences. Changes to your email address require re-verification.

Account Recovery: If you lose access to your account and cannot reset your password via email, contact support@novatech.com with your full name, the email address on the account, and the last 4 digits of the payment method on file. Our team will verify your identity and help restore access within 24 to 48 hours.
"""),
    ("Two-Factor Authentication", """
We strongly recommend enabling two-factor authentication (2FA) for your NovaTech account. 2FA adds an extra layer of security by requiring a verification code in addition to your password.

To enable 2FA, go to Account Settings, then Security, then Two-Factor Authentication, and click Enable. You can choose from the following methods:

Authenticator App (recommended): Use any TOTP-compatible app such as Google Authenticator, Authy, or Microsoft Authenticator. Scan the QR code displayed on screen and enter the 6-digit verification code to complete setup.

Hardware Security Key: We support FIDO2/WebAuthn security keys such as YubiKey. Insert your key and follow the on-screen instructions. You can register up to 5 security keys per account.

Backup Codes: When you enable 2FA, you will receive 10 one-time backup codes. Store these in a safe place — each code can be used once to access your account if you lose access to your primary 2FA method. You can regenerate backup codes at any time from your security settings.

If you lose access to all 2FA methods and backup codes, contact support for identity verification and 2FA reset. This process takes 48 to 72 hours for security purposes.
"""),
    ("Team and Organization Management", """
If you are on a Team or Enterprise plan, your team administrator can manage users from the Admin Console at admin.novatech.com.

Adding Users: Click "Add User" and enter the person's email address. They will receive an invitation email and must create a NovaTech account (or link an existing one) to join your team. You can assign roles such as Member, Manager, or Administrator.

Removing Users: When you remove a user from your team, their access to shared team resources is immediately revoked. Their personal files remain in their individual account. If you need to transfer their files to another team member, use the "Transfer Ownership" option before removing the user.

Role Permissions: Members can access shared files and channels. Managers can create channels, manage members within their department, and view team analytics. Administrators have full control including billing, security settings, user management, and organization-wide settings.

Single Sign-On (SSO): Team and Enterprise plans support SSO via SAML 2.0. Supported identity providers include Okta, Azure Active Directory, Google Workspace, and OneLogin. SSO setup is available in the Admin Console under Security, then Single Sign-On. Our support team can assist with configuration.
"""),
    ("Billing and Payment", """
NovaTech accepts the following payment methods: Visa, Mastercard, American Express, Discover, PayPal, and bank transfer (Enterprise plans only).

Your subscription is billed on the same day each month (or year for annual plans). You can view your billing history and download invoices at novatech.com/account/billing.

Payment Failures: If a payment fails, we will attempt to charge your payment method again after 3 days. If the second attempt fails, your account will be placed in a grace period of 7 days with full access. After the grace period, your account will be restricted to read-only mode — you can view your data but cannot create or edit content. Your data is preserved for 90 days. Update your payment method to restore full access immediately.

Invoices: Invoices are generated automatically for each payment and sent to your account email. Enterprise customers can request custom invoicing with purchase order numbers — contact billing@novatech.com.

Tax: Prices listed on novatech.com are exclusive of applicable sales tax. Tax is calculated based on your billing address and applied at checkout. Enterprise customers may provide a tax exemption certificate — email it to billing@novatech.com.
"""),
])

# ─────────────────────────────────────────────────────────────
# 8. Frequently Asked Questions (FAQ)
# ─────────────────────────────────────────────────────────────
build_pdf("NovaTech_FAQ.pdf", "NovaTech Solutions — Frequently Asked Questions", [
    ("General Questions", """
Q: What is NovaTech Solutions?
A: NovaTech Solutions is a technology company that provides cloud-based productivity software (NovaTech Cloud Suite), smart home devices (NovaHome), and enterprise IT solutions. We serve over 500,000 customers worldwide.

Q: Where is NovaTech based?
A: Our headquarters is in Austin, Texas. We also have offices in London, Berlin, and Singapore.

Q: How do I contact customer support?
A: You can reach us by email at support@novatech.com, by phone at 1-800-NOVA-TECH (available Monday to Friday, 8 AM to 8 PM Central Time, and Saturday 9 AM to 5 PM), or via live chat on our website during business hours. Our average email response time is under 4 hours, and live chat wait time averages under 2 minutes.

Q: Does NovaTech offer student or nonprofit discounts?
A: Yes. Verified students receive 50% off Personal and Team plans. Verified nonprofit organizations receive 30% off all plans. Apply at novatech.com/discounts with your .edu email or nonprofit documentation.
"""),
    ("Subscription and Billing", """
Q: Can I try NovaTech Cloud Suite before paying?
A: Yes. All paid plans include a 14-day free trial with full functionality. No credit card is required for the trial. Our Free plan is available indefinitely with limited features.

Q: How do I cancel my subscription?
A: Go to Account Settings, then Subscription, then click "Cancel Subscription." Your access continues until the end of the current billing period. No partial refunds are issued for monthly plans. Annual plans can be refunded in full if cancelled within 30 days.

Q: Can I switch between monthly and annual billing?
A: Yes. Go to Account Settings, then Subscription, then click "Change Billing Cycle." Switching to annual billing takes effect at your next billing date and saves approximately 17%.

Q: What happens to my data if I downgrade from a paid plan to the free plan?
A: If your stored data exceeds the 5 GB free plan limit, your account will be in read-only mode. You can view and download your files but cannot upload new content until you reduce your storage usage below 5 GB or upgrade back to a paid plan. No data is deleted automatically — your files remain safe.
"""),
    ("NovaHome Questions", """
Q: Do NovaHome devices work without an internet connection?
A: Basic functionality continues to work locally. The NovaHome Hub can control Zigbee and Z-Wave devices, the thermostat continues to follow its schedule, and the smart lock continues to accept fingerprint and PIN inputs. However, voice control, remote access via the app, cloud recording, and firmware updates require an active internet connection.

Q: Is there a monthly fee for NovaHome devices?
A: No. All NovaHome devices work fully without any subscription. Optional cloud recording storage for cameras is available at $3.99 per month per camera or $9.99 per month for unlimited cameras. The NovaCare+ extended warranty is a one-time purchase, not a subscription.

Q: Are NovaHome devices compatible with other smart home platforms?
A: Yes. All NovaHome devices are compatible with Amazon Alexa, Google Home, and Apple HomeKit via Matter protocol. The NovaHome Hub additionally supports Zigbee and Z-Wave, allowing it to control thousands of third-party smart home devices from brands like Philips Hue, Sonos, Aqara, and Yale.

Q: How do I update the firmware on my NovaHome devices?
A: Firmware updates are delivered automatically over-the-air (OTA) when the device is connected to Wi-Fi and plugged in. You can check for updates manually in the NovaHome app under the device settings. We recommend enabling automatic updates to ensure you have the latest security patches and features. Update notifications appear in the NovaHome app.
"""),
    ("Security and Privacy", """
Q: How does NovaTech protect my data?
A: All data is encrypted at rest using AES-256 and in transit using TLS 1.3. We use SOC 2 certified infrastructure, conduct annual penetration testing, and support two-factor authentication. We never sell personal data to third parties.

Q: Can I see what data NovaTech has about me?
A: Yes. Go to Account Settings, then Privacy, then "Download My Data" to export a complete copy of your personal data. The export is prepared within 48 hours and a download link is sent to your email.

Q: Does NovaTech sell my data?
A: No. NovaTech does not sell, share, or rent personal information to third parties for marketing purposes. We share data only with essential service providers (payment processors, cloud infrastructure) under strict data processing agreements.

Q: Can NovaTech employees see my camera footage?
A: No. Camera footage is encrypted and NovaTech employees do not have access to your recordings. The only exception is if you explicitly share footage with our support team during a troubleshooting session — and even then, access is temporary and logged.
"""),
])

print(f"\nAll PDFs generated in: {OUTPUT_DIR}")
print("You can now upload these via the admin documents page or run the seed script.")
