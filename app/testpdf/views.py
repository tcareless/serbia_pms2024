from django.shortcuts import render, redirect
from .forms import PDFUploadForm

def upload_pdf(request):
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Save the file to the model
            return redirect('pdf_success')  # Redirect to success page
    else:
        form = PDFUploadForm()
    return render(request, 'testpdf/upload_pdf.html', {'form': form})


def upload_success(request):
    return render(request, 'testpdf/success.html')
