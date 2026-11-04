"""Fill the retained BEU Word form in place; LibreOffice renders that same DOCX."""
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from threading import Lock
from zipfile import ZipFile
from zipfile import ZipInfo, ZIP_DEFLATED
import base64
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image

from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.filebased import FileBasedCache
from lxml import etree as ET

from .booking_slip_pdf import BookingSlipPDFError

TEMPLATE = Path(__file__).resolve().parent.parent / 'document_templates' / 'job_order_request.docx'
PDF_CACHE_VERSION = 'job-order-docx-v2-signatures-'
_conversion_lock = Lock()
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
      'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
      'v': 'urn:schemas-microsoft-com:vml'}
NS.update(r='http://schemas.openxmlformats.org/officeDocument/2006/relationships',
          pic='http://schemas.openxmlformats.org/drawingml/2006/picture')


def embed_signatures(root, source, signatures):
    """Fill only the original four blank sign-off cells; ZIP additions are deterministic."""
    if not signatures:
        return {}
    row = root.findall('w:body/w:tbl', NS)[1].findall('w:tr', NS)[1]
    for height in row.findall('w:trPr/w:trHeight', NS):
        height.set(tag('w:hRule'), 'atLeast')
    relationships = ET.fromstring(source.read('word/_rels/document.xml.rels'))
    relation_ns = 'http://schemas.openxmlformats.org/package/2006/relationships'
    additions = {}
    drawing_id = max([int(n.get('id')) for n in root.findall('.//wp:docPr', NS)] or [0]) + 1
    for index, key in enumerate(('filled_out_by', 'assisted_by', 'verified_by', 'approved_by')):
        record = signatures.get(key)
        if not record:
            continue
        content = base64.b64decode(record['attachment']['data'], validate=True)
        with Image.open(BytesIO(content)) as image:
            # Fit both dimensions without stretching a narrow/mobile signature.
            scale = min(1120000 / image.width, 400000 / image.height)
            cx, cy = round(image.width * scale), round(image.height * scale)
        filename = f'job-order-signature-{key}.png'
        relation = 'rIdJobOrderSignature' + str(index)
        while relationships.xpath('//*[@Id=$value]', value=relation):
            relation += 'x'
        ET.SubElement(relationships, '{' + relation_ns + '}Relationship',
            Id=relation, Type=NS['r'] + '/image', Target='media/' + filename)
        paragraph = row.findall('w:tc', NS)[index].find('w:p', NS)
        for child in list(paragraph):
            if child.tag != tag('w:pPr'):
                paragraph.remove(child)
        drawing = ET.SubElement(ET.SubElement(paragraph, tag('w:r')), tag('w:drawing'))
        inline = ET.SubElement(drawing, tag('wp:inline'), distT='0', distB='0', distL='0', distR='0')
        ET.SubElement(inline, tag('wp:extent'), cx=str(cx), cy=str(cy))
        ET.SubElement(inline, tag('wp:docPr'), id=str(drawing_id + index), name='Job Order signature ' + key)
        graphic = ET.SubElement(inline, tag('a:graphic'))
        graphic_data = ET.SubElement(graphic, tag('a:graphicData'), uri=NS['pic'])
        picture = ET.SubElement(graphic_data, tag('pic:pic'))
        nonvisual = ET.SubElement(picture, tag('pic:nvPicPr'))
        ET.SubElement(nonvisual, tag('pic:cNvPr'), id='0', name=filename)
        ET.SubElement(nonvisual, tag('pic:cNvPicPr'))
        fill = ET.SubElement(picture, tag('pic:blipFill'))
        ET.SubElement(fill, tag('a:blip'), {tag('r:embed'): relation})
        ET.SubElement(ET.SubElement(fill, tag('a:stretch')), tag('a:fillRect'))
        properties = ET.SubElement(picture, tag('pic:spPr'))
        transform = ET.SubElement(properties, tag('a:xfrm'))
        ET.SubElement(transform, tag('a:off'), x='0', y='0')
        ET.SubElement(transform, tag('a:ext'), cx=str(cx), cy=str(cy))
        ET.SubElement(ET.SubElement(properties, tag('a:prstGeom'), prst='rect'), tag('a:avLst'))
        stamp = datetime.fromisoformat(record['at']).astimezone(ZoneInfo('Asia/Manila')).strftime('%b %d, %Y %I:%M %p')
        fill_paragraph(paragraph, record['name'] + '\n' + stamp, append=True)
        additions['word/media/' + filename] = content
    additions['word/_rels/document.xml.rels'] = ET.tostring(relationships, xml_declaration=True, encoding='UTF-8', standalone=True)
    return additions


def tag(name):
    prefix, local = name.split(':')
    return '{' + NS[prefix] + '}' + local


def fill_paragraph(paragraph, value, *, append=False):
    """Reuse the slot's paragraph/run styling; values are text, never XML/HTML."""
    if not value:
        return
    style = paragraph.find('w:r/w:rPr', NS)
    if not append:
        for child in list(paragraph):
            if child.tag != tag('w:pPr'):
                paragraph.remove(child)
    properties = paragraph.find('w:pPr', NS)
    if properties is not None:
        spacing = properties.find('w:spacing', NS)
        if spacing is not None:
            # Source blank cells have exact line heights; filled lines must grow.
            spacing.set(tag('w:lineRule'), 'auto')
            spacing.set(tag('w:line'), '240')
    run = ET.SubElement(paragraph, tag('w:r'))
    if style is not None:
        run.append(deepcopy(style))
    if append:
        properties = run.find('w:rPr', NS)
        if properties is None:
            properties = ET.SubElement(run, tag('w:rPr'))
        bold = properties.find('w:b', NS)
        if bold is None:
            bold = ET.SubElement(properties, tag('w:b'))
        bold.set(tag('w:val'), '0')
    for index, line in enumerate(str(value).split('\n')):
        if index or append:
            ET.SubElement(run, tag('w:br'))
        text = ET.SubElement(run, tag('w:t'))
        text.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        text.text = line


def check_drawing(root, identifier):
    """Tick the existing outlined shape in both DrawingML and its VML fallback."""
    boxes = root.xpath('//mc:AlternateContent[.//wp:docPr[@id=$id]]', namespaces=NS, id=str(identifier))
    if len(boxes) != 1:
        raise ValueError('The Job Order checkbox layout has changed.')
    box = boxes[0]
    paths = box.find('.//a:custGeom/a:pathLst', NS)
    original = paths[0]
    width, height = int(original.get('w')), int(original.get('h'))
    points = [(width // 5, height // 2), (width * 2 // 5, height * 4 // 5),
              (width * 4 // 5, height // 5)]
    path = ET.SubElement(paths, tag('a:path'), w=str(width), h=str(height), fill='none', stroke='1')
    for index, (x, y) in enumerate(points):
        command = ET.SubElement(path, tag('a:moveTo' if index == 0 else 'a:lnTo'))
        ET.SubElement(command, tag('a:pt'), x=str(x), y=str(y))
    fallback = box.find('mc:Fallback//v:shape', NS)
    old_path = fallback.get('path').removesuffix('e')
    fallback.set('path', old_path + f'm{points[0][0]},{points[0][1]}l{points[1][0]},{points[1][1]},'
                 f'{points[2][0]},{points[2][1]}nfe')


def job_order_docx(data):
    """Saved presentation values -> DOCX bytes, preserving every other ZIP part."""
    try:
        with ZipFile(BytesIO(data['_template_bytes']) if data.get('_template_bytes') else TEMPLATE) as source:
            root = ET.fromstring(source.read('word/document.xml'), ET.XMLParser(resolve_entities=False, no_network=True))
            tables = root.findall('w:body/w:tbl', NS)
            rows = tables[0].findall('w:tr', NS)
            if len(tables) != 2 or len(rows) != 12:
                raise ValueError('The Job Order field layout has changed.')

            def slot(row, cell, value, append=False):
                paragraph = rows[row].findall('w:tc', NS)[cell].find('w:p', NS)
                fill_paragraph(paragraph, value, append=append)

            client = data['client']
            slot(0, 1, data['date'])
            slot(1, 1, client['name'])
            slot(3, 1, client['address'])
            slot(4, 1, client['phone'], True)
            slot(4, 2, client['email'], True)
            for row, cell, value in ((7, 2, data['turnaround_time']), (8, 2, data['service_other'])):
                if value:
                    for text in rows[row].findall('w:tc', NS)[cell].findall('.//w:t', NS):
                        if '_' in (text.text or ''):
                            prefix = text.text[:text.text.index('_')]
                            text.text = prefix + str(value)
            slot(9, 0, data['specifics'], True)
            slot(11, 0, data['items'])
            slot(11, 1, data['received_at'])
            slot(11, 2, data['required_at'])
            # Change only the number placeholder, retaining the original title runs.
            for text in root.findall('w:body/w:p/w:r/w:t', NS):
                if 'Request No. _________________' in (text.text or ''):
                    # The source title uses narrow indents. Allow a saved office number
                    # to fit on its existing second line instead of wrapping/clipping.
                    run = text.getparent()
                    indent = run.getparent().find('w:pPr/w:ind', NS)
                    if indent is not None:
                        indent.set(tag('w:left'), '0')
                        indent.set(tag('w:right'), '0')
                    text.text = 'Request'
                    ET.SubElement(run, tag('w:br'))
                    ET.SubElement(run, tag('w:t')).text = 'No. ' + (str(data['number']) or '_________________')
            selected = {value['label'] for value in data['service_choices'] if value['checked']}
            for label, identifier in {'Equipment Rental': 25, 'Facility Rental': 27,
                    'Hotel Accommodation': 29, 'Training Center': 31, 'Laboratory Analysis': 33,
                    'BPP NCII Assessment': 37}.items():
                if label in selected:
                    check_drawing(root, identifier)
            if data['service_other']:
                check_drawing(root, 39)
            for choice in data['gender_choices']:
                if choice['checked']:
                    check_drawing(root, {'Male': 17, 'Female': 19, 'Prefer not to say': 23}[choice['label']])
            if data['legacy_gender']:
                slot(2, 2, data['legacy_gender'], True)
            # The template's literal "1 of 1" becomes real fields, in place,
            # including the legacy header fallback, when long entries continue.
            for paragraph in root.xpath('//w:p[w:r/w:t="of"]', namespaces=NS):
                numbers = paragraph.xpath('w:r/w:t[text()="1"]', namespaces=NS)
                if len(numbers) == 2:
                    for text, instruction in zip(numbers, ('PAGE', 'NUMPAGES')):
                        run = text.getparent()
                        cached_run = ET.Element(tag('w:r'))
                        style = run.find('w:rPr', NS)
                        if style is not None:
                            cached_run.append(deepcopy(style))
                        cached_run.append(deepcopy(text))
                        run.remove(text)
                        field = ET.Element(tag('w:fldSimple'))
                        field.set(tag('w:instr'), instruction)
                        field.append(cached_run)
                        run.addnext(field)
            # Keep long saved content complete rather than clipping a fixed blank row.
            for row in rows:
                for restriction in row.findall('w:trPr/w:cantSplit', NS):
                    restriction.getparent().remove(restriction)
            # A4 portrait was explicitly requested; all other source geometry remains.
            for size in root.findall('.//w:sectPr/w:pgSz', NS):
                size.set(tag('w:w'), '11906')
                size.set(tag('w:h'), '16838')
            additions = embed_signatures(root, source, data.get('signatures'))
            output = BytesIO()
            with ZipFile(output, 'w') as result:
                for part in source.infolist():
                    content = ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True) \
                        if part.filename == 'word/document.xml' else additions.pop(part.filename, None) or source.read(part.filename)
                    result.writestr(part, content)
                for name, content in additions.items():
                    info = ZipInfo(name, date_time=source.getinfo('word/document.xml').date_time)
                    info.compress_type = ZIP_DEFLATED
                    result.writestr(info, content)
            return output.getvalue()
    except (OSError, ValueError, KeyError, IndexError, ET.XMLSyntaxError) as error:
        raise BookingSlipPDFError('Unable to prepare Job Order. Check the Word template on the server.') from error


def office_binary():
    configured = getattr(settings, 'JOB_ORDER_OFFICE_BINARY', '')
    if configured:
        executable = shutil.which(configured) or (str(configured) if Path(configured).is_file() else None)
        if executable:
            return executable
        raise BookingSlipPDFError('Unable to preview Job Order. Check JOB_ORDER_OFFICE_BINARY on the server.')
    for name in ('soffice.com', 'libreoffice', 'soffice'):
        if executable := shutil.which(name):
            return executable
    for environment, suffix in (('LOCALAPPDATA', 'CampusHub/tools/program/soffice.com'),
            ('PROGRAMFILES', 'LibreOffice/program/soffice.com'),
            ('PROGRAMFILES(X86)', 'LibreOffice/program/soffice.com')):
        directory = os.environ.get(environment)
        if directory and (executable := Path(directory) / suffix).is_file():
            return str(executable)
    raise BookingSlipPDFError('Unable to preview Job Order. Configure LibreOffice on the server. Download Word remains available.')


@lru_cache(maxsize=1)
def office_profile():
    """One private temporary profile per worker, removed when its process exits."""
    return TemporaryDirectory(prefix='campushub-job-profile-')


def prepared_documents():
    """Bounded, private PDF cache shared across restarts; never a public media URL."""
    directory = getattr(settings, 'JOB_ORDER_PDF_CACHE_DIR', None) or Path(settings.BASE_DIR) / '.cache' / 'job-order-pdfs'
    return FileBasedCache(directory, {
        'TIMEOUT': 7 * 24 * 3600, 'OPTIONS': {'MAX_ENTRIES': 200},
    })


def prepared_pdf(key):
    content = cache.get(key)
    if not content:
        try:
            content = prepared_documents().get(key)
        except OSError:
            # An unwritable cache must not prevent a normal conversion/download.
            content = None
    return content if isinstance(content, bytes) and content.startswith(b'%PDF-') else None


def job_order_pdf(data):
    """Fill DOCX -> private local conversion -> PDF. No HTML rendering or uploads."""
    executable = office_binary()
    document = job_order_docx(data)
    key = PDF_CACHE_VERSION + sha256(document).hexdigest()
    cached = prepared_pdf(key)
    if cached:
        return cached
    # Serialize access to this worker's profile and coalesce identical requests.
    if not _conversion_lock.acquire(timeout=60):
        raise BookingSlipPDFError('Job Order preparation is busy. Please retry, or download the Word document.')
    try:
        cached = prepared_pdf(key)
        if cached:
            return cached
        with TemporaryDirectory(prefix='campushub-job-order-') as directory:
            root = Path(directory)
            source = root / 'job-order.docx'
            source.write_bytes(document)
            profile = Path(office_profile().name)
            subprocess.run([executable, '-env:UserInstallation=' + profile.as_uri(),
                '--headless', '--nologo', '--nodefault', '--norestore',
                '--convert-to', 'pdf:writer_pdf_Export', '--outdir', str(root), str(source)],
                check=True, timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            content = (root / 'job-order.pdf').read_bytes()
            if not content.startswith(b'%PDF-'):
                raise ValueError('No valid PDF produced')
        # The complete DOCX hash changes whenever its template or saved data changes.
        cache.set(key, content, timeout=3600)
        try:
            prepared_documents().set(key, content)
        except OSError:
            pass  # The in-memory cache and generated response remain usable.
        return content
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise BookingSlipPDFError('Unable to preview or export Job Order. Retry, or download the Word document.') from error
    finally:
        _conversion_lock.release()
