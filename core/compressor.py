# core/compressor.py
import io
import re
from PIL import Image
import htmlmin
import cssmin
import jsmin

# --- Image Compression ---


def compress_image(image_bytes, options):
    """
    Compresses an image using Pillow.
    Converts to a more efficient format and reduces quality/resolution.

    Args:
        image_bytes (bytes): The raw bytes of the image.
        options (dict): A dictionary with compression settings.
                        - 'quality' (int): 0-100 quality for JPEG/WEBP.
                        - 'max_width' (int): Maximum width to resize to.
                        - 'max_height' (int): Maximum height to resize to.
                        - 'convert_to_jpeg' (bool): Whether to convert PNGs to JPEGs.
    Returns:
        bytes: The compressed image bytes.
        str: The new file extension (e.g., '.jpeg').
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        original_format = img.format.upper()

        # Determine target format
        # Use WEBP if available for transparency, otherwise JPEG.
        if original_format == "PNG" and options.get("convert_to_jpeg", True):
            # If image has transparency, save as WEBP or keep as PNG if WEBP not desired
            if img.mode in ("RGBA", "LA") or (
                img.mode == "P" and "transparency" in img.info
            ):
                target_format = "WEBP"
            else:
                img = img.convert("RGB")
                target_format = "JPEG"
        elif original_format == "GIF":
            target_format = "WEBP"
        else:
            target_format = (
                original_format if original_format in ["JPEG", "WEBP"] else "JPEG"
            )

        # Resize image if dimensions are specified
        max_size = (options.get("max_width"), options.get("max_height"))
        if max_size[0] is not None and max_size[1] is not None:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

        output_buffer = io.BytesIO()
        save_options = {"quality": options.get("quality", 75), "optimize": True}

        if target_format == "JPEG":
            save_options["progressive"] = True

        img.save(output_buffer, format=target_format, **save_options)

        new_extension = f".{target_format.lower()}"
        return output_buffer.getvalue(), new_extension

    except Exception as e:
        print(f"Could not compress image: {e}")
        # Return original if compression fails
        return image_bytes, None


# --- Text Minification ---


def minify_content(content_bytes, file_type):
    """
    Minifies HTML, CSS, or JS content.

    Args:
        content_bytes (bytes): Raw bytes of the text file.
        file_type (str): 'html', 'css', or 'js'.

    Returns:
        bytes: Minified content bytes.
    """
    try:
        content_str = content_bytes.decode("utf-8")
        minified_str = ""

        if file_type == "html":
            minified_str = htmlmin.minify(
                content_str, remove_comments=True, remove_empty_space=True
            )
        elif file_type == "css":
            minified_str = cssmin.cssmin(content_str)
        elif file_type == "js":
            minified_str = jsmin.jsmin(content_str)
        else:
            return content_bytes

        return minified_str.encode("utf-8")
    except Exception as e:
        print(f"Could not minify {file_type}: {e}")
        return content_bytes  # Return original on failure


# --- Font Handling ---


def strip_font_rules_from_css(css_content_bytes):
    """
    Removes all @font-face rules from a CSS file.

    Args:
        css_content_bytes (bytes): The raw bytes of the CSS file.

    Returns:
        bytes: The CSS content with @font-face rules removed.
    """
    try:
        css_content = css_content_bytes.decode("utf-8")
        # A robust regex to find @font-face blocks, even with nested braces in comments.
        font_face_pattern = re.compile(
            r"@font-face\s*\{[^{}]*(((?<=\()data:[^;]+)|[^{}]|\{[^{}]*\})*\}"
        )
        cleaned_css = font_face_pattern.sub("", css_content)
        return cleaned_css.encode("utf-8")
    except Exception as e:
        print(f"Could not strip fonts from CSS: {e}")
        return css_content_bytes
