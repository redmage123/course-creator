# Test Screenshots Directory

This directory contains test screenshot images used for E2E testing of the screenshot-based course creation feature.

## Purpose

The screenshot course creation tests (`test_screenshot_course_creation_e2e.py`) require sample screenshot images to upload and analyze during testing.

## Requirements

- **Format**: PNG, JPEG, or WEBP
- **Size**: Under 10MB per file
- **Resolution**: Recommended 1920x1080 or higher
- **Content**: Educational content (slides, diagrams, documentation)

## Automatic Generation

If this directory is empty, the test fixture will automatically generate test screenshots using PIL (Pillow):

```python
# Install Pillow if needed
pip install Pillow
```

The fixture will create 3 test screenshots:
- `test_screenshot_1.png` (1920x1080)
- `test_screenshot_2.png` (1920x1080)
- `test_screenshot_3.png` (1920x1080)

## Using Real Screenshots

For more realistic testing, you can place actual educational screenshots here:

1. **PowerPoint Slides**: Export slides as PNG images
2. **Course Diagrams**: Screenshots of educational diagrams
3. **Documentation**: Screenshots of tutorial pages or documentation

### Example Sources

- Course presentation slides
- Whiteboard diagrams
- Tutorial screenshots
- Educational infographics
- Code examples with syntax highlighting

## File Naming

Any naming convention works, but descriptive names help:

```
python_basics_slide_1.png
data_structures_diagram.png
api_documentation_page.png
```

## Cleanup

Test screenshots are preserved for debugging. To clean up:

```bash
rm /home/bbrelin/course-creator/tests/e2e/test_data/screenshots/*.png
```

## Notes

- **Git**: This directory may be .gitignored to prevent large binary files in repo
- **CI/CD**: Automated tests use generated screenshots
- **Manual Testing**: Real screenshots provide better validation of AI analysis
