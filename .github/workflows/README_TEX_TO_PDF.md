# Compile TEX to PDF GitHub Action

## Overview

This GitHub Action automatically finds all `.tex` files in your repository and compiles them to PDF using LaTeX.

## Features

- 🔍 **Automatic Discovery**: Finds all `.tex` files in the repository
- 📦 **LaTeX Compilation**: Uses `pdflatex` to compile each `.tex` file to PDF
- 📊 **Detailed Reports**: Generates compilation reports with success/failure statistics
- 💾 **Artifact Storage**: Uploads compiled PDFs as downloadable artifacts
- 🗜️ **Compressed Archive**: Creates a `.tar.gz` archive of all generated PDFs
- ⚡ **Error Handling**: Gracefully handles compilation failures and reports them

## How to Use

### Manual Trigger

1. Go to your repository on GitHub
2. Click on **Actions** tab
3. Select **Compile TEX to PDF** workflow from the left sidebar
4. Click **Run workflow** button
5. Select the branch and click **Run workflow**

### Automatic Triggers

The workflow runs automatically when:

- **On .tex file changes**: Whenever a `.tex` file is modified and pushed to main/master branch
- **Weekly**: Every Monday at 2 AM UTC (via cron schedule)
- **Manual**: Can be triggered manually anytime from the Actions tab

### Download Compiled PDFs

After the workflow runs:

1. Go to the **Actions** tab
2. Click on the completed workflow run
3. Scroll down to **Artifacts** section
4. Download the artifact named `compiled-pdfs-[run-number]`
5. Extract the `.tar.gz` file to access all PDFs

## What Gets Generated

The workflow creates:

1. **Individual PDF Files**: Each `.tex` file is compiled to a corresponding `.pdf` file
2. **Compressed Archive**: `compiled-pdfs-[timestamp].tar.gz`
   - Contains all successfully compiled PDF files
   - Preserves original directory structure
3. **Compilation Report**: `compilation_report.md`
   - Summary of successful and failed compilations
   - List of all generated PDFs
   - Error details for failed compilations

## LaTeX Packages Included

The workflow installs the following LaTeX packages:

- `texlive-latex-extra` - Extended LaTeX packages
- `texlive-fonts-recommended` - Recommended fonts
- `texlive-fonts-extra` - Additional fonts
- `texlive-xetex` - XeTeX engine
- `latexmk` - LaTeX build automation

## Compilation Process

For each `.tex` file:

1. **First Pass**: Compiles the `.tex` file with `pdflatex`
2. **Second Pass**: Runs `pdflatex` again to resolve cross-references
3. **Validation**: Checks if PDF was successfully generated
4. **Organization**: Copies PDF to output directory maintaining structure

## Configuration Options

### Change Schedule

Edit the cron schedule in `compile-tex-to-pdf.yml`:

```yaml
schedule:
  - cron: '0 2 * * 1'  # Current: Weekly on Monday at 2 AM UTC
```

Examples:
- Daily at midnight: `'0 0 * * *'`
- Twice weekly (Mon & Thu): `'0 2 * * 1,4'`
- Monthly on 1st: `'0 2 1 * *'`

### Artifact Retention

Change how long artifacts are kept (default: 90 days):

```yaml
retention-days: 90  # Change to desired number of days
```

### Add More LaTeX Packages

If your `.tex` files require additional packages, add them to the installation step:

```yaml
- name: Install LaTeX
  run: |
    sudo apt-get update
    sudo apt-get install -y texlive-latex-extra texlive-fonts-recommended \
      texlive-fonts-extra texlive-xetex latexmk \
      texlive-bibtex-extra biber  # Add more packages here
```

### Use Different LaTeX Engine

To use XeLaTeX or LuaLaTeX instead of pdflatex, modify the compilation command:

```bash
# For XeLaTeX
xelatex -interaction=nonstopmode -halt-on-error "$tex_base.tex"

# For LuaLaTeX
lualatex -interaction=nonstopmode -halt-on-error "$tex_base.tex"
```

## Troubleshooting

### Common Compilation Errors

1. **Missing Packages**
   - Check the compilation report for error details
   - Add required packages to the installation step
   - Example: `sudo apt-get install -y texlive-science`

2. **File Not Found Errors**
   - Ensure all included files (images, bibliography, etc.) are in the repository
   - Check relative paths in `\includegraphics`, `\input`, `\include` commands

3. **Encoding Issues**
   - Use `\usepackage[utf8]{inputenc}` in your `.tex` files
   - Or switch to XeLaTeX which handles UTF-8 natively

4. **Bibliography Errors**
   - Install `biber` or `bibtex`: `sudo apt-get install -y texlive-bibtex-extra biber`
   - Add bibtex/biber compilation steps between pdflatex runs

### Workflow Not Running

- Ensure the workflow file is in `.github/workflows/` directory
- Check GitHub Actions is enabled in repository settings
- Verify the branch name matches the trigger configuration

### No PDFs Generated

- Check the compilation report in the artifacts
- Review workflow logs for specific error messages
- Test compilation locally to identify issues

## Advanced Usage

### Selective Compilation

To compile only specific `.tex` files, modify the find command:

```bash
# Only compile files in a specific directory
find ./Admin/AI-lectures-MarcToussaint -type f -name "*.tex" > tex_list.txt

# Only compile files matching a pattern
find . -type f -name "script.tex" > tex_list.txt
```

### Add Bibliography Support

For documents with bibliographies, add these steps between the pdflatex runs:

```yaml
- name: Compile TEX files to PDF with Bibliography
  run: |
    pdflatex -interaction=nonstopmode "$tex_base.tex"
    bibtex "$tex_base" || true
    pdflatex -interaction=nonstopmode "$tex_base.tex"
    pdflatex -interaction=nonstopmode "$tex_base.tex"
```

### Commit PDFs to Repository

To automatically commit generated PDFs back to the repository:

```yaml
- name: Commit PDFs to repository
  run: |
    git config --local user.email "github-actions[bot]@users.noreply.github.com"
    git config --local user.name "github-actions[bot]"
    git add compiled_pdfs/*.pdf
    git commit -m "Auto-generate PDFs from .tex files" || echo "No changes to commit"
    git push
```

**Note**: Be cautious with this approach as it can significantly increase repository size.

## Repository Statistics

Based on the repository scan, you have approximately:

- **100+** `.tex` files in the repository
- Main locations:
  - `Admin/AI-lectures-MarcToussaint/ArtificialIntelligence/` - AI course materials
  - `Admin/AI-lectures-MarcToussaint/MachineLearning/` - ML course materials
  - `Admin/AI-lectures-MarcToussaint/Optimization/` - Optimization course materials
  - `Admin/AI-lectures-MarcToussaint/Robotics/` - Robotics course materials

## Performance

- **Installation Time**: ~2-3 minutes (LaTeX packages)
- **Compilation Time**: Varies by file complexity (typically 5-30 seconds per file)
- **Total Runtime**: Approximately 10-30 minutes for 100+ files

## Requirements

- GitHub Actions enabled in repository
- No additional secrets or tokens required
- Works on public and private repositories
- Ubuntu runner with at least 2GB RAM

## Best Practices

1. **Test Locally First**: Ensure your `.tex` files compile locally before relying on the workflow
2. **Use Relative Paths**: Keep all resources (images, includes) in relative paths
3. **Monitor Artifact Storage**: GitHub has storage limits for artifacts
4. **Regular Cleanup**: Remove old artifacts if storage becomes an issue
5. **Version Control**: Keep both `.tex` and `.pdf` files in version control for critical documents

## Limitations

- Some complex LaTeX packages may not be available in standard texlive distributions
- Large documents with many images may take longer to compile
- Compilation errors in one file don't stop processing of other files
- Artifacts have a maximum retention period

## Support

For issues or questions:
- Check the compilation report in the workflow artifacts
- Review workflow logs in GitHub Actions tab
- Test `.tex` file compilation locally
- Check LaTeX error messages for specific issues

## Related Workflows

- **save-all-pdfs.yml**: Collects all existing PDF files in the repository
- **compile-tex-to-pdf.yml**: This workflow - compiles .tex files to PDF

## License

This workflow is part of the TeachingDataScience repository.
