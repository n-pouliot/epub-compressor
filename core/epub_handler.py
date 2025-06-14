# core/epub_handler.py
import os
import shutil
from ebooklib import epub
from . import compressor


def get_epub_info(path):
    """Gathers initial information and file list from an EPUB without extracting."""
    if not os.path.exists(path):
        return None

    book = epub.read_epub(path)
    total_size = os.path.getsize(path)

    info = {
        "total_size": total_size,
        "images": 0,
        "html": 0,
        "css": 0,
        "fonts": 0,
        "other": 0,
        "image_size": 0,
        "html_size": 0,
        "css_size": 0,
        "font_size": 0,
        "other_size": 0,
        "file_list": [],
    }

    for item in book.get_items():
        size = len(item.get_content())
        name = item.get_name()
        info["file_list"].append(name)

        if item.get_type() == epub.ITEM_IMAGE:
            info["images"] += 1
            info["image_size"] += size
        elif item.get_type() == epub.ITEM_DOCUMENT:
            info["html"] += 1
            info["html_size"] += size
        elif item.get_type() == epub.ITEM_STYLE:
            info["css"] += 1
            info["css_size"] += size
        elif item.get_type() == epub.ITEM_FONT:
            info["fonts"] += 1
            info["font_size"] += size
        else:
            info["other"] += 1
            info["other_size"] += size

    return info


def compress_epub_file(
    input_path, output_path, options, log_callback, progress_callback
):
    """
    The main function that orchestrates the EPUB compression process.
    """
    original_size = os.path.getsize(input_path)
    log_callback(f"Starting compression for: {os.path.basename(input_path)}")
    log_callback(f"Original size: {original_size / 1024 / 1024:.2f} MB")

    book = epub.read_epub(input_path)
    items_to_process = list(book.get_items())
    total_items = len(items_to_process)
    items_to_remove = []

    # --- Processing Loop ---
    for i, item in enumerate(items_to_process):
        progress = int((i + 1) / total_items * 100)
        file_name = item.get_name()
        original_item_size = len(item.get_content())

        # 1. Compress Images
        if item.get_type() == epub.ITEM_IMAGE and options.get("compress_images"):
            progress_callback(progress, f"Compressing image: {file_name}")
            compressed_bytes, new_ext = compressor.compress_image(
                item.get_content(), options["image_options"]
            )
            if len(compressed_bytes) < original_item_size:
                item.set_content(compressed_bytes)
                if new_ext and not file_name.endswith(new_ext):
                    # To properly handle file name changes, we need to update references.
                    # This is complex. For now, we'll just log it.
                    # A full implementation would parse HTML/CSS to update paths.
                    log_callback(
                        f"  - Compressed {file_name} ({original_item_size / 1024:.1f} KB -> {len(compressed_bytes) / 1024:.1f} KB)"
                    )
            else:
                log_callback(f"  - Skipped {file_name}, no size improvement.")

        # 2. Minify HTML
        elif item.get_type() == epub.ITEM_DOCUMENT and options.get("minify_html"):
            progress_callback(progress, f"Minifying HTML: {file_name}")
            minified_content = compressor.minify_content(item.get_content(), "html")
            item.set_content(minified_content)

        # 3. Minify CSS
        elif item.get_type() == epub.ITEM_STYLE and options.get("minify_css"):
            progress_callback(progress, f"Minifying CSS: {file_name}")
            minified_content = compressor.minify_content(item.get_content(), "css")
            item.set_content(minified_content)

        # 4. Mark Fonts for Removal
        elif item.get_type() == epub.ITEM_FONT and options.get("strip_fonts"):
            log_callback(f"Marking font for removal: {file_name}")
            items_to_remove.append(item)

        progress_callback(progress, "Processing...")

    # --- Post-Processing ---

    # 5. If fonts were stripped, also remove their rules from CSS files
    if options.get("strip_fonts"):
        log_callback("Stripping @font-face rules from CSS files...")
        for item in book.get_items_of_type(epub.ITEM_STYLE):
            cleaned_css = compressor.strip_font_rules_from_css(item.get_content())
            item.set_content(cleaned_css)

    # Actually remove the marked items from the book manifest
    for item in items_to_remove:
        book.items.remove(item)

    # 6. Rebuild and Save
    log_callback("Rebuilding and saving compressed EPUB...")
    progress_callback(99, "Saving file...")
    epub.write_epub(output_path, book, {})

    # --- Final Stats ---
    final_size = os.path.getsize(output_path)
    reduction_bytes = original_size - final_size
    reduction_percent = (
        (reduction_bytes / original_size * 100) if original_size > 0 else 0
    )

    log_callback(f"Compression complete: {os.path.basename(output_path)}")
    log_callback(f"Final size: {final_size / 1024 / 1024:.2f} MB")
    log_callback(
        f"Reduced by: {reduction_bytes / 1024 / 1024:.2f} MB ({reduction_percent:.1f}%)"
    )

    return {
        "original_size": original_size,
        "final_size": final_size,
        "reduction_percent": reduction_percent,
    }
