"""
Management command to generate sample PDF files for books that don't have PDFs yet.
Usage: python manage.py generate_sample_pdfs
"""

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from apps.books.models import Book


class Command(BaseCommand):
    help = 'Generate sample PDF files for books without PDFs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing PDFs'
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # Get books without files (or all if --force)
        if force:
            books = Book.objects.all()
            self.stdout.write(self.style.WARNING(f'Regenerating PDFs for {books.count()} books...'))
        else:
            books = Book.objects.filter(file='')
            self.stdout.write(self.style.SUCCESS(f'Found {books.count()} books without PDFs'))
        
        if not books.exists():
            self.stdout.write(self.style.SUCCESS('✅ All books already have PDFs!'))
            return

        count = 0
        for book in books:
            try:
                # Generate sample PDF content
                pdf_bytes = self._generate_sample_pdf(book)
                
                # Save to book
                filename = f'{book.id}_{book.title[:30]}.pdf'
                book.file.save(
                    filename,
                    ContentFile(pdf_bytes),
                    save=True
                )
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Generated PDF for: {book.title}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed for {book.title}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Successfully generated {count}/{books.count()} PDFs')
        )

    @staticmethod
    def _generate_sample_pdf(book):
        """Generate a simple sample PDF for a book"""
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Title page
        p.setFont("Helvetica-Bold", 24)
        p.drawString(50, height - 100, book.title)
        
        p.setFont("Helvetica", 14)
        p.drawString(50, height - 150, f"by {book.author}")
        
        # Book info
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 200, f"Pages: {book.total_pages}")
        p.drawString(50, height - 220, f"Language: {book.language}")
        
        if book.publisher:
            p.drawString(50, height - 240, f"Publisher: {book.publisher}")
        
        # Sample content
        p.setFont("Helvetica", 12)
        y = height - 300
        p.drawString(50, y, "SAMPLE PDF - This is a placeholder for the full book content")
        y -= 30
        
        # Add some sample pages
        for page_num in range(1, min(book.total_pages or 10, 11)):
            p.showPage()
            p.setFont("Helvetica", 12)
            p.drawString(50, height - 50, f"Page {page_num}")
            p.setFont("Helvetica", 10)
            p.drawString(50, height - 100, f"Your book '{book.title}' would display here")
            
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
