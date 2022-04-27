from core import pdf
from django.conf import settings
from django.http import HttpResponse


def make_pdf(header, data, filename, http_status):
    site_name = settings.SITE_NAME

    pdf_data = [
        (pdf.Constant.DT_CAPTION, 'Мой список покупок:'),
        (pdf.Constant.DT_EMPTYLINE, '')
    ]

    for ingredient in data:
        pdf_data.append((
            pdf.Constant.DT_TEXT,
            '□ {name} - {amount} {unit}'.format(
                name=ingredient['ingredient__name'],
                amount=ingredient['amount_total'],
                unit=ingredient['ingredient__measurement_unit']
            )))

    pdf_obj = pdf.PDFMaker()
    pdf_obj.data = pdf_data
    pdf_obj.footer_text = f'Список покупок сгенерирован на сайте {site_name}'

    content = pdf_obj.pdf_render()

    response = HttpResponse(
        content=content,
        content_type='application/pdf',
        status=http_status)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response
