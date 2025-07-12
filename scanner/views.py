from django.shortcuts import render
from .models import QRCode
import qrcode
from django.core.files.storage import FileSystemStorage
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path
from pyzbar.pyzbar import decode
from PIL import Image

# Create your views here.
def generate_qr(req):
  qr_image_url=None
  if req.method=="POST":
    mobile_number=req.POST.get('mobile_number')
    data = req.POST.get('qr_data')

    if not mobile_number or len(mobile_number) !=10 or not mobile_number.isdigit():
      return render(req,'scanner/generate.html',{'error':'Invaild mobile number'})
    
    qr_content = f"{data}|{mobile_number}"
    qr=qrcode.make(qr_content)
    qr_image_io = BytesIO()
    qr.save(qr_image_io,format='PNG')
    qr_image_io.seek(0)

    qr_stroage_path =settings.MEDIA_ROOT/'qr_codes'
    fs = FileSystemStorage(location=qr_stroage_path,base_url='/media/qr_codes/')
    filename=f"{data}_{mobile_number}.png"
    qr_image_content=ContentFile(qr_image_io.read(),name=filename)
    filepath=fs.save(filename,qr_image_content)
    qr_image_url=fs.url(filename)
    QRCode.objects.create(data=data,
    mobile_number=mobile_number)

  return render(req,'scanner/generate.html',{'qr_image_url':qr_image_url})

def scan_qr(req):
  result=None
  if req.method == "POST" and req.FILES.get('qr_image'):
    qr_image=req.FILES['qr_image']
    mobile_number=req.POST.get('mobile_number')

    if not mobile_number or len(mobile_number) !=10 or not mobile_number.isdigit():
        return render(req,'scanner/scan.html',{'error':'Invalid mobile number'})

    fs = FileSystemStorage()
    filename = fs.save(qr_image.name,qr_image)
    image_path =Path(fs.location)/filename
    try:
      image = Image.open(image_path)
      decoded_object=decode(image)
      
      if decoded_object:
        qr_content=decoded_object[0].data.decode('utf-8').strip()
        qr_data,qr_mobile_number=qr_content.split('|')
        qr_entry = QRCode.objects.filter(data=qr_data,mobile_number=mobile_number).first()

        if qr_entry and qr_mobile_number == mobile_number:
          result = "scan Success : vaild QR code for the provided mobile number "
          qr_entry.delete()

          qr_image_path=settings.MEDIA_ROOT / 'qr_codes' / f"{qr_data}_{qr_mobile_number}.png"

          if qr_image_path.exists():
            qr_image_path.unlink()
          
          if image_path.exists():
            image_path.unlink()
        else:
          result = "Scan Failed: Invaild QR Code or mobile number mismatch"
      else:
        result = "No QR Code detected in the image."
    except Exception as e:
      result=f"Eroor PRoceesing the image {str(e)}"
    finally:
      if image_path.exists():
        image_path.unlink()
  return render(req,'scanner/scan.html',{'result':result})