#!/usr/bin/env python3
import sys
import os
from contract_splicer import ContractSplicer

def main():
    try:
        splicer = ContractSplicer('CU', k=1)
        adj_close = splicer.build()
        print("CU k=1 Spliced series built successfully!")
        print("Shape:", adj_close.shape)
        print("First 5 values:\n", adj_close.head())
        print("Last 5 values:\n", adj_close.tail())
        print("Number of rolls:", len(splicer.roll_dates))
        print("First 5 rolls:", splicer.roll_dates[:5])
        print("Unique active contracts:", splicer.contract_log.dropna().unique())
        
        # Test TF
        splicer_tf = ContractSplicer('TF', k=2)
        adj_close_tf = splicer_tf.build()
        print("\nTF k=2 Spliced series built successfully!")
        print("Shape:", adj_close_tf.shape)
        print("Number of rolls:", len(splicer_tf.roll_dates))
        print("Unique active contracts:", splicer_tf.contract_log.dropna().unique())
    except Exception as e:
        print("Error during test:", e)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
