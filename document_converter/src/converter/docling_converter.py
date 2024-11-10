import io
from pathlib import Path
from itertools import batched

from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker
from docling.datamodel.base_models import FigureElement, InputFormat, Table
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem

from . import utils
from api_models import ConvertDocumentResponse


_UPLOADED_FILES_PATH = Path("/uploaded_files")


class DoclingDocumentConverter:

    def __init__(self):
        artifacts_path = StandardPdfPipeline.download_models_hf("/converter_cache")
        pipeline_options = PdfPipelineOptions(artifacts_path=artifacts_path)
        pipeline_options.images_scale = 2.0
        pipeline_options.generate_page_images = True
        pipeline_options.generate_table_images = True
        pipeline_options.generate_picture_images = True

        self.converter = DocumentConverter(format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        })

        self.max_num_pages = utils.get_max_num_pages()
        self.max_file_size = utils.get_max_file_size()

    def convert(
        self, 
        document_name: str, 
        chunk_size: int = 800
    ) -> ConvertDocumentResponse:
        
        document_path = _UPLOADED_FILES_PATH / document_name
        print(document_path)
        if not document_path.exists():
            raise FileNotFoundError(f"Document {document_name} not found")

        result = self.converter.convert(
            document_path,
            max_num_pages=self.max_num_pages,
            max_file_size=self.max_file_size
        )
        
        markdown_document = result.document.export_to_markdown()
        chunks = batched(markdown_document, chunk_size)

        result = ConvertDocumentResponse(
            text_chunks=[
                "".join(chunk) for chunk in chunks
            ]
        )
        # chunks = list(
        #     HierarchicalChunker().chunk(document)
        # )

        # self.convert_to_markup(file_name, file_bytes)

        return result
    
    def convert_to_markup(self, file_name, file_bytes):
        
        document_stream = DocumentStream(
            name=file_name, 
            stream=io.BytesIO(file_bytes)
        )
        result = self.converter.convert(
            document_stream,
            max_num_pages=self.max_num_pages,
            max_file_size=self.max_file_size
        )
        output_dir = Path("scratch")
        output_dir.mkdir(parents=True, exist_ok=True)
        doc_filename = result.input.file.stem

        # Save page images
        for page_no, page in result.document.pages.items():
            page_no = page.page_no
            page_image_filename = output_dir / f"{doc_filename}-{page_no}.png"
            with page_image_filename.open("wb") as fp:
                page.image.pil_image.save(fp, format="PNG")

        # Save images of figures and tables
        table_counter = 0
        picture_counter = 0
        for element, _level in result.document.iterate_items():
            if isinstance(element, TableItem):
                table_counter += 1
                element_image_filename = (
                    output_dir / f"{doc_filename}-table-{table_counter}.png"
                )
                with element_image_filename.open("wb") as fp:
                    element.image.pil_image.save(fp, "PNG")

            if isinstance(element, PictureItem):
                picture_counter += 1
                element_image_filename = (
                    output_dir / f"{doc_filename}-picture-{picture_counter}.png"
                )
                with element_image_filename.open("wb") as fp:
                    element.image.pil_image.save(fp, "PNG")

        # Save markdown with embedded pictures
        content_md = result.document.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
        md_filename = output_dir / f"{doc_filename}-with-images.md"
        with md_filename.open("w") as fp:
            fp.write(content_md)
