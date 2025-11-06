#!/bin/bash

# Fix cohort/sub-project terminology to use "location" throughout the web app
# This script replaces user-facing text while preserving code identifiers

FILE="/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html"

# Create backup
cp "$FILE" "$FILE.backup_$(date +%Y%m%d_%H%M%S)"

# Replace user-facing text (between > and <)
# Step titles and headings
sed -i 's/>Configure Sub-Projects (Cohorts)</>Configure Locations</g' "$FILE"
sed -i 's/>Defined Cohorts</>Defined Locations</g' "$FILE"
sed -i 's/>Add New Cohort</>Add New Location</g' "$FILE"
sed -i 's/>Add Cohort \/ Location</>Add Location</g' "$FILE"
sed -i 's/>Add Cohort</>Add Location</g' "$FILE"
sed -i 's/>✓ Add Cohort</>✓ Add Location</g' "$FILE"

# Descriptions and help text
sed -i 's/Define cohorts for your multi-location project/Define locations for your multi-location project/g' "$FILE"
sed -i 's/Each cohort represents/Each location represents/g' "$FILE"
sed -i 's/Set up cohorts for different locations/Set up training locations/g' "$FILE"
sed -i 's/Each cohort can have its own schedule/Each location can have its own schedule/g' "$FILE"
sed -i 's/No cohorts defined yet/No locations defined yet/g' "$FILE"
sed -i 's/Click "Add Cohort" to create your first location/Click "Add Location" to create your first location/g' "$FILE"
sed -i 's/You can add more cohorts later/You can add more locations later/g' "$FILE"

# Form labels
sed -i 's/>Cohort Name</>Location Name</g' "$FILE"
sed -i 's/placeholder="e.g., New York Campus, Q1 2025 Cohort"/placeholder="e.g., New York Campus, Downtown Branch"/g' "$FILE"

# Multi-Location Project Setup box
sed -i 's/>Multi-Location Project Setup</>Multi-Location Project Setup</g' "$FILE"

# Info boxes and tips
sed -i 's/Tip: You can add more cohorts/Tip: You can add more locations/g' "$FILE"
sed -i 's/from the project detail view\. Instructors, students, and tracks will be assigned in the next steps\./from the project detail view. Instructors, students, and tracks will be assigned in the next steps./g' "$FILE"

echo "✅ Terminology updated in org-admin-dashboard.html"
echo "Backup created: $FILE.backup_$(date +%Y%m%d_%H%M%S)"
