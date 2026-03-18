from pathlib import Path


def convert_to_cog(input_path: str, output_path: str) -> str:
    """Convert a raster file to Cloud Optimized GeoTIFF using rio-cogeo."""
    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    cog_profile = cog_profiles.get("deflate")
    cog_translate(
        input_path,
        str(output),
        cog_profile,
        in_memory=False,
        quiet=True,
    )
    return str(output)
