"""Writes site/offer-videos.json: one conversion video for each offer page of financedepartmentllc.com and one for
the home page, in the words of the pages and the Claim Library (firm claims FD-01 to FD-29, approved by Talha; tax
facts as the pages and the W47 pieces state them). Run it, then render each piece with

  python3 tools/studio/render.py site/offer-videos.json offer-1099 --media <dir> --preview <dir>

Every video runs the same way, in under a minute: the visitor's situation, what is at stake, the offer and its
price, the written guarantee, what you get, the record, and one call to action, the same words as the button under
the video on the page ("Book a 30 minute call"). The end card stays 2 seconds: the page's player keeps showing it.
"""
import json, os

CTA = "Book a 30 minute call"
CTA_SAY = "Book a thirty minute call with Muhammad Talha."   # the end card shows his name above the button

# The record, in the Claim Library's wording: FD-01 with FD-03, or FD-02 (shortened as the website's proof strip does).
TALHA = ("We have worked with 300+ founders, and Muhammad Talha trained at BDO Ebrahim & Co.",
         "We have worked with more than three hundred founders, and Muhammad Talha trained at B D O Ebrahim and Co.",
         {"type": "stat", "prefix": "We have worked with", "value": "300+", "label": "founders",
          "chips": ["Muhammad Talha trained at BDO Ebrahim & Co."], "chips_at": ["muhammad"], "at": "three"})
RAISED = ("Materials we prepared have helped founders raise more than $100M.",
          "Materials we prepared have helped founders raise more than one hundred million dollars.",
          {"type": "stat", "prefix": "Materials we prepared have helped founders raise more than", "value": "$100M", "at": "one"})


def piece(pid, page, title, claims, kicker, hook, hook_say, beats, offer, record=TALHA):
    beats = list(beats) + [record]
    assert len(beats) <= 7, pid
    return {
        "id": pid, "format": "explainer", "title": title, "page": page, "claims": claims,
        "content": {
            "kicker": kicker, "hook": hook, "lines": [b[0] for b in beats], "cta": CTA, "offer": offer, "end_hold": 2.0,
            "say": {"hook": hook_say, "lines": [b[1] for b in beats], "cta": CTA_SAY},
            "scenes": [None] + [b[2] for b in beats] + [None],
        },
        "media": [], "status": "Planned",
    }


def promise(note, title, text, at):
    return {"type": "promise", "stamp": "Guaranteed", "note": note, "title": title, "text": text, "at": at}


P = []

P.append(piece(
    "offer-1099", "/1099-filing", "1099s Done by February 1", ["1099-02", "1099-08", "FD-09", "FD-24", "FD-29", "FD-01", "FD-03", "FD-12"],
    "1099s for 2026 payments", "Paid a contractor $2,000 or more in 2026?",
    "Paid a contractor two thousand dollars or more in twenty twenty-six?",
    [
        ("Form 1099-NEC is due by Monday 1 February 2027.",
         "Form ten ninety-nine N E C is due by Monday, February first, twenty twenty-seven.",
         {"type": "date", "label": "Form 1099-NEC due", "top": "FEB 2027", "day": "1", "bottom": "MONDAY", "at": "february"}),
        ("Late or wrong, each one costs $60 if put right within 30 days, $130 by 1 August, then $340.",
         "Late or wrong, each one costs sixty dollars if put right within thirty days, a hundred and thirty by August first, then three hundred and forty.",
         {"type": "ladder", "title": "A late or wrong 1099, each", "bars": [
             {"value": "$60", "label": "Within 30 days", "tone": "green"}, {"value": "$130", "label": "By 1 August", "tone": "amber"},
             {"value": "$340", "label": "Then", "tone": "red"}], "show": [0, 1, 2], "at": ["sixty", "hundred", "three"]}),
        ("We file them for you: $100 for up to five contractors, then $12.50 a form.",
         "We file them for you. A hundred dollars for up to five contractors, then twelve fifty a form.",
         {"type": "stat", "prefix": "We file them for you", "value": "$100", "label": "for up to five contractors",
          "chips": ["then $12.50 a form"], "chips_at": ["twelve"], "at": "hundred"}),
        ("Guaranteed in writing: send your list by 20 January, and if we miss 1 February, we pay the IRS penalties up to $500.",
         "Guaranteed, in writing. Send your list by January twentieth, and if we miss February first, we pay the I R S penalties, up to five hundred dollars.",
         promise("Send your list by 20 January", "If we miss 1 February", "we pay the IRS penalties up to $500", "five")),
        ("We prepare every form, collect missing W-9s, file with the IRS and send each contractor a copy.",
         "We prepare every form, collect missing W nine forms, file with the I R S, and send each contractor a copy.",
         {"type": "checklist", "title": "What you get", "items": ["Every form prepared", "Missing W-9s collected", "Filed with the IRS", "A copy to each contractor"]}),
    ],
    "1099s Done by February 1, from $100"))

P.append(piece(
    "offer-tax-returns", "/startup-tax-returns", "Startup Tax Return, Filed On Time", ["IRS-7004-2026", "FD-16", "FD-22", "FD-23", "FD-29", "FD-01", "FD-03", "FD-12"],
    "Tax returns for 2026", "No profit yet? Your startup still files.",
    "No profit yet? Your startup still files.",
    [
        ("C corporations file by 15 April 2027, and S corporations and partnerships by 15 March, profit or not.",
         "C corporations file by April fifteenth, twenty twenty-seven, and S corporations and partnerships by March fifteenth, profit or not.",
         {"type": "compare", "left": {"title": "15 March", "icon": "calendar", "note": "S corporations and partnerships"},
          "right": {"title": "15 April", "icon": "calendar", "note": "C corporations"}, "join": "+", "chip": "Profit or not", "chip_at": "profit", "at": "march"}),
        ("$600 for an S corporation or partnership, $750 for a C corporation, with one state included.",
         "Six hundred dollars for an S corporation or partnership, seven fifty for a C corporation, with one state included.",
         {"type": "stat", "prefix": "S corporation or partnership", "value": "$600", "label": "with one state included",
          "chips": ["$750 for a C corporation"], "chips_at": ["seven"], "at": "six"}),
        ("Guaranteed in writing: if your details are in four weeks before the deadline and we miss it, we pay the IRS late filing penalty up to the fee.",
         "Guaranteed, in writing. If your details are in four weeks before the deadline, and we miss it, we pay the I R S late filing penalty, up to the fee.",
         promise("Details in four weeks before the deadline", "If we miss it", "we pay the IRS late filing penalty up to the fee", "penalty")),
        ("Included: a free extension if anything is late, Delaware franchise tax checked both ways, and a review of last year's return.",
         "Included. A free extension if anything is late, Delaware franchise tax checked both ways, and a review of last year's return.",
         {"type": "checklist", "title": "Included", "items": ["A free extension if anything is late", "Delaware franchise tax checked both ways", "A review of last year's return"]}),
        ("Tax season places are limited: reserve yours now and pay when we start your return.",
         "Tax season places are limited. Reserve yours now, and pay when we start your return.",
         {"type": "steps", "items": ["Places are limited", "Reserve yours now", "Pay when we start your return"], "at": ["places", "reserve", "pay"]}),
    ],
    "Startup Tax Return, Filed On Time, from $600"))

P.append(piece(
    "offer-books", "/books-cleanup", "Books Catch Up", ["FD-21", "FD-29", "FD-02", "FD-12"],
    "Books behind", "Books behind? Caught up before an investor looks.",
    "Books behind? Caught up, before an investor looks.",
    [
        ("Diligence starts with your monthly financials: your books need to hold up when an investor's accountant opens them.",
         "Diligence starts with your monthly financials. Your books need to hold up when an investor's accountant opens them.",
         {"type": "icons", "items": [{"icon": "search", "label": "Diligence", "at": "diligence"}, {"icon": "chart", "label": "Your monthly financials", "at": "monthly"},
                                     {"icon": "person", "label": "An investor's accountant", "at": "accountant"}]}),
        ("We bring them current on the accrual basis: $1,000 up to 6 months behind, $1,750 for 7 to 12, and $3,000 for 13 to 24.",
         "We bring them current, on the accrual basis. A thousand dollars up to six months behind, seventeen fifty for seven to twelve, and three thousand for thirteen to twenty-four.",
         {"type": "ladder", "title": "Fixed fee, by months behind", "bars": [
             {"value": "$1,000", "label": "Up to 6 months", "tone": "green"}, {"value": "$1,750", "label": "7 to 12 months", "tone": "green"},
             {"value": "$3,000", "label": "13 to 24 months", "tone": "green"}], "show": [0, 1, 2], "at": ["thousand", "seventeen", "three"]}),
        ("Guaranteed in writing: every account reconciled to its statements, or we fix it free.",
         "Guaranteed, in writing. Every account reconciled to its statements, or we fix it free.",
         promise("Every account", "Reconciled to its statements", "or we fix it free", "free")),
        ("You get every account reconciled, accrual books with revenue recognition, monthly statements and a log of every adjustment.",
         "You get every account reconciled, accrual books with revenue recognition, monthly statements, and a log of every adjustment.",
         {"type": "checklist", "title": "What you get", "items": ["Every account reconciled", "Accrual books with revenue recognition", "Monthly statements", "A log of every adjustment"]}),
        ("Up to 6 months behind, they are ready in 15 working days from complete documents, and you pay half to start, half on delivery.",
         "Up to six months behind, they are ready in fifteen working days from complete documents, and you pay half to start, half on delivery.",
         {"type": "stat", "prefix": "Up to 6 months behind, ready in", "value": "15", "label": "working days from complete documents",
          "chips": ["Half to start", "Half on delivery"], "chips_at": ["half", "delivery"], "at": "fifteen"}),
    ],
    "Books Catch Up, from $1,000", record=RAISED))

P.append(piece(
    "offer-payroll", "/payroll", "Payroll Set Up Right", ["FD-16", "FD-25", "FD-29", "FD-01", "FD-03", "FD-12"],
    "Your first hires", "First hire coming? Payroll set up right from day one.",
    "First hire coming? Payroll, set up right from day one.",
    [
        ("Payroll brings federal and state withholding, unemployment tax registration, quarterly returns and W-2s each January.",
         "Payroll brings federal and state withholding, unemployment tax registration, quarterly returns, and W twos each January.",
         {"type": "icons", "items": [{"icon": "bank", "label": "Withholding", "at": "withholding"}, {"icon": "doc", "label": "Unemployment tax registration", "at": "unemployment"},
                                     {"icon": "calendar", "label": "Quarterly returns", "at": "quarterly"}, {"icon": "mail", "label": "W-2s each January", "at": "january"}]}),
        ("We set it up in your own Gusto account for $200, one state included, then $75 a month for up to five people.",
         "We set it up in your own Gusto account for two hundred dollars, one state included, then seventy-five dollars a month for up to five people.",
         {"type": "stat", "prefix": "Set up in your own Gusto account", "value": "$200", "label": "one state included",
          "chips": ["then $75 a month for up to five people"], "chips_at": ["seventy"], "at": "two"}),
        ("Guaranteed in writing: if an error in our setup causes a payroll tax penalty, we pay it up to the setup fee.",
         "Guaranteed, in writing. If an error in our setup causes a payroll tax penalty, we pay it, up to the setup fee.",
         promise("An error in our setup", "Causes a payroll tax penalty?", "we pay it up to the setup fee", "pay")),
        ("The money never passes through us, and every run is checked before you approve it.",
         "The money never passes through us, and every run is checked before you approve it.",
         {"type": "icons", "items": [{"icon": "lock", "label": "The money never passes through us", "at": "money"},
                                     {"icon": "check", "label": "Every run checked before you approve it", "at": "every"}]}),
        ("You get your payroll tax registrations, your pay schedule and people set up, and your first run checked with you.",
         "You get your payroll tax registrations, your pay schedule and people set up, and your first run checked with you.",
         {"type": "checklist", "title": "What you get", "items": ["Payroll tax registrations", "Pay schedule and people set up", "First run checked with you"]}),
    ],
    "Payroll Set Up Right, $200, then $75 a month"))

P.append(piece(
    "offer-rd-credit", "/rd-tax-credit", "R&D Credit at a Fixed $1,000", ["IRC-41h", "FD-16", "FD-29", "FD-01", "FD-03", "FD-12"],
    "The research credit", "Building a product? Claim the research credit against payroll taxes.",
    "Building a product? Claim the research credit, against payroll taxes.",
    [
        ("With gross receipts under $5 million, and none before the last five years, a company can use it against payroll taxes.",
         "With gross receipts under five million dollars, and none before the last five years, a company can use it against payroll taxes.",
         {"type": "stat", "prefix": "Gross receipts under", "value": "$5M", "label": "and none before the last five years", "at": "five"}),
        ("That is up to $500,000 a year off payroll taxes, instead of waiting for income tax.",
         "That is up to five hundred thousand dollars a year off payroll taxes, instead of waiting for income tax.",
         {"type": "stat", "prefix": "Up to", "value": "$500,000", "label": "a year off payroll taxes", "at": "five"}),
        ("Our fee is a fixed $1,000, never a share of your credit.",
         "Our fee is a fixed thousand dollars, never a share of your credit.",
         {"type": "stat", "prefix": "Our fee is a fixed", "value": "$1,000", "label": "never a share of your credit", "at": "thousand"}),
        ("Guaranteed in writing: if the study finds no credit you can claim, you get the fee back.",
         "Guaranteed, in writing. If the study finds no credit you can claim, you get the fee back.",
         promise("If the study finds", "No credit you can claim?", "you get the fee back", "fee")),
        ("Before you pay, a short call checks whether your work looks like qualifying research.",
         "Before you pay, a short call checks whether your work looks like qualifying research.",
         {"type": "icons", "items": [{"icon": "reply", "label": "A short call before you pay", "at": "short"},
                                     {"icon": "search", "label": "Does your work look like qualifying research?", "at": "qualifying"}]}),
        ("Then we review your work and costs against the IRS test, prepare Form 6765, and set up the payroll offset each quarter.",
         "Then we review your work and costs against the I R S test, prepare form sixty-seven sixty-five, and set up the payroll offset each quarter.",
         {"type": "checklist", "title": "What you get", "items": ["Work and costs reviewed against the IRS test", "Form 6765 prepared", "The payroll offset set up each quarter"]}),
    ],
    "R&D Credit at a Fixed $1,000"))

P.append(piece(
    "offer-funded", "/funded-startups", "The Funded Startup Finance Department", ["FD-17", "FD-18", "FD-19", "FD-29", "FD-02", "FD-12"],
    "The Funded plan", "Closed a round? Your finance department, for $625 a month.",
    "Closed a round? Your finance department, for six hundred and twenty-five dollars a month.",
    [
        ("Your books closed within 10 working days of month end, with burn and runway every close.",
         "Your books closed within ten working days of month end, with burn and runway every close.",
         {"type": "stat", "prefix": "Books closed within", "value": "10", "label": "working days of month end",
          "chips": ["Burn and runway every close"], "chips_at": ["burn"], "at": "ten"}),
        ("Payroll for up to five people in your own Gusto, and your federal and state return each year.",
         "Payroll for up to five people in your own Gusto, and your federal and state return each year.",
         {"type": "icons", "items": [{"icon": "people", "label": "Payroll for up to five people", "at": "payroll"},
                                     {"icon": "doc", "label": "Your federal and state return", "at": "federal"}]}),
        ("Guaranteed in writing: a close later than 10 working days, or runway under nine months without a warning first, makes that month free.",
         "Guaranteed, in writing. A close later than ten working days, or runway under nine months without a warning first, makes that month free.",
         promise("A close later than 10 working days", "That month free", "and the same if runway falls under nine months without a warning first", "free")),
        ("When you start, up to three months of past books are caught up free, and your 1099s and Delaware filing are included.",
         "When you start, up to three months of past books are caught up free, and your ten ninety-nines and Delaware filing are included.",
         {"type": "checklist", "title": "Included", "items": ["Up to three months of past books caught up free", "Your 1099s", "Your Delaware filing"]}),
        ("Leave anytime on 30 days' notice, with a full handover.",
         "Leave anytime, on thirty days' notice, with a full handover.",
         {"type": "stat", "prefix": "Leave anytime on", "value": "30", "label": "days' notice, with a full handover", "at": "thirty"}),
    ],
    "The Funded Startup Finance Department, $625 a month", record=RAISED))

P.append(piece(
    "offer-international", "/international-founder-plan", "The International Founder Plan", ["5472-04", "FD-17", "FD-20", "FD-29", "FD-01", "FD-03", "FD-12"],
    "The International Founder Plan", "Running a US company from abroad?",
    "Running a U S company from abroad?",
    [
        ("For an LLC with one owner outside the US, each Form 5472 not filed when due costs $25,000.",
         "For an L L C with one owner outside the U S, each form fifty-four seventy-two not filed when due costs twenty-five thousand dollars.",
         {"type": "alert", "title": "Form 5472 not filed when due", "value": "$25,000", "suffix": "each", "at": "twenty"}),
        ("For $175 a month, plus state fees at cost, we keep your US company compliant: monthly books, your registered agent and annual report, and Form 5472.",
         "For a hundred and seventy-five dollars a month, plus state fees at cost, we keep your U S company compliant. Monthly books, your registered agent and annual report, and form fifty-four seventy-two.",
         {"type": "stat", "prefix": "We keep your US company compliant", "value": "$175", "label": "a month, plus state fees at cost",
          "chips": ["Monthly books", "Registered agent and annual report", "Form 5472"], "chips_at": ["monthly", "registered", "form"], "at": "hundred"}),
        ("Guaranteed in writing: if your Form 5472 details are in by 31 March and we miss 15 April, a month's fee back and a penalty relief request.",
         "Guaranteed, in writing. If your form fifty-four seventy-two details are in by March thirty-first, and we miss April fifteenth, a month's fee back, and a penalty relief request.",
         promise("Your details in by 31 March", "If we miss 15 April", "a month's fee back and a penalty relief request", "penalty")),
        ("When you start, you get a calendar of every US filing deadline your company has.",
         "When you start, you get a calendar of every U S filing deadline your company has.",
         {"type": "checklist", "title": "Every US filing deadline", "rows": 4}),
        ("Your books reconciled and closed within 10 working days of each month end.",
         "Your books reconciled, and closed within ten working days of each month end.",
         {"type": "stat", "prefix": "Books closed within", "value": "10", "label": "working days of each month end", "at": "ten"}),
    ],
    "The International Founder Plan, $175 a month"))

P.append(piece(
    "offer-us-company", "/us-entry", "US Company in 10 Working Days", ["FD-26", "FD-29", "FD-01", "FD-03", "FD-12"],
    "US company setup", "Setting up a US company from abroad?",
    "Setting up a U S company from abroad?",
    [
        ("Without a US Social Security or taxpayer number, the IRS online EIN application is closed to you.",
         "Without a U S Social Security or taxpayer number, the I R S online E I N application is closed to you.",
         {"type": "icons", "items": [{"icon": "globe", "label": "No US Social Security or taxpayer number", "at": "social"},
                                     {"icon": "lock", "label": "Online EIN application closed", "at": "closed"}]}),
        ("Your company formed, your EIN, help with your US bank application and your first year of state compliance, for one price.",
         "Your company formed, your E I N, help with your U S bank application, and your first year of state compliance, for one price.",
         {"type": "checklist", "title": "For one price", "items": ["Your company formed", "Your EIN", "Help with your US bank application", "Your first year of state compliance"]}),
        ("$425 for a Wyoming LLC, or $484 for a Delaware corporation, state fees included.",
         "Four hundred and twenty-five dollars for a Wyoming L L C, or four hundred and eighty-four for a Delaware corporation, state fees included.",
         {"type": "stat", "prefix": "Wyoming LLC", "value": "$425", "label": "state fees included",
          "chips": ["$484 for a Delaware corporation"], "chips_at": ["eighty"], "at": "four"}),
        ("Guaranteed in writing: filed within 10 working days of complete details, or our fee back.",
         "Guaranteed, in writing. Filed within ten working days of complete details, or our fee back.",
         promise("Your company", "Filed within 10 working days", "of complete details, or our fee back", "fee")),
        ("Start the International Founder Plan with your company, and its first month is free.",
         "Start the International Founder Plan with your company, and its first month is free.",
         {"type": "stat", "prefix": "The International Founder Plan", "value": "Free", "label": "its first month, with your company", "at": "free"}),
    ],
    "US Company in 10 Working Days, from $425"))

P.append(piece(
    "offer-delaware", "/delaware-franchise-tax", "Delaware Franchise Tax, Worked Out Both Ways", ["DE-01", "DE-03", "DE-04", "DE-07", "FD-08", "FD-27", "FD-29", "FD-01", "FD-03", "FD-12"],
    "Delaware franchise tax", "Your Delaware franchise tax may be far higher than it needs to be.",
    "Your Delaware franchise tax may be far higher than it needs to be.",
    [
        ("Delaware gives two ways to work out the tax, and says to use whichever gives the lower figure.",
         "Delaware gives two ways to work out the tax, and says to use whichever gives the lower figure.",
         {"type": "icons", "items": [{"icon": "scale", "label": "Two ways to work out the tax", "at": "two"},
                                     {"icon": "check", "label": "Use the lower figure", "at": "lower"}]}),
        ("With 10,000,000 authorized shares, the authorized shares method gives $85,165.",
         "With ten million authorized shares, the authorized shares method gives eighty-five thousand, one hundred and sixty-five dollars.",
         {"type": "ladder", "id": "dft", "title": "Two ways to work out the tax", "bars": [
             {"value": "$85,165", "label": "Authorized shares", "tone": "red"}, {"value": "$800", "label": "Assumed par value", "tone": "green"}],
          "at": ["eighty"]}),
        ("With 8,000,000 shares issued and $1,000,000 in gross assets, assumed par value gives $800.",
         "With eight million shares issued, and one million dollars in gross assets, assumed par value gives eight hundred dollars.",
         {"type": "ladder", "id": "dft", "show": [1], "at": ["hundred"], "mark": [1], "mark_at": ["assumed"]}),
        ("We work it out both ways and file the lower figure, for $125 a year plus Delaware's own tax and fee.",
         "We work it out both ways, and file the lower figure, for a hundred and twenty-five dollars a year, plus Delaware's own tax and fee.",
         {"type": "stat", "prefix": "Worked out both ways", "value": "$125", "label": "a year",
          "chips": ["The lower figure filed", "Plus Delaware's own tax and fee"], "chips_at": ["file", "plus"], "at": "hundred"}),
        ("Guaranteed in writing: send your details by 15 February, and if we miss 1 March, we pay the penalty and interest up to $500.",
         "Guaranteed, in writing. Send your details by February fifteenth, and if we miss March first, we pay the penalty and interest, up to five hundred dollars.",
         promise("Send your details by 15 February", "If we miss 1 March", "we pay the penalty and interest up to $500", "five")),
    ],
    "Delaware Franchise Tax, Worked Out Both Ways, $125 a year"))

P.append(piece(
    "offer-5472", "/form-5472", "Form 5472 for Foreign Owned LLCs", ["5472-01", "5472-04", "FD-16", "FD-28", "FD-29", "FD-01", "FD-03", "FD-12"],
    "Form 5472", "Own a US LLC from abroad?",
    "Own a U S L L C from abroad?",
    [
        ("If you are its only owner, money in or out means Form 5472 that year, even with no US tax owed.",
         "If you are its only owner, money in or out means form fifty-four seventy-two that year, even with no U S tax owed.",
         {"type": "icons", "items": [{"icon": "person", "label": "Its only owner", "at": "only"}, {"icon": "dollar", "label": "Money in or out", "at": "money"},
                                     {"icon": "doc", "label": "Form 5472 that year", "at": "form"}, {"icon": "check", "label": "Even with no US tax owed", "at": "even"}]}),
        ("Each Form 5472 not filed when due carries a $25,000 penalty.",
         "Each form fifty-four seventy-two not filed when due carries a twenty-five thousand dollar penalty.",
         {"type": "alert", "title": "Form 5472 not filed when due", "value": "$25,000", "suffix": "penalty", "at": "twenty"}),
        ("We file it for you for $300 a year, with a free extension when needed.",
         "We file it for you for three hundred dollars a year, with a free extension when needed.",
         {"type": "stat", "prefix": "Filed for you", "value": "$300", "label": "a year", "chips": ["A free extension when needed"], "chips_at": ["free"], "at": "three"}),
        ("Guaranteed in writing: if your details are in by 31 March and we miss 15 April, the fee back and a penalty relief request.",
         "Guaranteed, in writing. If your details are in by March thirty-first, and we miss April fifteenth, the fee back, and a penalty relief request.",
         promise("Your details in by 31 March", "If we miss 15 April", "the fee back and a penalty relief request", "penalty")),
        ("We work out the year's transactions from your bank statements, prepare the forms, and fax or mail them to the IRS.",
         "We work out the year's transactions from your bank statements, prepare the forms, and fax or mail them to the I R S.",
         {"type": "checklist", "title": "What you get", "items": ["The year's transactions worked out", "The forms prepared", "Faxed or mailed to the IRS"]}),
    ],
    "Form 5472 for Foreign Owned LLCs, $300 a year"))

P.append(piece(
    "offer-scan", "/investor-ready-scan", "5 Day Investor Ready Scan", ["FD-13", "FD-14", "FD-05", "FD-29", "FD-02", "FD-12"],
    "5 Day Investor Ready Scan", "Raising soon? Find what investors will find, in five working days.",
    "Raising soon? Find what investors will find, in five working days.",
    [
        ("The Scan reviews your books, revenue recognition, cap table, key contracts and runway against what a seed or Series A investor will check.",
         "The Scan reviews your books, revenue recognition, cap table, key contracts, and runway, against what a seed or Series A investor will check.",
         {"type": "checklist", "title": "What the Scan reviews", "items": ["Books", "Revenue recognition", "Cap table", "Key contracts", "Runway"]}),
        ("Your findings report names every gap and what it costs to fix, with a Money at Stake page.",
         "Your findings report names every gap, and what it costs to fix, with a Money at Stake page.",
         {"type": "gauge", "label": "Your findings report", "gap_label": "Gap", "gaps": 3, "at": ["every", "costs", "money"]}),
        ("$750 for our first five clients, then $1,250.",
         "Seven hundred and fifty dollars for our first five clients, then twelve fifty.",
         {"type": "stat", "prefix": "For our first five clients", "value": "$750", "label": "then $1,250", "at": "seven"}),
        ("Guaranteed in writing: your findings within five working days of complete documents, or the fee back.",
         "Guaranteed, in writing. Your findings within five working days of complete documents, or the fee back.",
         promise("Your findings", "Within five working days", "of complete documents, or the fee back", "fee")),
        ("Go ahead within 90 days, and the full fee is credited against a books cleanup or the Investor Ready Sprint.",
         "Go ahead within ninety days, and the full fee is credited against a books cleanup, or the Investor Ready Sprint.",
         {"type": "stat", "prefix": "Go ahead within", "value": "90", "label": "days, and the full fee is credited",
          "chips": ["A books cleanup", "The Investor Ready Sprint"], "chips_at": ["books", "investor"], "at": "ninety"}),
        ("We do not introduce investors or take a success fee: you stay in charge of your raise.",
         "We do not introduce investors, or take a success fee. You stay in charge of your raise.",
         {"type": "icons", "items": [{"icon": "shield", "label": "No success fee", "at": "success"},
                                     {"icon": "person", "label": "You stay in charge of your raise", "at": "charge"}]}),
    ],
    "5 Day Investor Ready Scan, $750 for our first five clients", record=RAISED))

P.append(piece(
    "offer-sprint", "/investor-ready-sprint", "Investor Ready Sprint", ["FD-15", "FD-05", "FD-29", "FD-02", "FD-12"],
    "Investor Ready Sprint", "Raising soon? Investor ready in 40 working days.",
    "Raising soon? Investor ready in forty working days.",
    [
        ("First the Scan, then a three statement financial model, then an investor pack and a data room, delivered in order.",
         "First the Scan, then a three statement financial model, then an investor pack and a data room, delivered in order.",
         {"type": "steps", "items": ["The Scan", "A three statement financial model", "An investor pack and a data room"], "at": ["scan", "three", "investor"]}),
        ("The Scan in 5 working days, the model in 15, and the investor pack and data room in 20.",
         "The Scan in five working days, the model in fifteen, and the investor pack and data room in twenty.",
         {"type": "ladder", "title": "Working days", "bars": [
             {"value": "5", "label": "The Scan", "tone": "green"}, {"value": "15", "label": "The model", "tone": "green"},
             {"value": "20", "label": "Pack and data room", "tone": "green"}], "show": [0, 1, 2], "at": ["five", "fifteen", "twenty"]}),
        ("The investor pack is a pitch deck, an investment memo and a one page summary.",
         "The investor pack is a pitch deck, an investment memo, and a one page summary.",
         {"type": "icons", "items": [{"icon": "chart", "label": "Pitch deck", "at": "pitch"}, {"icon": "doc", "label": "Investment memo", "at": "memo"},
                                     {"icon": "list", "label": "One page summary", "at": "summary"}]}),
        ("$4,250 for one company: half to start, and half when we deliver.",
         "Four thousand two hundred and fifty dollars for one company. Half to start, and half when we deliver.",
         {"type": "stat", "value": "$4,250", "label": "for one company", "chips": ["Half to start", "Half when we deliver"], "chips_at": ["start", "deliver"], "at": "four"}),
        ("Guaranteed in writing: six of our scorecard checks at full marks by delivery, or we keep working at no extra cost.",
         "Guaranteed, in writing. Six of our scorecard checks at full marks by delivery, or we keep working, at no extra cost.",
         promise("Six of our scorecard checks", "At full marks by delivery", "or we keep working at no extra cost", "keep")),
        ("We do not introduce investors or take a success fee: you stay in charge of your raise.",
         "We do not introduce investors, or take a success fee. You stay in charge of your raise.",
         {"type": "icons", "items": [{"icon": "shield", "label": "No success fee", "at": "success"},
                                     {"icon": "person", "label": "You stay in charge of your raise", "at": "charge"}]}),
    ],
    "Investor Ready Sprint, $4,250", record=RAISED))

P.append(piece(
    "home-finance-department", "/", "Finance Department", ["FD-30", "FD-09", "FD-16", "FD-17", "FD-26", "FD-13", "FD-01", "FD-03", "FD-12"],
    "For US founders", "Every startup or company needs a Finance Department. Here's yours.",
    "Every startup or company needs a Finance Department. Here's yours.",
    [
        # Talha, 15 November 2026: the home video opens on his line (FD-30), as the home page now does, and the
        # old headline follows as the line under it; FD-29's guarantee line is struck.
        ("Your books, taxes and US filings, handled.",
         "Your books, taxes, and U S filings, handled.",
         {"type": "headline"}),
        ("For US startups, and for founders running a US company from abroad.",
         "For U S startups, and for founders running a U S company from abroad.",
         {"type": "icons", "items": [{"icon": "rocket", "label": "US startups", "at": "startups"},
                                     {"icon": "globe", "label": "Founders running a US company from abroad", "at": "founders"}]}),
        ("Books and tax: 1099s from $100, tax returns from $600, and your finance department for $625 a month.",
         "Books and tax. Ten ninety-nines from a hundred dollars, tax returns from six hundred, and your finance department for six hundred and twenty-five dollars a month.",
         {"type": "checklist", "title": "Books and tax", "items": ["1099s from $100", "Tax returns from $600", "Your finance department for $625 a month"]}),
        ("Your US company set up from $425, and kept compliant for $175 a month.",
         "Your U S company set up from four hundred and twenty-five dollars, and kept compliant for a hundred and seventy-five a month.",
         {"type": "stat", "prefix": "Your US company set up from", "value": "$425", "label": "and kept compliant for $175 a month", "at": "four"}),
        ("Raising? The 5 Day Investor Ready Scan finds your gaps before an investor does.",
         "Raising? The five day Investor Ready Scan finds your gaps, before an investor does.",
         {"type": "gauge", "label": "The 5 Day Investor Ready Scan", "gap_label": "Gap", "gaps": 3, "at": ["finds", "gaps", "investor"]}),
        ("Pick a service or book a call, send your documents, and we do the work, on time.",
         "Pick a service or book a call, send your documents, and we do the work, on time.",
         {"type": "steps", "items": ["Pick a service or book a call", "Send your documents", "We do the work, on time"], "at": ["pick", "send", "work"]}),
    ],
    "Every startup or company needs a Finance Department. Here's yours."))

out = {"week": "site", "media": "site/media", "note": "Conversion videos for the website's offer pages and home page. Made by make_offer_videos.py.", "pieces": P}
here = os.path.dirname(os.path.abspath(__file__))
json.dump(out, open(os.path.join(here, "offer-videos.json"), "w"), indent=1, ensure_ascii=False)
for p in P:
    c = p["content"]
    words = len(c["say"]["hook"].split()) + sum(len(x.split()) for x in c["say"]["lines"]) + len(c["say"]["cta"].split())
    est = words / 2.65 + 0.55 * (len(c["lines"]) + 1) + 0.35 + 2.0
    print("%-26s %2d lines %3d spoken words  about %4.1f s" % (p["id"], len(c["lines"]), words, est))
