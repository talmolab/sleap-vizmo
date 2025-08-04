#!/bin/bash

# Test script for metadata extraction

# Function to extract metadata from filename
extract_metadata() {
    local filename="$1"
    local filepath="$2"
    
    # Extract components from filename
    # Pattern: [Prefix]_[Treatment]_[Set]_[Day]_[Timestamp]_[Number].tif
    local basename=$(basename "$filename" .tif)
    
    # Extract day number
    local day=$(echo "$basename" | grep -o 'day[0-9]\+' | sed 's/day//')
    
    # Extract timestamp (find pattern like 20250523-131815)
    local timestamp=$(echo "$basename" | grep -o '[0-9]\{8\}-[0-9]\{6\}')
    
    # Extract number (last part after final underscore)
    local number=$(echo "$basename" | grep -o '_[0-9]\+\.tif$' | sed 's/_\([0-9]\+\)\.tif$/\1/' || echo "$basename" | sed 's/.*_\([0-9]\+\)$/\1/')
    
    # Split by underscores and work backwards from known patterns
    IFS='_' read -ra PARTS <<< "$basename"
    local prefix="${PARTS[0]}"
    
    # Find the index of the part containing "set" or "day"
    local set=""
    local treatment=""
    local set_index=-1
    local day_index=-1
    
    for i in "${!PARTS[@]}"; do
        if [[ "${PARTS[i]}" =~ ^set[0-9] ]]; then
            set_index=$i
            set="${PARTS[i]}"
        elif [[ "${PARTS[i]}" =~ ^day[0-9] ]]; then
            day_index=$i
            break
        fi
    done
    
    # If we found set index, treatment is everything between prefix and set
    if [[ $set_index -gt 1 ]]; then
        treatment=""
        for ((i=1; i<set_index; i++)); do
            if [[ $i -eq 1 ]]; then
                treatment="${PARTS[i]}"
            else
                treatment="${treatment}_${PARTS[i]}"
            fi
        done
        # Remove trailing underscores
        treatment=$(echo "$treatment" | sed 's/_*$//')
    else
        # Fallback: assume second part is treatment
        treatment="${PARTS[1]}"
    fi
    
    # If no set found, try to extract from context
    if [[ -z "$set" ]]; then
        set=$(echo "$basename" | grep -o 'set[0-9]\+' | head -1)
        if [[ -z "$set" ]]; then
            set="unknown"
        fi
    fi
    
    echo "$day,$prefix,$treatment,$set,$timestamp,$number,$filepath,$filename"
}

# Test with the problematic filename
echo "Testing problematic filename:"
result=$(extract_metadata "F_Gr__set1_day10_20250523-131815_007.tif" "test/path")
echo "Result: $result"

# Test with normal filename
echo "Testing normal filename:"
result=$(extract_metadata "F_Ac_set1_day10_20250523-131615_001.tif" "test/path")
echo "Result: $result"

# Test with complex treatment
echo "Testing complex treatment:"
result=$(extract_metadata "OG_DhA_set2_day10_20250523-132250_017.tif" "test/path")
echo "Result: $result"