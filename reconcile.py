#!/usr/bin/env python3
"""Payment reconciliation (Fixed & Bulletproof).

Reads payments.jsonl, safely parses JSON lines, deduplicates webhook events by txn_id, 
cleans currency string formatting, and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json

transactions = {}

# 1. Read and store unique transactions with safe error handling for malformed lines
with open("payments.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        line_clean = line.strip()
        if not line_clean:
            continue
        
        try:
            event = json.loads(line_clean)
        except json.JSONDecodeError:
            continue
        
        # The unique transaction key is 'txn_id'
        tx_id = event.get("txn_id")
        if tx_id:
            # Keep the latest event version if there are duplicate timestamps
            if tx_id in transactions:
                if event.get("ts", "") >= transactions[tx_id].get("ts", ""):
                    transactions[tx_id] = event
            else:
                transactions[tx_id] = event

# 2. Calculate totals and counts from the deduplicated dictionary
total = 0.0
count = 0

for tx_id, event in transactions.items():
    status = event.get("status", "").lower()
    if status == "success":
        raw_amount = event.get("amount", 0.0)
        
        # Clean amount string if it has commas (e.g., '3,218.81' -> 3218.81)
        if isinstance(raw_amount, str):
            raw_amount = raw_amount.replace(",", "")
            
        total += float(raw_amount)
        count += 1

# 3. Read expected count and verify
with open("expected.txt", "r", encoding="utf-8") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
