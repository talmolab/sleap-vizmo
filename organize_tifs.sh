#!/bin/bash

# organize_tifs.sh
# Script to organize TIF files from Google Drive downloads into day-based directories
# and generate metadata reports
# Usage: ./organize_tifs.sh [target_directory] [--metadata-only]

set -e  # Exit on any error

# Default target directory
TARGET_DIR="${1:-$(pwd)/tifs/MK22}"
METADATA_ONLY=false

# Extract project name from target directory
PROJECT_NAME=$(basename "$TARGET_DIR")
SCANS_DIR="${PROJECT_NAME}_Scans"

# Check for metadata-only flag
if [[ "$2" == "--metadata-only" ]] || [[ "$1" == "--metadata-only" ]]; then
    METADATA_ONLY=true
    if [[ "$1" == "--metadata-only" ]]; then
        TARGET_DIR="$(pwd)/tifs/MK22"
    fi
fi

echo "Organizing TIF files in: $TARGET_DIR"

# Change to target directory
cd "$TARGET_DIR"


# Function to move files with fallback to copy for permission issues
move_or_copy() {
    local src="$1"
    local dest="$2"
    
    if mv "$src" "$dest" 2>/dev/null; then
        return 0
    else
        echo "Warning: Could not move $src, copying instead..."
        cp "$src" "$dest"
        return 0
    fi
}


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

# Function to generate metadata report
generate_metadata_report() {
    local report_file="./tif_metadata_report.csv"
    
    echo "Generating metadata report..."
    echo "Day,Prefix,Treatment,Set,Timestamp,Number,FilePath,Filename" > "$report_file"
    
    cd "$SCANS_DIR"
    for dir in Day*_scans_${PROJECT_NAME}; do
        if [ -d "$dir" ]; then
            local day_num=$(echo "$dir" | grep -o '[0-9]\+')
            for file in "$dir"/*.tif; do
                if [ -f "$file" ]; then
                    local metadata=$(extract_metadata "$file" "$TARGET_DIR/$SCANS_DIR/$file")
                    echo "$metadata" >> "../$report_file"
                fi
            done
        fi
    done
    
    echo "Metadata report saved to: $(pwd)/../$report_file"
    cd ..
}

# Function to discover all days from TIF filenames
discover_days() {
    echo "Discovering scan days from TIF filenames..."
    
    # Find all TIF files and extract day numbers
    local discovered_days=()
    
    # Search for TIF files in current directory and subdirectories
    while IFS= read -r -d '' file; do
        local basename=$(basename "$file" .tif)
        local day=$(echo "$basename" | grep -o 'day[0-9]\+' | sed 's/day//')
        if [[ -n "$day" ]]; then
            discovered_days+=("$day")
        fi
    done < <(find . -name "*.tif" -print0)
    
    # Remove duplicates and sort
    local unique_days=($(printf '%s\n' "${discovered_days[@]}" | sort -n | uniq))
    
    echo "Discovered days: ${unique_days[*]}"
    echo "${unique_days[@]}"
}

# Function to check for missing files
check_missing_files() {
    echo ""
    echo "=== Missing Files Analysis ==="
    
    cd "$SCANS_DIR"
    
    # Get all day directories that exist
    local existing_days=()
    for dir in Day*_scans_${PROJECT_NAME}; do
        if [ -d "$dir" ]; then
            local day_num=$(echo "$dir" | grep -o '[0-9]\+')
            existing_days+=("$day_num")
        fi
    done
    
    # Sort the days
    IFS=$'\n' existing_days=($(sort -n <<<"${existing_days[*]}"))
    unset IFS
    
    # Check each day for potential missing files
    for day in "${existing_days[@]}"; do
        local day_dir="Day${day}_scans_${PROJECT_NAME}"
        if [ -d "$day_dir" ]; then
            local file_count=$(ls "$day_dir" 2>/dev/null | wc -l)
            echo "Day $day: $file_count files"
            
            # List unique combinations found
            echo "  Unique prefix_treatment_set combinations:"
            for file in "$day_dir"/*.tif; do
                if [ -f "$file" ]; then
                    local basename=$(basename "$file" .tif)
                    local combo=$(echo "$basename" | cut -d'_' -f1-3)
                    echo "    $combo"
                fi
            done | sort | uniq | head -10
            
            # Dynamic threshold warning based on average
            if [ "$file_count" -lt 10 ]; then
                echo "  WARNING: Day $day has only $file_count files (might be missing some)"
            fi
        fi
        echo ""
    done
    
    cd ..
}

# Skip file organization if metadata-only flag is set
if [ "$METADATA_ONLY" = false ]; then
    # Create main scans directory if it doesn't exist
    mkdir -p "$SCANS_DIR"

    # Extract any zip files found in the directory
    echo "Extracting zip files..."
    if command -v unzip >/dev/null 2>&1; then
        for zipfile in *.zip; do
            if [ -f "$zipfile" ]; then
                echo "Extracting $zipfile..."
                unzip -o "$zipfile" -d .
            fi
        done
    else
        echo "Warning: unzip command not found. Skipping zip extraction."
        echo "Please extract zip files manually or install unzip."
    fi

    # Discover all days from TIF filenames
    days_array=($(discover_days))
    
    if [ ${#days_array[@]} -eq 0 ]; then
        echo "No TIF files with day patterns found!"
        exit 1
    fi

    # Create day-based directories dynamically
    echo "Creating day-based directories for days: ${days_array[*]}"
    cd "$SCANS_DIR"
    for day in "${days_array[@]}"; do
        mkdir -p "Day${day}_scans_${PROJECT_NAME}"
    done

    # Go back to parent directory for file operations
    cd ..

    # Organize files by day
    echo "Organizing TIF files by scan day..."

    # Process all discovered days
    for day in "${days_array[@]}"; do
        echo "Processing Day $day files..."
        find . -name "*day${day}*.tif" -not -path "./$SCANS_DIR/*" -print0 | while IFS= read -r -d '' file; do
            move_or_copy "$file" "$SCANS_DIR/Day${day}_scans_${PROJECT_NAME}/"
        done
    done
else
    # Even in metadata-only mode, we need to know what days exist
    if [ -d "$SCANS_DIR" ]; then
        echo "$SCANS_DIR directory exists, proceeding with metadata analysis..."
    else
        echo "$SCANS_DIR directory not found. Please run without --metadata-only first."
        exit 1
    fi
fi

# Generate reports
echo ""
echo "=== Organization Complete ==="
echo "File counts by day:"
cd "$SCANS_DIR"
for dir in Day*_scans_${PROJECT_NAME}; do
    if [ -d "$dir" ]; then
        count=$(ls "$dir" 2>/dev/null | wc -l)
        echo "$dir: $count files"
    fi
done
cd ..

# Generate metadata report
generate_metadata_report

# Check for missing files
check_missing_files

echo ""
echo "TIF files have been organized into day-based directories."
echo "You can now access files at: $TARGET_DIR/$SCANS_DIR/Day[X]_scans_${PROJECT_NAME}/"