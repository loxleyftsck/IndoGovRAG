# Contributing to IndoGovRAG

Thank you for your interest in contributing to IndoGovRAG! 🎉

## 🌳 Branch Strategy

We follow **Git Flow** branching model:

```
main (production)
  └─ develop (integration)
      ├─ feature/data-collection
      ├─ feature/indonesian-preprocessing
      ├─ bugfix/pdf-extraction
      └─ hotfix/quota-tracker
```

### Branch Types

- **`main`** - Production-ready code, tagged releases only
- **`develop`** - Integration branch for features
- **`feature/*`** - New features (e.g., `feature/hybrid-search`)
- **`bugfix/*`** - Bug fixes (e.g., `bugfix/pii-detection`)
- **`hotfix/*`** - Critical production fixes
- **`release/*`** - Release preparation (e.g., `release/v0.2.0`)

---

## 🚀 Development Workflow

### 1. Fork & Clone
```bash
git clone https://github.com/loxleyftsck/IndoGovRAG.git
cd IndoGovRAG
git checkout develop
```

### 2. Create Feature Branch
```bash
# From develop branch
git checkout -b feature/your-feature-name
```

### 3. Make Changes
- Write clean, documented code
- Follow existing code style (PEP 8 for Python)
- Add tests for new features
- Update documentation

### 4. Commit
```bash
# Use conventional commits
git commit -m "✨ feat: add hybrid search retrieval"
git commit -m "🐛 fix: resolve PDF extraction encoding issue"
git commit -m "📝 docs: update embedding benchmark guide"
```

**Commit Format:**
```
<emoji> <type>: <description>

[optional body]
[optional footer]
```

**Types:**
- `feat` ✨ - New feature
- `fix` 🐛 - Bug fix
- `docs` 📝 - Documentation
- `refactor` ♻️ - Code refactoring
- `perf` ⚡ - Performance improvement
- `test` ✅ - Testing
- `chore` 🔧 - Maintenance

### 5. Push & PR
```bash
git push origin feature/your-feature-name
```

Then open PR on GitHub: `feature/your-feature-name` → `develop`

---

## 📋 Pull Request Guidelines

### PR Title Format
```
✨ feat: Add hybrid search (vector + BM25)
🐛 fix: Handle scanned PDFs in text extraction
📝 docs: Update deployment guide for Vercel
```

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style
- [ ] Self-reviewed code
- [ ] Commented complex logic
- [ ] Updated documentation
- [ ] Added tests
```

---

## 🧪 Testing Requirements

### Before Submitting PR
```bash
# Run all tests
pytest tests/

# Check code style
flake8 src/

# Format code
black src/ tests/
```

### Test Coverage
- Aim for >80% coverage
- All new features must have tests
- Bug fixes should include regression tests

---

## 📝 Code Style

### Python (PEP 8)
```python
# Good
def process_document(doc_path: str, chunk_size: int = 512) -> List[str]:
    """
    Process document into chunks.
    
    Args:
        doc_path: Path to document
        chunk_size: Size of chunks in tokens
    
    Returns:
        List of text chunks
    """
    pass

# Bad
def processDoc(path,size=512):
    pass
```

### Naming Conventions
- **Files:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions:** `snake_case()`
- **Constants:** `UPPER_CASE`
- **Private:** `_leading_underscore`

---

## 🐛 Reporting Bugs

Use GitHub Issues with template:

**Title:** `[BUG] PDF extraction fails for scanned documents`

**Description:**
```markdown
**Describe the bug**
Clear description

**To Reproduce**
1. Steps to reproduce
2. ...

**Expected behavior**
What should happen

**Environment**
- OS: Windows 11
- Python: 3.9.12
- Version: 0.1.0

**Screenshots**
If applicable
```

---

## 💡 Feature Requests

**Title:** `[FEATURE] Add reranking for better retrieval`

**Description:**
```markdown
**Problem**
What problem does this solve?

**Proposed Solution**
How would it work?

**Alternatives**
Other options considered

**Additional Context**
Any other info
```

---

## 📚 Documentation

### Update These When Needed
- `README.md` - For user-facing changes
- `docs/*.md` - For technical details
- `CHANGELOG.md` - For all changes
- Docstrings - For code changes

---

## 🎯 Week-Specific Contributions

### Week 1 (Current)
- Data collection scripts
- Indonesian text preprocessing
- PII detection
- Vector store setup

### Week 2 (Upcoming)
- RAGAS evaluation
- Expanded test dataset
- Baseline benchmarks

### Week 3
- Hybrid search
- Reranking
- A/B testing

---

## ✅ Checklist Before Submit

- [ ] Code works locally
- [ ] All tests pass
- [ ] Code is documented
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts
- [ ] Branch is up-to-date with develop
- [ ] Commit messages follow convention
- [ ] PR description is complete

---

## 🤝 Code Review Process

1. **Automated Checks** - CI/CD runs tests
2. **Maintainer Review** - Code review by maintainer
3. **Feedback** - Address comments
4. **Approval** - 1 approval required
5. **Merge** - Squash & merge to develop

---

## 📞 Questions?

- Open a discussion on GitHub
- Check existing issues/PRs
- Tag @loxleyftsck for questions

---

**Happy Contributing!** 🚀

Built with ❤️ for Indonesia 🇮🇩
