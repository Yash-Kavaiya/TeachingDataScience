#!/usr/bin/env python3
"""
Optimized LaTeX to PDF Converter
Converts all .tex files in the repository to PDF format.
Saves output to Artifacts folder maintaining directory structure.
"""

import os
import subprocess
import sys
import logging
import argparse
import shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Tuple, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tex_conversion.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of a single conversion attempt."""
    tex_file: Path
    pdf_file: Optional[Path]
    success: bool
    error_message: str = ""
    conversion_time: float = 0.0


class TexToPdfConverter:
    """Optimized converter for LaTeX files to PDF."""

    def __init__(
        self,
        source_dir: Path,
        output_dir: Path,
        max_workers: int = 4,
        latex_engine: str = "pdflatex",
        timeout: int = 120,
        clean_aux: bool = True
    ):
        """
        Initialize the converter.

        Args:
            source_dir: Root directory to search for .tex files
            output_dir: Directory to save PDF outputs (Artifacts folder)
            max_workers: Number of parallel conversion processes
            latex_engine: LaTeX engine to use (pdflatex, xelatex, lualatex)
            timeout: Timeout for each conversion in seconds
            clean_aux: Whether to clean auxiliary files after conversion
        """
        self.source_dir = Path(source_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.max_workers = max_workers
        self.latex_engine = latex_engine
        self.timeout = timeout
        self.clean_aux = clean_aux

        # Auxiliary file extensions to clean
        self.aux_extensions = [
            '.aux', '.log', '.out', '.toc', '.lof', '.lot',
            '.fls', '.fdb_latexmk', '.synctex.gz', '.bbl',
            '.blg', '.nav', '.snm', '.vrb', '.idx', '.ilg',
            '.ind', '.glo', '.gls', '.ist'
        ]

    def find_tex_files(self) -> List[Path]:
        """Find all .tex files in source directory."""
        tex_files = list(self.source_dir.rglob("*.tex"))
        logger.info(f"Found {len(tex_files)} .tex files")
        return tex_files

    def get_output_path(self, tex_file: Path) -> Path:
        """
        Calculate output PDF path maintaining directory structure.

        Args:
            tex_file: Path to the source .tex file

        Returns:
            Path where the PDF should be saved
        """
        # Get relative path from source directory
        try:
            relative_path = tex_file.relative_to(self.source_dir)
        except ValueError:
            relative_path = tex_file.name

        # Create output path with .pdf extension
        pdf_path = self.output_dir / relative_path.with_suffix('.pdf')
        return pdf_path

    def convert_single(self, tex_file: Path) -> ConversionResult:
        """
        Convert a single .tex file to PDF.

        Args:
            tex_file: Path to the .tex file

        Returns:
            ConversionResult with success/failure information
        """
        start_time = time.time()
        output_pdf = self.get_output_path(tex_file)

        # Create output directory if it doesn't exist
        output_pdf.parent.mkdir(parents=True, exist_ok=True)

        # Working directory is the directory containing the .tex file
        # This is important for relative paths in \input, \include, etc.
        work_dir = tex_file.parent

        try:
            # Run pdflatex twice to resolve references
            for run in range(2):
                result = subprocess.run(
                    [
                        self.latex_engine,
                        '-interaction=nonstopmode',
                        '-halt-on-error',
                        '-output-directory', str(work_dir),
                        str(tex_file.name)
                    ],
                    cwd=str(work_dir),
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

                if result.returncode != 0 and run == 1:
                    # Only fail on second run to allow first run to create aux files
                    error_msg = self._extract_error(result.stdout + result.stderr)
                    return ConversionResult(
                        tex_file=tex_file,
                        pdf_file=None,
                        success=False,
                        error_message=error_msg,
                        conversion_time=time.time() - start_time
                    )

            # Check if PDF was created
            generated_pdf = work_dir / tex_file.with_suffix('.pdf').name

            if generated_pdf.exists():
                # Move PDF to output directory
                shutil.copy2(generated_pdf, output_pdf)

                # Clean up generated PDF in source dir if different from output
                if generated_pdf != output_pdf:
                    generated_pdf.unlink()

                # Clean auxiliary files
                if self.clean_aux:
                    self._clean_aux_files(tex_file)

                return ConversionResult(
                    tex_file=tex_file,
                    pdf_file=output_pdf,
                    success=True,
                    conversion_time=time.time() - start_time
                )
            else:
                return ConversionResult(
                    tex_file=tex_file,
                    pdf_file=None,
                    success=False,
                    error_message="PDF file was not generated",
                    conversion_time=time.time() - start_time
                )

        except subprocess.TimeoutExpired:
            return ConversionResult(
                tex_file=tex_file,
                pdf_file=None,
                success=False,
                error_message=f"Conversion timed out after {self.timeout}s",
                conversion_time=time.time() - start_time
            )
        except Exception as e:
            return ConversionResult(
                tex_file=tex_file,
                pdf_file=None,
                success=False,
                error_message=str(e),
                conversion_time=time.time() - start_time
            )

    def _extract_error(self, log_output: str) -> str:
        """Extract meaningful error message from LaTeX log."""
        lines = log_output.split('\n')
        error_lines = []

        for i, line in enumerate(lines):
            if '!' in line or 'Error' in line or 'error' in line:
                error_lines.append(line.strip())
                # Include next line for context
                if i + 1 < len(lines):
                    error_lines.append(lines[i + 1].strip())
                if len(error_lines) >= 4:
                    break

        if error_lines:
            return ' | '.join(error_lines[:4])
        return "Unknown error - check log file"

    def _clean_aux_files(self, tex_file: Path) -> None:
        """Clean auxiliary files generated during compilation."""
        base_path = tex_file.with_suffix('')
        for ext in self.aux_extensions:
            aux_file = Path(str(base_path) + ext)
            if aux_file.exists():
                try:
                    aux_file.unlink()
                except Exception:
                    pass

    def convert_all(self, tex_files: Optional[List[Path]] = None) -> Tuple[List[ConversionResult], List[ConversionResult]]:
        """
        Convert all .tex files to PDF using parallel processing.

        Args:
            tex_files: Optional list of specific files to convert.
                      If None, finds all .tex files in source_dir.

        Returns:
            Tuple of (successful_results, failed_results)
        """
        if tex_files is None:
            tex_files = self.find_tex_files()

        if not tex_files:
            logger.warning("No .tex files found to convert")
            return [], []

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        successful = []
        failed = []
        total = len(tex_files)

        logger.info(f"Starting conversion of {total} files with {self.max_workers} workers")

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all conversion jobs
            future_to_file = {
                executor.submit(self.convert_single, tex_file): tex_file
                for tex_file in tex_files
            }

            # Process completed conversions
            for i, future in enumerate(as_completed(future_to_file), 1):
                tex_file = future_to_file[future]
                try:
                    result = future.result()
                    if result.success:
                        successful.append(result)
                        logger.info(f"[{i}/{total}] SUCCESS: {tex_file.name} ({result.conversion_time:.1f}s)")
                    else:
                        failed.append(result)
                        logger.warning(f"[{i}/{total}] FAILED: {tex_file.name} - {result.error_message}")
                except Exception as e:
                    failed.append(ConversionResult(
                        tex_file=tex_file,
                        pdf_file=None,
                        success=False,
                        error_message=str(e)
                    ))
                    logger.error(f"[{i}/{total}] ERROR: {tex_file.name} - {e}")

        return successful, failed

    def generate_report(self, successful: List[ConversionResult], failed: List[ConversionResult]) -> str:
        """Generate a summary report of the conversion process."""
        total = len(successful) + len(failed)
        success_rate = (len(successful) / total * 100) if total > 0 else 0

        report = f"""
{'='*60}
LATEX TO PDF CONVERSION REPORT
{'='*60}

Total Files Processed: {total}
Successful Conversions: {len(successful)} ({success_rate:.1f}%)
Failed Conversions: {len(failed)} ({100 - success_rate:.1f}%)

Output Directory: {self.output_dir}
"""

        if failed:
            report += f"\n{'='*60}\nFAILED CONVERSIONS:\n{'='*60}\n"
            for result in failed[:20]:  # Show first 20 failures
                report += f"\n- {result.tex_file.name}\n  Error: {result.error_message}\n"
            if len(failed) > 20:
                report += f"\n... and {len(failed) - 20} more failures\n"

        if successful:
            total_time = sum(r.conversion_time for r in successful)
            avg_time = total_time / len(successful) if successful else 0
            report += f"\n{'='*60}\nPERFORMANCE:\n{'='*60}\n"
            report += f"Total Conversion Time: {total_time:.1f}s\n"
            report += f"Average Time per File: {avg_time:.2f}s\n"

        return report


def check_latex_installed() -> bool:
    """Check if pdflatex is installed."""
    try:
        result = subprocess.run(['pdflatex', '--version'], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_latex() -> bool:
    """Attempt to install texlive-latex-base."""
    logger.info("pdflatex not found. Attempting to install texlive...")
    try:
        subprocess.run(['apt-get', 'update'], check=True, capture_output=True)
        subprocess.run(
            ['apt-get', 'install', '-y', 'texlive-latex-base', 'texlive-latex-extra', 'texlive-fonts-recommended'],
            check=True,
            capture_output=True
        )
        logger.info("texlive installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install texlive: {e}")
        return False
    except FileNotFoundError:
        logger.error("apt-get not available")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert LaTeX files to PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--source', '-s',
        type=str,
        default='/home/user/TeachingDataScience',
        help='Source directory containing .tex files'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='/home/user/TeachingDataScience/Artifacts/PDFs',
        help='Output directory for PDF files'
    )
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )
    parser.add_argument(
        '--engine', '-e',
        type=str,
        default='pdflatex',
        choices=['pdflatex', 'xelatex', 'lualatex'],
        help='LaTeX engine to use'
    )
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=120,
        help='Timeout per file in seconds (default: 120)'
    )
    parser.add_argument(
        '--no-clean',
        action='store_true',
        help='Do not clean auxiliary files'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='List files without converting'
    )
    parser.add_argument(
        '--pattern', '-p',
        type=str,
        default=None,
        help='Only convert files matching this pattern (e.g., "*/MachineLearning/*")'
    )

    args = parser.parse_args()

    # Initialize converter first (needed for dry-run)
    converter = TexToPdfConverter(
        source_dir=args.source,
        output_dir=args.output,
        max_workers=args.workers,
        latex_engine=args.engine,
        timeout=args.timeout,
        clean_aux=not args.no_clean
    )

    # Find files
    tex_files = converter.find_tex_files()

    # Filter by pattern if specified
    if args.pattern:
        from fnmatch import fnmatch
        tex_files = [f for f in tex_files if fnmatch(str(f), args.pattern)]
        logger.info(f"Filtered to {len(tex_files)} files matching pattern '{args.pattern}'")

    if args.dry_run:
        print(f"\nDry run - would convert {len(tex_files)} files:")
        for f in tex_files[:30]:
            output_path = converter.get_output_path(f)
            print(f"  {f.relative_to(converter.source_dir)}")
            print(f"    -> {output_path.relative_to(converter.source_dir)}")
        if len(tex_files) > 30:
            print(f"  ... and {len(tex_files) - 30} more")
        print(f"\nOutput directory: {args.output}")
        return

    # Check/install LaTeX (only for actual conversion)
    if not check_latex_installed():
        logger.warning("pdflatex not found on system")
        if not install_latex():
            logger.error("Could not install LaTeX. Please install texlive manually:")
            logger.error("  sudo apt-get install texlive-latex-base texlive-latex-extra")
            sys.exit(1)

    # Convert files
    successful, failed = converter.convert_all(tex_files)

    # Generate and print report
    report = converter.generate_report(successful, failed)
    print(report)

    # Save report to file
    report_path = Path(args.output) / 'conversion_report.txt'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
    logger.info(f"Report saved to {report_path}")

    # Exit with error code if there were failures
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
