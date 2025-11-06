# PDF to Markdown Conversion Accuracy Metrics

## Overview

Measuring conversion accuracy for PDF to Markdown is challenging because it involves both structural and semantic correctness. This document outlines common approaches and metrics used in document conversion systems.

## Common Accuracy Measurement Methods

### 1. String-Based Similarity Metrics

#### Levenshtein Distance (Edit Distance)
- Measures minimum number of single-character edits needed to transform one string into another
- **Pros**: Simple, well-understood, language-agnostic
- **Cons**: Doesn't account for structural differences, sensitive to whitespace
- **Use case**: Quick approximation of text accuracy

#### Normalized Edit Distance
```python
similarity = 1 - (levenshtein_distance / max(len(source), len(target)))
```
- Returns value between 0 (no match) and 1 (perfect match)

#### Jaro-Winkler Distance
- Better for shorter strings and typos
- Gives more weight to prefix matches
- **Use case**: Comparing individual elements like headings or list items

### 2. Token-Based Metrics

#### BLEU Score (Bilingual Evaluation Understudy)
- Originally from machine translation
- Measures n-gram overlap between reference and generated text
- **Pros**: Good for overall content preservation
- **Cons**: Doesn't handle structural differences well
- **Range**: 0-1, higher is better

#### ROUGE Score (Recall-Oriented Understudy for Gisting Evaluation)
- Focuses on recall (how much of reference appears in output)
- Variants: ROUGE-N (n-grams), ROUGE-L (longest common subsequence)
- **Use case**: Ensuring important content isn't lost

### 3. Structural Similarity Metrics

#### Abstract Syntax Tree (AST) Comparison
- Parse both Markdown documents into AST
- Compare tree structures element by element
- **Pros**: Accounts for semantic structure
- **Cons**: Requires robust Markdown parser

#### Element-Level Accuracy
Measure accuracy by document element type:
```
Heading Accuracy = correct_headings / total_headings
List Accuracy = correct_list_items / total_list_items
Table Accuracy = correct_table_cells / total_table_cells
```

#### Structure Preservation Ratio
```python
structural_accuracy = {
    'heading_levels': match_ratio,
    'list_nesting': match_ratio,
    'table_dimensions': match_ratio,
    'emphasis_markup': match_ratio
}
```

### 4. Semantic Similarity Metrics

#### Embedding-Based Similarity
- Use models like Sentence-BERT or OpenAI embeddings
- Calculate cosine similarity between document embeddings
- **Pros**: Captures semantic meaning
- **Cons**: Expensive, doesn't verify exact structure

#### Named Entity Recognition (NER) Overlap
- Extract entities from both documents
- Compare entity preservation
- **Use case**: Ensuring critical information (names, dates, numbers) is preserved

### 5. Visual/Layout Metrics

#### Bounding Box Overlap
- Compare spatial positions of elements
- **Use case**: For PDFs where layout matters (forms, tables)

#### Reading Order Accuracy
- Verify elements appear in correct sequence
- Critical for multi-column layouts

### 6. Human Evaluation Metrics

#### Mean Opinion Score (MOS)
- Humans rate conversions on scale (e.g., 1-5)
- Categories: Overall quality, readability, structure preservation

#### Task-Based Evaluation
- Can users accomplish specific tasks with converted document?
- Example: Find specific information, follow instructions

### 7. Domain-Specific Metrics

#### Mathematical Formula Accuracy
- For academic papers
- Verify LaTeX/MathML conversion correctness

#### Citation Preservation
- For research papers
- Ensure references and citations are intact

#### Code Block Fidelity
- For technical documentation
- Verify syntax highlighting markers and indentation

## Recommended Approach for unpdf

### Multi-Level Testing Strategy

#### Level 1: Unit Tests (Element-Level)
```python
def test_header_conversion():
    assert convert_header(pdf_header) == expected_markdown_header
    
def test_list_structure():
    assert convert_list(pdf_list) == expected_markdown_list
```

#### Level 2: Component Accuracy
- Test each converter (TextConverter, TableConverter, etc.)
- Measure accuracy for specific element types
- Track metrics over time

#### Level 3: End-to-End Similarity
```python
def measure_conversion_accuracy(original_md: str, converted_md: str) -> Dict:
    return {
        'text_similarity': calculate_text_similarity(original_md, converted_md),
        'structure_similarity': compare_ast_structure(original_md, converted_md),
        'element_accuracy': compare_elements(original_md, converted_md),
        'visual_score': calculate_visual_similarity(original_md, converted_md)
    }
```

#### Level 4: Golden Dataset
- Curate set of diverse PDFs with verified Markdown outputs
- Run regression tests on each release
- Track metrics:
  - Overall accuracy score
  - Per-element-type accuracy
  - Failure cases

### Practical Implementation

```python
class ConversionAccuracyMetrics:
    """Calculate various accuracy metrics for PDF to Markdown conversion."""
    
    def __init__(self, reference: str, generated: str):
        self.reference = reference
        self.generated = generated
    
    def text_accuracy(self) -> float:
        """Normalized edit distance."""
        import Levenshtein
        distance = Levenshtein.distance(self.reference, self.generated)
        max_len = max(len(self.reference), len(self.generated))
        return 1 - (distance / max_len) if max_len > 0 else 1.0
    
    def structure_accuracy(self) -> Dict[str, float]:
        """Compare structural elements."""
        ref_ast = parse_markdown_ast(self.reference)
        gen_ast = parse_markdown_ast(self.generated)
        
        return {
            'headings': self._compare_headings(ref_ast, gen_ast),
            'lists': self._compare_lists(ref_ast, gen_ast),
            'tables': self._compare_tables(ref_ast, gen_ast),
            'code_blocks': self._compare_code_blocks(ref_ast, gen_ast),
        }
    
    def semantic_accuracy(self) -> float:
        """Embedding-based similarity (requires model)."""
        # Using sentence-transformers or similar
        ref_embedding = embed_text(self.reference)
        gen_embedding = embed_text(self.generated)
        return cosine_similarity(ref_embedding, gen_embedding)
```

### Benchmarking Against Other Tools

To differentiate from pymupdf:

1. **Create benchmark suite** with diverse PDF types
2. **Run all tools** (pymupdf, pdfplumber, unpdf) on same inputs
3. **Measure**:
   - Text extraction accuracy
   - Structure preservation
   - Table extraction quality
   - Processing speed
   - File size support
4. **Document strengths**: Where does unpdf excel?

### Quality Thresholds

Suggested minimum thresholds for production use:

- **Text Accuracy**: ≥ 95% (edit distance)
- **Heading Preservation**: ≥ 90%
- **List Structure**: ≥ 85%
- **Table Accuracy**: ≥ 80% (tables are hard!)
- **Overall Structure**: ≥ 85%

## Tools and Libraries

### Python Libraries for Metrics

```bash
pip install python-Levenshtein  # Edit distance
pip install nltk                # BLEU, tokenization
pip install rouge-score         # ROUGE metrics
pip install sentence-transformers  # Semantic embeddings
pip install markdown            # Parse Markdown
pip install beautifulsoup4      # HTML comparison
```

### Markdown AST Parsers
- `mistune` - Fast Markdown parser with AST
- `markdown-it-py` - Python port of markdown-it
- `marko` - CommonMark parser with AST

## Example Test Suite

```python
def test_obsidian_example():
    """Test against known good conversion."""
    with open('example-obsidian/obsidian-input.md') as f:
        reference = f.read()
    
    # Convert PDF
    pdf_path = 'example-obsidian/obsidian-input.pdf'
    generated = convert_pdf_to_markdown(pdf_path)
    
    # Calculate metrics
    metrics = ConversionAccuracyMetrics(reference, generated)
    
    # Assert minimum quality
    assert metrics.text_accuracy() >= 0.90, "Text accuracy too low"
    
    struct = metrics.structure_accuracy()
    assert struct['headings'] >= 0.95, "Heading accuracy too low"
    assert struct['lists'] >= 0.85, "List accuracy too low"
    assert struct['tables'] >= 0.80, "Table accuracy too low"
    
    # Generate report
    print(f"Text Accuracy: {metrics.text_accuracy():.2%}")
    print(f"Structure Accuracy: {struct}")
```

## Continuous Monitoring

1. **Track metrics over time** in CI/CD
2. **Alert on regressions** (accuracy drops)
3. **Maintain quality dashboard** showing trends
4. **Collect real-world examples** for test suite expansion

## Conclusion

For unpdf, the recommended approach is:

1. **Start simple**: Edit distance + element counting
2. **Add structure**: AST-based comparison
3. **Enhance with semantics**: Embeddings for content verification
4. **Build golden dataset**: Curated examples with known outputs
5. **Automate regression testing**: Run on every commit

Focus on **structural accuracy** as the key differentiator from pymupdf, which excels at text extraction but may miss formatting nuances.
