# Accuracy Detection

unpdf includes built-in accuracy detection to help you measure conversion quality when you have the original markdown available.

## Usage

### Command Line

```bash
# Convert and check accuracy against original markdown
unpdf document.pdf --check-accuracy original.md

# With custom output path
unpdf input.pdf -o output.md --check-accuracy original.md
```

### Example Output

```
INFO: Converting: example.pdf
INFO: ✓ Converted: example.md
INFO:
Checking accuracy against: original.md
INFO:
=== Accuracy Report ===
INFO: Overall Accuracy: 91.3%
INFO: Precision: 100.0%
INFO: Recall: 84.1%
INFO: F1 Score: 91.3%
INFO:
Element Counts: 58 detected, 69 expected
INFO: True Positives: 58, False Positives: 0, False Negatives: 11
INFO:
Per-Element Type Accuracy:
INFO:   header: 100.0% (detected: 25, expected: 25)
INFO:   paragraph: 85.7% (detected: 6, expected: 8)
INFO:   list_item: 100.0% (detected: 12, expected: 12)
INFO:   table: 100.0% (detected: 10, expected: 10)
INFO:   code_block: 100.0% (detected: 3, expected: 3)
INFO:   blockquote: 100.0% (detected: 2, expected: 2)
INFO:   horizontal_rule: 0.0% (detected: 0, expected: 9)
```

## Understanding the Metrics

### Overall Metrics

- **Precision**: Percentage of detected elements that are correct (avoiding false positives)
- **Recall**: Percentage of expected elements that were detected (avoiding false negatives)
- **F1 Score**: Harmonic mean of precision and recall (balanced accuracy measure)
- **Overall Accuracy**: Same as F1 Score, expressed as a percentage

### Element Counts

- **True Positives**: Elements correctly detected
- **False Positives**: Elements detected but not in original
- **False Negatives**: Elements in original but not detected

### Per-Element Type Accuracy

Shows accuracy breakdown for each markdown element type:
- Headers (H1-H6)
- Paragraphs
- List items (bullets, numbered)
- Tables
- Code blocks
- Blockquotes
- Horizontal rules
- Images
- Links

## Use Cases

### Development Testing

```bash
# Test conversion during development
unpdf test.pdf --check-accuracy test-original.md

# Run on multiple test files
for pdf in tests/*.pdf; do
    unpdf "$pdf" --check-accuracy "${pdf%.pdf}.md"
done
```

### Quality Assurance

Use accuracy detection to:
- Validate conversion quality on known documents
- Compare different configuration options
- Track improvements over time
- Identify problematic element types

### Benchmarking

```bash
# Test with different heading ratios
unpdf doc.pdf --heading-ratio 1.2 --check-accuracy original.md
unpdf doc.pdf --heading-ratio 1.3 --check-accuracy original.md
unpdf doc.pdf --heading-ratio 1.5 --check-accuracy original.md
```

## Python API

```python
from unpdf import convert_pdf
from unpdf.accuracy.element_detector import ElementDetector
from unpdf.accuracy.element_scorer import ElementScorer

# Convert PDF
converted_md = convert_pdf("document.pdf")

# Load original markdown
with open("original.md") as f:
    original_md = f.read()

# Detect elements
detector = ElementDetector()
original_elements = detector.detect(original_md)
converted_elements = detector.detect(converted_md)

# Calculate accuracy
scorer = ElementScorer()
accuracy = scorer.calculate_scores(converted_elements, original_elements)

print(f"Overall Accuracy: {accuracy.overall.accuracy_percentage:.1f}%")
print(f"Precision: {accuracy.overall.precision:.1%}")
print(f"Recall: {accuracy.overall.recall:.1%}")

# Per-element breakdown
for elem_type, scores in accuracy.by_type.items():
    counts = accuracy.element_counts[elem_type]
    if counts["expected"] > 0:
        print(f"{elem_type.value}: {scores.accuracy_percentage:.1f}%")
```

## Limitations

- Accuracy detection compares element **counts** and **types**, not exact text matching
- Different markdown formatting can still match (e.g., `**bold**` vs `__bold__`)
- Whitespace differences are normalized
- Order of elements matters for matching
- Best used for regression testing and quality trends, not absolute accuracy measurement

## Tips

1. **Use version control**: Track both PDF and original markdown together
2. **Test representative documents**: Use real-world examples that cover all element types
3. **Set baselines**: Measure current accuracy before making changes
4. **Focus on critical elements**: If headers are most important, optimize for header accuracy
5. **Iterate**: Use accuracy feedback to guide improvements
