import random
from . import log
from typing import Callable, Dict, List, Tuple

DEFAULT_TRANSFORMER_COUNT: int = 3

def get_transformer_dicts() -> Tuple[Dict[str, Callable], Dict[str, Callable]]:
    """
    Lazily imports transformers and returns a tuple of dictionaries:
    (raster_transformers_dict, linear_transformers_dict)
    
    CRITICAL: This function isolates the imports. Do not move these imports
    to the top of the file, or the circular dependency error will return.
    """
    from Transformers.RasterTransformers import (
        AnamorphicTransformer,
        ColormapTransformer,
        DataMoshTransformer,
        DuotoneTransformer,
        FisheyeTransformer,
        FlipWilsonTransformer,
        FluidWarpTransformer,
        FractalWarpTransformer,
        GlitchWarpTransformer,
        HalftoneTransformer,
        # InvertRGBTransformer, # Removed: Causing errors
        MeltMorphTransformer,
        NullTransformer,
        PosterizationTransformer,
        RadialWarpTransformer,
        SwirlWarpTransformer,
        ThreeDExtrusionTransformer,
        ThermalImagingTransformer,
        TritoneTransformer,
        WatercolorTransformer,
        WheelTransformer,
        XrayTransformer,
    )

    # FIXED: Import from the specific module file inside the LinearTransformers folder
    from Transformers.LinearTransformers.kochSnowflakeTransformer import KochSnowflakeTransformer
    from Transformers.LinearTransformers.sierpinskiTransformer import SierpinskiTransformer
    from Transformers.LinearTransformers.smoothingTransformer import SmoothingTransformer
    from Transformers.LinearTransformers.sinewaveTransformer import SineWaveTransformer
    from Transformers.LinearTransformers.jitterTransformer import JitterTransformer

    all_linear_transformers: List[Callable] = [
        KochSnowflakeTransformer,
        SierpinskiTransformer,
        SmoothingTransformer,
        SineWaveTransformer,
        JitterTransformer
    ]

    all_raster_transformers: List[Callable] = [
        AnamorphicTransformer,
        ColormapTransformer,
        DataMoshTransformer,
        DuotoneTransformer,
        FisheyeTransformer,
        FlipWilsonTransformer,
        FluidWarpTransformer,
        FractalWarpTransformer,
        GlitchWarpTransformer,
        HalftoneTransformer,
        # InvertRGBTransformer,
        MeltMorphTransformer,
        NullTransformer,
        PosterizationTransformer,
        RadialWarpTransformer,
        SwirlWarpTransformer,
        ThermalImagingTransformer,
        ThreeDExtrusionTransformer,
        TritoneTransformer,
        WatercolorTransformer,
        WheelTransformer,
        XrayTransformer,
    ]

    raster_dict = {
        str(transformer.__name__).lower(): transformer
        for transformer in all_raster_transformers
    }
    
    linear_dict = {
        str(transformer.__name__).lower(): transformer
        for transformer in all_linear_transformers
    }

    return raster_dict, linear_dict

class Pipeline:
    def __init__(self, config: dict | None):
        self.config = config if config is not None else {}
        self.transformer_count = self.config.get("transformer_count", DEFAULT_TRANSFORMER_COUNT)
        
        # 1. Fetch the dictionaries (Lazy Load)
        raster_dict_source, linear_dict_source = get_transformer_dicts()

        # 2. Prepare both lists using identical logic
        self.raster_transformers = self._configure_transformers(raster_dict_source)
        self.linear_transformers = self._configure_transformers(linear_dict_source)

    def _configure_transformers(self, source_dict: Dict[str, Callable]) -> List[Callable]:
        """
        Applies include/exclude filters, NullTransformer logic, and random sampling
        to a dictionary of transformers, returning a list of instantiated objects.
        """
        current_transformers_dict = source_dict.copy()

        # A. Check for an 'include' list and filter if present
        include_list = self.config.get("include")
        if include_list:
            include_list_lower = [str(x).lower() for x in include_list]
            current_transformers_dict = {
                name: cls for name, cls in current_transformers_dict.items()
                if name in include_list_lower
            }

        # B. Check for an 'exclude' list and filter if present
        exclude_list = self.config.get("exclude")
        if exclude_list:
            exclude_list_lower = [str(x).lower() for x in exclude_list]
            current_transformers_dict = {
                name: cls for name, cls in current_transformers_dict.items()
                if name not in exclude_list_lower
            }

        # C. Filter out 'NullTransformer' if there is more than one item remaining.
        if (len(current_transformers_dict) > 1 and 
        "nulltransformer" in current_transformers_dict):
            del current_transformers_dict["nulltransformer"]

        # D. Use the filtered dictionary for selection
        transformers_list = list(current_transformers_dict.items())
        
        # Handle the case where the dictionary might be empty after filtering
        if not transformers_list:
            log.warning("No transformers available in this category after applying filters.")
            return []

        # Get the available transformer names
        transformer_population = [name for name, _ in transformers_list]
        population_size = len(transformer_population)

        if not isinstance(self.transformer_count, int) or self.transformer_count < 0:
            log.warning(f"Invalid transformer_count '{self.transformer_count}', using default {DEFAULT_TRANSFORMER_COUNT}")
            # We don't overwrite self.transformer_count here to avoid affecting the next call
            count_to_use = DEFAULT_TRANSFORMER_COUNT
        else:
            count_to_use = self.transformer_count

        num_to_sample = min(count_to_use, population_size)
        
        if population_size > 0:
            chosen_names = random.sample(transformer_population, k=num_to_sample)
        else:
            return []

        # Instantiate and return
        return [source_dict[name]() for name in chosen_names]

    def get_transformers(self):
        return self.raster_transformers, self.linear_transformers
