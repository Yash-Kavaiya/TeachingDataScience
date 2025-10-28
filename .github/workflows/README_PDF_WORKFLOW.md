# Save All PDFs GitHub Action

## Overview

This GitHub Action automatically finds, collects, and saves all PDF files in the repository.

## Features

- Finds all PDF files in the repository
- Creates a compressed archive (`.tar.gz`) of all PDFs
- Generates an inventory report with statistics
- Uploads artifacts that can be downloaded
- Optional: Create GitHub releases with PDF backups

## How to Use

### Manual Trigger

1. Go to your repository on GitHub
2. Click on **Actions** tab
3. Select **Save All PDFs** workflow from the left sidebar
4. Click **Run workflow** button
5. Select the branch and click **Run workflow**

### Automatic Triggers

The workflow runs automatically:

- **Weekly**: Every Sunday at midnight UTC (via cron schedule)
- **On PDF changes**: Whenever a PDF file is added or modified in the repository

### Download Saved PDFs

After the workflow runs:

1. Go to the **Actions** tab
2. Click on the completed workflow run
3. Scroll down to **Artifacts** section
4. Download the artifact named `all-pdfs-[run-number]`
5. Extract the `.tar.gz` file to access all PDFs

## What Gets Saved

The workflow creates:

1. **Compressed Archive**: `all-pdfs-[timestamp].tar.gz`
   - Contains all PDF files with original directory structure
   - Compressed for efficient storage and download

2. **PDF Report**: `pdf_report.md`
   - List of all PDF files found
   - Total count and size statistics
   - Breakdown by directory

3. **PDF List**: `pdf_list.txt`
   - Simple text file listing all PDF paths

## Configuration Options

### Change Schedule

Edit line 8 in `save-all-pdfs.yml`:

```yaml
schedule:
  - cron: '0 0 * * 0'  # Current: Weekly on Sunday
```

Examples:
- Daily at midnight: `'0 0 * * *'`
- Monthly on 1st: `'0 0 1 * *'`
- Every 6 hours: `'0 */6 * * *'`

### Artifact Retention

Change how long artifacts are kept (default: 90 days):

```yaml
retention-days: 90  # Change to desired number of days
```

### Enable GitHub Releases

To automatically create releases with PDF backups:

1. Uncomment lines 116-128 in `save-all-pdfs.yml`
2. Each manual run will create a new release with PDFs attached

## Artifact Storage

- Artifacts are stored in GitHub Actions
- Default retention: 90 days
- Artifacts count against repository storage quota
- Can be downloaded via GitHub UI or API

## Requirements

- GitHub Actions enabled in repository
- No additional secrets or tokens required (uses default GITHUB_TOKEN)
- Works on public and private repositories

## Troubleshooting

### Workflow not appearing

- Make sure the workflow file is in `.github/workflows/` directory
- File must have `.yml` or `.yaml` extension
- Check GitHub Actions is enabled in repository settings

### Workflow failing

- Check the workflow logs in Actions tab
- Ensure there are PDF files in the repository
- Verify repository permissions

### Cannot download artifacts

- Artifacts expire after retention period (default: 90 days)
- Re-run the workflow to generate new artifacts

## Technical Details

- **Runner**: Ubuntu Latest
- **Checkout**: Full repository history
- **Archive Format**: tar.gz (gzip compression)
- **File Search**: Recursive, excludes `.git` directory
- **Upload**: GitHub Actions Artifacts v4

## Examples

### Current Repository Stats

Based on the repository scan, you have approximately:
- **150+** PDF files across multiple directories
- Main locations:
  - `Admin/Interview/docs/` - Interview preparation materials
  - `Admin/Syllabii/` - Course syllabi
  - `Code/*/data/` - Various data files
  - `LaTeX/images/` - Image PDFs

### Estimated Archive Size

The compressed archive will be significantly smaller than the total PDF size due to compression.

## Support

For issues or questions:
- Check workflow logs in GitHub Actions tab
- Review this documentation
- Check GitHub Actions documentation: https://docs.github.com/en/actions

## License

This workflow is part of the TeachingDataScience repository.
