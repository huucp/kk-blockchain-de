#!/bin/bash
ps -ef | grep liquity.sh > /dev/null
if [ $? -eq 0 ]; then
  echo "Process is running."
else
  python3 liquity_event_scanner.py
  python3 liquity_event_scanner_borrower_operation.py
  python3 liquity_transaction.py
fi
